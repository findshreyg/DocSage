import boto3
import logging
import os
import hashlib
from dotenv import load_dotenv
from boto3.dynamodb.conditions import Key, Attr
from botocore.client import Config
from botocore.exceptions import ClientError
from utils import extract_metadata, save_metadata
from fastapi import UploadFile, HTTPException


load_dotenv()

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
DDB_TABLE = os.getenv("DDB_TABLE")
DYNAMODB_CONVERSATION_TABLE = os.getenv("DYNAMODB_CONVERSATION_TABLE")
AWS_REGION = os.getenv("AWS_REGION")
from botocore.client import Config
s3_client = boto3.client(
    's3',
    region_name=AWS_REGION,
    config=Config(signature_version='s3v4')
)
metadata_table = boto3.resource('dynamodb', region_name=AWS_REGION).Table(DDB_TABLE)  # Replace with your actual metadata table name
conversation_table = boto3.resource('dynamodb', region_name=AWS_REGION).Table(DYNAMODB_CONVERSATION_TABLE)  # Replace with your actual conversations table name

logger = logging.getLogger(__name__)

def delete_all_user_files_and_metadata(user_id: str):
    """
    Delete all user files, metadata records, and related conversations.

    Args:
        user_id (str): The ID of the user whose data will be deleted.

    Raises:
        HTTPException: If deletion fails or any step encounters an unexpected error.
    """
    try:
        # 1️⃣ List all metadata items for this user
        response = metadata_table.scan(
            FilterExpression=Key("user_id").eq(user_id)
        )
        for item in response.get("Items", []):
            s3_key = item.get("s3_key")
            file_hash = item.get("hash")

            if s3_key:
                # Delete the original file from S3
                s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
                # Delete any converted version
                converted_key = s3_key + ".converted.pdf"
                s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=converted_key)

            if file_hash:
                # Delete metadata record from DynamoDB
                metadata_table.delete_item(
                    Key={"user_id": user_id, "hash": file_hash}
                )

                # Delete all conversations related to this file hash
                convo_response = conversation_table.scan(
                    FilterExpression=Key("user_id").eq(user_id) & Attr("file_hash_timestamp").begins_with(file_hash)
                )
                for convo_item in convo_response.get("Items", []):
                    file_hash_ts = convo_item.get("file_hash_timestamp")
                    if file_hash_ts:
                        conversation_table.delete_item(
                            Key={"user_id": user_id, "file_hash_timestamp": file_hash_ts}
                        )
                    else:
                        raise Exception(f"Missing file_hash_timestamp in conversation item: {convo_item}")

        # 2️⃣ Extra safety: remove any leftover conversations for this user
        leftover_convos = conversation_table.scan(
            FilterExpression=Key("user_id").eq(user_id)
        )
        for leftover in leftover_convos.get("Items", []):
            file_hash_ts = leftover.get("file_hash_timestamp")
            if file_hash_ts:
                conversation_table.delete_item(
                    Key={"user_id": user_id, "file_hash_timestamp": file_hash_ts}
                )
            else:
                raise Exception(f"Missing file_hash_timestamp in leftover conversation: {leftover}")

    except ClientError:
        raise HTTPException(status_code=500, detail="Failed to delete user files and metadata.")
    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected error during delete operation.")


def list_user_files(user_id: str):
    """
    List all file metadata records belonging to the specified user.

    Args:
        user_id (str): The ID of the user.

    Returns:
        list: List of file metadata items or an empty list if an error occurs.
    """
    try:
        response = metadata_table.query(
            KeyConditionExpression="user_id = :uid",
            ExpressionAttributeValues={":uid": user_id}
        )
        items = response.get("Items", [])
        return items
    except ClientError:
        return []
    except Exception:
        return []


