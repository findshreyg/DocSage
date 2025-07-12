import httpx
import re
import json
import hashlib
import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv
import logging

from fastapi import HTTPException

logger = logging.getLogger(__name__)
load_dotenv()

MISTRAL_API_URL = os.getenv("MISTRAL_API_URL")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_LLM_MODEL=os.getenv("MISTRAL_LLM_MODEL")
AWS_REGION = os.getenv("AWS_REGION")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")

async def check_duplicate(bucket_name: str, file_path: str) -> bool:
    """
    Check if a file already exists in the given S3 bucket.

    This function performs a HEAD request to S3 to check if the object exists.

    Args:
        bucket_name (str): Name of the S3 bucket.
        file_path (str): Full path (key) of the file to check.

    Returns:
        bool: True if the file exists, False otherwise.

    Raises:
        HTTPException: If S3 throws an unexpected error.
    """
    s3_client = boto3.client('s3')
    try:
        s3_client.head_object(Bucket=bucket_name, Key=file_path)
        return True
    except ClientError as e:
        # A 404 error means the object does not exist
        if e.response['Error']['Code'] == '404':
            return False
        else:
            logger.exception("Unexpected S3 error in check_duplicate: %s", e)
            raise HTTPException(status_code=500, detail="Unexpected error while checking duplicate.")

def upload_to_s3(user_id: str, filename: str, file_content: bytes, bucket_name: str) -> str:
    """
    Upload a file to the given S3 bucket.

    Args:
        user_id (str): ID of the user uploading the file.
        filename (str): Name of the file being uploaded.
        file_content (bytes): The binary content of the file.
        bucket_name (str): Target S3 bucket name.

    Returns:
        str: The full S3 key where the file was stored.

    Raises:
        HTTPException: If upload fails for any reason.
    """
    s3_client = boto3.client('s3')
    s3_key = f"{user_id}/{filename}"
    try:
        s3_client.put_object(Bucket=bucket_name, Key=s3_key, Body=file_content)
        return s3_key
    except ClientError as e:
        logger.exception("Failed to upload file to S3: %s", e)
        raise HTTPException(status_code=500, detail="Failed to upload file to S3.")
    except Exception as e:
        logger.exception("Unexpected error during upload_to_s3: %s", e)
        raise HTTPException(status_code=500, detail="Unexpected error during file upload.")

def save_metadata(user_id: str, file_hash: str, filename: str, s3_key: str, metadata: dict):
    """
    Save extracted file metadata to the DynamoDB table in DynamoDB JSON format.

    Args:
        user_id (str): ID of the user who uploaded the file.
        file_hash (str): The SHA-256 hash of the file for deduplication.
        filename (str): The original filename.
        s3_key (str): S3 key where the file is stored.
        metadata (dict): Extracted metadata and questions.

    Raises:
        HTTPException: If DynamoDB put operation fails.
    """
    try:
        item = {
            "user_id": {"S": user_id},
            "hash": {"S": file_hash},
            "filename": {"S": filename},
            "s3_key": {"S": s3_key},
            "metadata": {
                "M": {
                    "created_date": {"S": metadata.get('metadata', {}).get('created_date', 'unknown')},
                    "pages": {"N": str(metadata.get('metadata', {}).get('pages', 0))},
                    "title": {"S": metadata.get('metadata', {}).get('title', 'unknown')},
                    "type": {"S": metadata.get('metadata', {}).get('type', 'unknown')},
                    "questions": {
                        "L": [{"S": q} for q in metadata.get('questions', [])]
                    }
                }
            }
        }

        # Use low-level DynamoDB client because the item is already DynamoDB JSON
        dynamodb_client = boto3.client('dynamodb',AWS_REGION)
        dynamodb_client.put_item(TableName='IDPMetadata', Item=item)
        logger.info("Metadata saved successfully for user %s: %s", user_id, filename)

    except ClientError as e:
        logger.exception("Failed to save metadata %s", e)
        raise HTTPException(status_code=500, detail="Failed to save metadata to database.")
    except Exception as e:
        logger.exception("Unexpected error during save_metadata: %s", e)
        raise HTTPException(status_code=500, detail="Unexpected error while saving metadata.")



client = boto3.client("cognito-idp", region_name=AWS_REGION)

def get_user_from_token(access_token: str):
    """
    Validate a Cognito access token and fetch the user profile.

    Args:
        access_token (str): A valid Cognito access token.

    Raises:
        HTTPException: If the token is missing or invalid.

    Returns:
        dict: Cognito user profile attributes.
    """
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token missing.")
    try:
        response = client.get_user(AccessToken=access_token)
        return response
    except Exception as e:
        logger.exception(f"Failed to get user from token: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired access token.")

# Async function to extract metadata using Mistral API
async def extract_metadata(file_bytes: bytes, file_name: str):
    """
    Use Mistral LLM to extract metadata and suggested questions from document content.

    Args:
        file_bytes (bytes): The file content as bytes.
        file_name (str): The name of the file.

    Raises:
        HTTPException: If LLM call fails or JSON parsing fails.

    Returns:
        dict: Parsed metadata and suggested questions.
    """
    try:
        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json"
        }

        decoded_content = file_bytes.decode('utf-8', errors='ignore')

        prompt = f"""
        You are an intelligent assistant. Analyze the uploaded document '{file_name}'.
        Here is the file content:
        {decoded_content}

        Extract the key metadata (title, type, number of pages, created date) and return
        5 likely questions a user might ask about this document. Respond in JSON:
        {{
          "metadata": {{
            "title": string,
            "type": string,
            "pages": int,
            "created_date": string
          }},
          "questions": [string, ...]
        }}
        """

        data = {
            "model": MISTRAL_LLM_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
        }

        # Make async HTTP call to Mistral LLM API
        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(MISTRAL_API_URL, headers=headers, json=data)

            if resp.status_code != 200:
                logger.error(f"LLM API error (metadata): {resp.status_code} - {resp.text}")
                raise HTTPException(status_code=resp.status_code, detail=resp.text)

            result_text = resp.json()["choices"][0]["message"]["content"]

            # Extract JSON block from the LLM output
            match = re.search(r'```json\s*(\{.*?\})\s*```', result_text, re.DOTALL)
            if match:
                logger.info(f"Metadata extracted successfully for file_name={file_name}")
                return json.loads(match.group(1).strip())
            else:
                logger.error("No valid JSON block found in LLM metadata response.")
                raise HTTPException(status_code=500, detail="No valid JSON block found in LLM metadata response.")
    except Exception as e:
        logger.exception("Error in extract_metadata")
        raise HTTPException(status_code=500, detail=str(e))