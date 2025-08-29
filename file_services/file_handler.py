import hashlib
import boto3
import logging
import os
from dotenv import load_dotenv
from boto3.dynamodb.conditions import Key, Attr
from botocore.client import Config
from botocore.exceptions import ClientError
from fastapi import UploadFile, HTTPException
from .utils import extract_metadata, save_metadata

load_dotenv()

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
DDB_TABLE = os.getenv("DDB_TABLE")
DYNAMODB_CONVERSATION_TABLE = os.getenv("DYNAMODB_CONVERSATION_TABLE")
AWS_REGION = os.getenv("AWS_REGION")

if not all([S3_BUCKET_NAME, DDB_TABLE, DYNAMODB_CONVERSATION_TABLE, AWS_REGION]):
    raise RuntimeError("Missing required environment variables for AWS resources.")

s3_client = boto3.client(
    's3',
    region_name=AWS_REGION,
    config=Config(signature_version='s3v4')
)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
metadata_table = dynamodb.Table(DDB_TABLE)
conversation_table = dynamodb.Table(DYNAMODB_CONVERSATION_TABLE)

logger = logging.getLogger(__name__)

def delete_all_user_files_and_metadata(user_id: str):
    """
    Delete all user files, metadata, and their associated conversation entries.
    Args:
        user_id (str): The user's unique identifier.
    Raises:
        HTTPException: If a step fails, with specific detail.
    """
    try:
        # Gather all files for this user
        response = metadata_table.scan(FilterExpression=Key("user_id").eq(user_id))
        for item in response.get("Items", []):
            s3_key = item.get("s3_key")
            file_hash = item.get("hash")
            if s3_key:
                # Delete original file
                try:
                    s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
                except Exception as e:
                    logger.warning(f"Error deleting file in S3: {s3_key} - {e}")
                # Delete converted PDF if present
                try:
                    converted_key = s3_key + ".converted.pdf"
                    s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=converted_key)
                except Exception as e:
                    logger.debug(f"No converted PDF or error deleting converted: {e}")
            if file_hash:
                try:
                    metadata_table.delete_item(Key={"user_id": user_id, "hash": file_hash})
                except Exception as e:
                    logger.warning(f"Error deleting metadata: {file_hash} - {e}")
                convo_response = conversation_table.scan(FilterExpression=Key("user_id").eq(user_id) & Attr("file_hash_timestamp").begins_with(file_hash))
                for convo_item in convo_response.get("Items", []):
                    file_hash_ts = convo_item.get("file_hash_timestamp")
                    if file_hash_ts:
                        try:
                            conversation_table.delete_item(Key={"user_id": user_id, "file_hash_timestamp": file_hash_ts})
                        except Exception as e:
                            logger.warning(f"Error deleting convo: {file_hash_ts} - {e}")

        # Now extra safety: remove any leftover conversations for this user
        leftover_convos = conversation_table.scan(FilterExpression=Key("user_id").eq(user_id))
        for leftover in leftover_convos.get("Items", []):
            file_hash_ts = leftover.get("file_hash_timestamp")
            if file_hash_ts:
                try:
                    conversation_table.delete_item(Key={"user_id": user_id, "file_hash_timestamp": file_hash_ts})
                except Exception as e:
                    logger.warning(f"Error deleting leftover conversation: {file_hash_ts} - {e}")
    except ClientError as e:
        logger.exception(f"Failed deleting user files/metadata: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user files and metadata.")
    except Exception as e:
        logger.exception(f"Unexpected error during delete_all_user_files_and_metadata: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error during delete operation.")

def list_user_files(user_id: str):
    """
    List all file metadata items for a user.
    Args:
        user_id (str): User ID
    Returns:
        list: File metadata items
    """
    try:
        response = metadata_table.query(
            KeyConditionExpression=Key("user_id").eq(user_id)
        )
        return response.get("Items", [])
    except ClientError as e:
        logger.error(f"DynamoDB error listing files: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error listing user files: {e}")
        return []

