import boto3
import logging
from boto3.dynamodb.conditions import Key, Attr

logger = logging.getLogger(__name__)

S3_BUCKET_NAME = "your-s3-bucket-name"  # Replace with your actual S3 bucket name
s3_client = boto3.client('s3')
metadata_table = boto3.resource('dynamodb').Table('MetadataTable')  # Replace with your actual metadata table name
CONVERSATIONS_TABLE = boto3.resource('dynamodb').Table('ConversationsTable')  # Replace with your actual conversations table name

def delete_all_user_files_and_metadata(user_id: str):
    # 1️⃣ List all metadata items for this user
    response = metadata_table.scan(
        FilterExpression=Key("user_id").eq(user_id)
    )
    for item in response.get("Items", []):
        s3_key = item.get("s3_key")
        file_hash = item.get("hash")

        if s3_key:
            s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
            logger.info("Deleted S3 object")

            converted_key = s3_key + ".converted.pdf"
            s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=converted_key)
            logger.info("Deleted converted PDF")

        if file_hash:
            metadata_table.delete_item(
                Key={"user_id": user_id, "hash": file_hash}
            )
            logger.info("Deleted metadata for file")

            convo_response = CONVERSATIONS_TABLE.scan(
                FilterExpression=Key("user_id").eq(user_id) & Attr("file_hash_timestamp").begins_with(file_hash)
            )
            for convo_item in convo_response.get("Items", []):
                file_hash_ts = convo_item.get("file_hash_timestamp")
                if file_hash_ts:
                    CONVERSATIONS_TABLE.delete_item(
                        Key={"user_id": user_id, "file_hash_timestamp": file_hash_ts}
                    )
                    logger.info("Deleted related conversation")
                else:
                    raise Exception(f"Missing file_hash_timestamp in conversation item: {convo_item}")

    # 2️⃣ Delete any remaining conversations for this user (safety net)
    leftover_convos = CONVERSATIONS_TABLE.scan(
        FilterExpression=Key("user_id").eq(user_id)
    )
    for leftover in leftover_convos.get("Items", []):
        file_hash_ts = leftover.get("file_hash_timestamp")
        if file_hash_ts:
            CONVERSATIONS_TABLE.delete_item(
                Key={"user_id": user_id, "file_hash_timestamp": file_hash_ts}
            )
            logger.info("Deleted leftover conversation")
        else:
            raise Exception(f"Missing file_hash_timestamp in leftover conversation: {leftover}")

        logger.exception("Failed to save metadata: %s", e)
        raise

def list_user_files(user_id: str):
    """Scan or query DynamoDB for files belonging to the given user_id."""
    try:
        response = metadata_table.query(
            KeyConditionExpression="user_id = :uid",
            ExpressionAttributeValues={":uid": user_id}
        )
        items = response.get("Items", [])
        logger.info("Listed %d files for user %s", len(items), user_id)
        return items
    except ClientError as e:
        logger.exception("Failed to list files: %s", e)
        return []

def delete_user_file(user_id: str, file_hash: str):
    try:
        item = metadata_table.get_item(Key={"user_id": user_id, "hash": file_hash})
        if "Item" not in item:
            logger.warning("File not found for user_id=%s, hash=%s", user_id, file_hash)
            return False, "File not found"

        s3_key = item["Item"]["s3_key"]

        # ✅ 1️⃣ Delete DynamoDB metadata first
        metadata_table.delete_item(Key={"user_id": user_id, "hash": file_hash})
        logger.info("Deleted metadata for file")

        # ✅ 2️⃣ Then delete S3 objects
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
        logger.info("Deleted S3 object")

        converted_key = s3_key + ".converted.pdf"
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=converted_key)
        logger.info("Deleted converted PDF")

        # ✅ 3️⃣ Delete related conversations
        # (this already has atomic fail behavior)

        response = CONVERSATIONS_TABLE.scan(
            FilterExpression=Key("user_id").eq(user_id) & Attr("file_hash_timestamp").begins_with(file_hash)
        )
        for item in response.get("Items", []):
            file_hash_ts = item.get("file_hash_timestamp")
            if file_hash_ts:
                CONVERSATIONS_TABLE.delete_item(
                    Key={"user_id": user_id, "file_hash_timestamp": file_hash_ts}
                )
                logger.info("Deleted related conversation")
            else:
                raise Exception(f"Missing file_hash_timestamp in conversation item: {item}")

        return True, f"Deleted {s3_key}"

    except Exception as e:
        logger.exception("Atomic delete failed: %s", e)
        raise

# Async upload handler for processing file uploads, checking for duplicates, uploading to S3,
# extracting metadata using an LLM, and saving metadata.
async def handle_upload(file, user):
    content = await file.read()
    file_hash = calculate_file_hash(content)

    exists = check_duplicate(user["sub"], file_hash)
    if exists and "Item" in exists:
        logger.info("File already uploaded for user %s: %s", user["sub"], file.filename)
        return {
            "message": "File already uploaded.",
            "s3_key": exists["Item"]["s3_key"]
        }

    s3_key = upload_to_s3(user["sub"], file.filename, content)

    # Here you should call your LLM extract_metadata helper:
    from services.mistral_llm import extract_metadata
    result = await extract_metadata(content, file.filename)

    save_metadata(user["sub"], file_hash, file.filename, s3_key, result)
    logger.info("Upload successful for user %s: %s", user["sub"], file.filename)

    return {
        "message": "Upload successful",
        "s3_key": s3_key,
        "result": result
    }