def delete_user_file(user_id: str, file_hash: str):
    """
    Delete a specific user file, its metadata, and all related conversation records.

    Args:
        user_id (str): The ID of the user.
        file_hash (str): The hash of the file to delete.

    Returns:
        tuple[bool, str]: Tuple indicating success and a message.

    Raises:
        HTTPException: If deletion fails or any step encounters an unexpected error.
    """
    try:
        item = metadata_table.get_item(Key={"user_id": user_id, "hash": file_hash})
        if "Item" not in item:
            return False, "File not found"

        s3_key = item["Item"]["s3_key"]

        # ✅ 1️⃣ Delete DynamoDB metadata first
        metadata_table.delete_item(Key={"user_id": user_id, "hash": file_hash})

        # ✅ 2️⃣ Then delete S3 objects
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
        converted_key = s3_key + ".converted.pdf"
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=converted_key)

        # ✅ 3️⃣ Delete related conversations for this file hash
        response = conversation_table.scan(
            FilterExpression=Key("user_id").eq(user_id) & Attr("file_hash_timestamp").begins_with(file_hash)
        )
        for item in response.get("Items", []):
            file_hash_ts = item.get("file_hash_timestamp")
            if file_hash_ts:
                conversation_table.delete_item(
                    Key={"user_id": user_id, "file_hash_timestamp": file_hash_ts}
                )
            else:
                raise Exception(f"Missing file_hash_timestamp in conversation item: {item}")

        return True, f"Deleted {s3_key}"

    except ClientError:
        raise HTTPException(status_code=500, detail="Failed to delete file.")
    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected error during file deletion.")


async def handle_upload(file: UploadFile, user: dict):
    """
    Handle uploading a file, deduplication, S3 storage, metadata extraction, and saving.

    Args:
        file (UploadFile): The uploaded file object.
        user (dict): Dictionary containing authenticated user details.

    Returns:
        dict: Result message, S3 key, and extracted metadata.

    Raises:
        HTTPException: If any step fails during upload or save.
    """
    try:
        logger.info(f"Starting upload for user: {user['Username']}, filename: {file.filename}")

        content = await file.read()
        file_hash = hashlib.sha256(content).hexdigest()
        logger.info(f"Computed file hash: {file_hash}")

        # Check if the same file already exists for this user
        exists = metadata_table.get_item(Key={"user_id": user["Username"], "hash": file_hash})
        if exists and "Item" in exists:
            logger.info("Duplicate file detected. Skipping upload.")
            return {
                "message": "File already uploaded.",
                "s3_key": exists["Item"]["s3_key"]
            }

        s3_key = f"{user['Username']}/{file.filename}"
        logger.info(f"Uploading file to S3 at key: {s3_key}")

        file.file.seek(0)
        try:
            s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=s3_key, Body=file.file)
            logger.info("File successfully uploaded to S3.")
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload file to storage.")

        try:
            logger.info("Starting metadata extraction.")
            extracted_metadata = await extract_metadata(content, file.filename)
            logger.info(f"Metadata extraction result: {extracted_metadata}")
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            raise HTTPException(status_code=500, detail="Metadata extraction failed.")

        try:
            logger.info("Saving metadata to DynamoDB.")
            save_metadata(user["Username"], file_hash, file.filename, s3_key, extracted_metadata)
            logger.info("Metadata saved successfully.")
        except ClientError as e:
            logger.error(f"Failed to save metadata: {e}")
            raise HTTPException(status_code=500, detail="Failed to save metadata.")

        logger.info("Upload completed successfully.")
        return {
            "message": "Upload successful",
            "s3_key": s3_key,
            "result": extracted_metadata
        }

    except Exception as e:
        logger.exception(f"Unexpected error during file upload: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during upload.")


def generate_presigned_url(user_id: str, file_hash: str, expires_in: int = 3600):
    """
    Generate a presigned S3 URL to securely download a file.

    Args:
        user_id (str): The ID of the user requesting the file.
        file_hash (str): The hash of the file.
        expires_in (int): Time in seconds until the URL expires (default: 1 hour).

    Returns:
        str: The generated presigned URL.

    Raises:
        HTTPException: If any part of the process fails.
    """
    if not S3_BUCKET_NAME:
        raise ValueError("S3_BUCKET_NAME is not set. Check your .env configuration.")

    try:
        # Look up the S3 key for this file in DynamoDB
        result = metadata_table.get_item(Key={"user_id": user_id, "hash": file_hash})
    except ClientError:
        raise HTTPException(status_code=500, detail="DynamoDB error when fetching metadata.")

    # Explicitly check if metadata exists before proceeding
    if "Item" not in result or not result["Item"]:
        raise HTTPException(status_code=404, detail="File metadata not found for this hash and user.")

    s3_key = result["Item"].get("s3_key")
    if not s3_key:
        raise HTTPException(status_code=500, detail="S3 key is missing in metadata record.")

    try:
        # Generate the presigned URL for download
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=expires_in
        )
        return url
    except ClientError:
        raise HTTPException(status_code=500, detail="Could not generate presigned URL due to AWS error.")
    except Exception:
        raise HTTPException(status_code=500, detail="Could not generate presigned URL.")