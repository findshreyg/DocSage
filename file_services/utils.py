import httpx
import re
import json
import hashlib
import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv
import logging
import tempfile
import subprocess

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

async def extract_metadata(file_name: str, s3_key: str):
    """
    Use Mistral LLM to extract metadata and suggested questions from document content.

    Args:
        file_name (str): The name of the file.
        s3_key (str): The S3 key of the document.

    Raises:
        HTTPException: If LLM call fails or JSON parsing fails.

    Returns:
        dict: Parsed metadata and suggested questions.
    """
    try:
        s3_client = boto3.client("s3", region_name=AWS_REGION)
        S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

        def convert_to_pdf_if_needed(bucket, key):
            """
            Download file from S3, convert to PDF if not already PDF, upload, and return key for presigned URL.
            """
            ext = key.lower().split(".")[-1]
            # Only convert if not already PDF
            if ext == "pdf":
                return key
            converted_key = key + ".converted.pdf"
            # Check if already converted
            try:
                s3_client.head_object(Bucket=bucket, Key=converted_key)
                return converted_key
            except ClientError as e:
                if e.response['Error']['Code'] != '404':
                    raise
            # Download, convert, upload
            with tempfile.TemporaryDirectory() as tmpdir:
                local_path = os.path.join(tmpdir, os.path.basename(key))
                s3_client.download_file(bucket, key, local_path)
                # Convert to PDF using LibreOffice
                output_path = os.path.splitext(local_path)[0] + ".pdf"
                subprocess.run([
                    "libreoffice", "--headless", "--convert-to", "pdf",
                    "--outdir", tmpdir,
                    local_path
                ], check=True)
                # Find the converted PDF (LibreOffice may not use same name)
                pdf_files = [f for f in os.listdir(tmpdir) if f.endswith(".pdf")]
                if not pdf_files:
                    raise Exception("PDF conversion failed: no PDF output found.")
                converted_path = os.path.join(tmpdir, pdf_files[0])
                s3_client.upload_file(converted_path, bucket, converted_key)
                return converted_key

        # Determine if conversion is needed and get the correct key for presigned URL
        # Only convert if not PDF, .pptx, .xlsx, .ppt, .xls, etc.
        ext = s3_key.lower().split(".")[-1]
        if ext not in ["pdf"]:
            key_for_url = convert_to_pdf_if_needed(S3_BUCKET_NAME, s3_key)
        else:
            key_for_url = s3_key

        s3_url = s3_client.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': key_for_url},
            ExpiresIn=3600
        )
        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json"
        }

        prompt = f"""
        You are an intelligent assistant. Analyze the uploaded document '{file_name}'.

        Use the document to extract the key metadata (title, type, number of pages, created date) and return
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
                        {"type": "text", "text": prompt},
                        {
                            "type": "document_url",
                            "document_url": s3_url
                        }
                    ]
                }
            ],
            "document_image_limit": 8,
            "document_page_limit": 1000
        }

        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(MISTRAL_API_URL, headers=headers, json=data)

            if resp.status_code != 200:
                logger.error(f"LLM API error (metadata): {resp.status_code} - {resp.text}")
                raise HTTPException(status_code=resp.status_code, detail=resp.text)

            result_text = resp.json()["choices"][0]["message"]["content"]
            match = re.search(r'```json\s*(\{.*?\})\s*```', result_text, re.DOTALL)
            if not match:
                logger.error("No valid JSON block found in LLM metadata response.")
                raise HTTPException(status_code=500, detail="No valid JSON block found in LLM metadata response.")

            parsed = json.loads(match.group(1).strip())

            # Type checks for parsed fields
            metadata = parsed.get("metadata", {})
            questions = parsed.get("questions", [])

            if not isinstance(metadata.get("title"), str):
                raise HTTPException(status_code=500, detail="Invalid LLM response: missing or invalid 'title'")
            if not isinstance(metadata.get("type"), str):
                raise HTTPException(status_code=500, detail="Invalid LLM response: missing or invalid 'type'")
            if not isinstance(metadata.get("pages"), int):
                raise HTTPException(status_code=500, detail="Invalid LLM response: missing or invalid 'pages'")
            if not isinstance(metadata.get("created_date"), str):
                raise HTTPException(status_code=500, detail="Invalid LLM response: missing or invalid 'created_date'")
            if not isinstance(questions, list) or not all(isinstance(q, str) for q in questions):
                raise HTTPException(status_code=500, detail="Invalid LLM response: 'questions' must be a list of strings")

            return {
                "metadata": metadata,
                "questions": questions[:5]
            }
    except Exception as e:
        logger.exception("Error in extract_metadata")
        raise HTTPException(status_code=500, detail=str(e))