def delete_user_file(user_id: str, file_hash: str):
    """
    Delete a specific user's file and all associated metadata/conversations.
    Args:
        user_id (str)
        file_hash (str)
    Returns:
        tuple (bool, str): True and message if deleted, False and error otherwise.
    """
    try:
        item = metadata_table.get_item(Key={"user_id": user_id, "hash": file_hash})
        if "Item" not in item:
            return False, "File not found."
        s3_key = item["Item"]["s3_key"]
        # Delete metadata
        try:
            metadata_table.delete_item(Key={"user_id": user_id, "hash": file_hash})
        except Exception as e:
            logger.error(f"Error deleting DynamoDB metadata: {e}")
        # Delete from S3 (both original and converted)
        base_key = s3_key.replace(".converted.pdf", "")
        try:
            s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=base_key)
            s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=base_key + ".converted.pdf")
        except Exception as e:
            logger.warning(f"Error deleting S3 objects: {e}")
        # Delete conversations
        convo_response = conversation_table.scan(FilterExpression=Key("user_id").eq(user_id) & Attr("file_hash_timestamp").begins_with(file_hash))
        for i in convo_response.get("Items", []):
            file_hash_ts = i.get("file_hash_timestamp")
            if file_hash_ts:
                try:
                    conversation_table.delete_item(Key={"user_id": user_id, "file_hash_timestamp": file_hash_ts})
                except Exception as e:
                    logger.warning(f"Error deleting conversation: {file_hash_ts} - {e}")
        return True, f"Deleted {s3_key}"
    except ClientError as e:
        logger.exception(f"Failed to delete user file {file_hash}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete file.")
    except Exception as e:
        logger.exception(f"Unexpected error deleting file: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error during file deletion.")

async def handle_upload(file: UploadFile, user: dict) -> dict:
    """
    Handle the file upload, deduplication, metadata extraction, and DynamoDB/S3 save.
    Args:
        file (UploadFile): The uploaded file object.
        user (dict): The authenticated user profile.
    Returns:
        dict: Upload result.
    """
    try:
        logger.info(f"User: {user.get('Username')} uploading file: {file.filename}")
        content = await file.read()
        file_hash = hashlib.sha256(content).hexdigest()
        # Check deduplication
        exists = metadata_table.get_item(Key={"user_id": user["Username"], "hash": file_hash})
        if exists and "Item" in exists:
            logger.info("Duplicate file detected. Skipping upload.")
            return {"message": "File already uploaded.", "s3_key": exists["Item"]["s3_key"]}
        s3_key = f"{user['Username']}/{file.filename}"
        file.file.seek(0)
        try:
            s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=s3_key, Body=file.file)
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload file to storage.")
        # Extract metadata with LLM, then save it
        try:
            extracted_metadata = await extract_metadata(file.filename, s3_key)
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            raise HTTPException(status_code=500, detail="Metadata extraction failed.")
        try:
            save_metadata(user["Username"], file_hash, file.filename, s3_key, extracted_metadata)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
            raise HTTPException(status_code=500, detail="Failed to save metadata.")
        logger.info(f"Upload complete for {file.filename}")
        return {
            "message": "Upload successful",
            "s3_key": s3_key,
            "file_hash": file_hash,
            "result": extracted_metadata
        }
    except Exception as e:
        logger.exception(f"Unexpected error during upload: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during upload.")

def generate_presigned_url(user_id: str, file_hash: str, expires_in: int = 3600) -> str:
    """
    Generate a (temporary) presigned download URL for a user's file.
    Args:
        user_id (str)
        file_hash (str)
        expires_in (int): URL expiry in seconds (default 1hr)
    Returns:
        str: Presigned download URL
    """
    if not S3_BUCKET_NAME:
        raise RuntimeError("S3_BUCKET_NAME not set in environment.")
    try:
        result = metadata_table.get_item(Key={"user_id": user_id, "hash": file_hash})
        if "Item" not in result or not result["Item"]:
            raise HTTPException(status_code=404, detail="File metadata not found.")
        s3_key = result["Item"].get("s3_key")
        if not s3_key:
            raise HTTPException(status_code=500, detail="S3 key missing in metadata.")
        try:
            url = s3_client.generate_presigned_url('get_object', Params={'Bucket': S3_BUCKET_NAME, 'Key': s3_key}, ExpiresIn=expires_in)
            return url
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise HTTPException(status_code=500, detail="Could not generate presigned URL due to AWS error.")
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        raise HTTPException(status_code=500, detail="Error accessing DynamoDB for presigned URL.")
    except Exception as e:
        logger.error(f"Unexpected error during presigned URL generation: {e}")
        raise HTTPException(status_code=500, detail="Could not generate presigned URL.")

