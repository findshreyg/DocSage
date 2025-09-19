import httpx
import re
import json
import hashlib
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal
import os
from dotenv import load_dotenv
import logging
import tempfile
import subprocess

from fastapi import HTTPException
from schemas import AdaptiveExtractRequest, AdaptiveExtractResponse, ClassificationResult, FieldValueWithConfidence

logger = logging.getLogger(__name__)
load_dotenv()

MISTRAL_API_URL = os.getenv("MISTRAL_API_URL")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_LLM_MODEL = os.getenv("MISTRAL_LLM_MODEL")
AWS_REGION = os.getenv("AWS_REGION")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
METADATA_TABLE_NAME = os.getenv("DDB_TABLE")

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

def convert_floats_to_decimal(obj):
    """
    Recursively convert float values to Decimal for DynamoDB compatibility.
    
    Args:
        obj: The object to convert (dict, list, or primitive)
        
    Returns:
        The object with floats converted to Decimals
    """
    if isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_floats_to_decimal(item) for item in obj)
    elif isinstance(obj, float):
        # Handle special float values
        if obj != obj:  # NaN check
            return None
        elif obj == float('inf') or obj == float('-inf'):
            return str(obj)
        else:
            return Decimal(str(obj))
    else:
        return obj

def save_metadata(user_id: str, file_hash: str, filename: str, s3_key: str, metadata: dict):
    """
    Save extracted file metadata to the DynamoDB table.

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
        # Use high-level DynamoDB resource for easier handling
        dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        table = dynamodb.Table(METADATA_TABLE_NAME or 'IDPMetadata')
        
        # Log the original metadata structure for debugging
        logger.debug(f"Original metadata type: {type(metadata)}")
        logger.debug(f"Original metadata keys: {list(metadata.keys()) if isinstance(metadata, dict) else 'Not a dict'}")
        
        # Convert floats to Decimals for DynamoDB compatibility
        dynamodb_compatible_metadata = convert_floats_to_decimal(metadata)
        
        # Log after conversion
        logger.debug("Metadata converted to DynamoDB compatible format")
        
        # Prepare the item for DynamoDB
        item = {
            "user_id": user_id,
            "hash": file_hash,
            "filename": filename,
            "s3_key": s3_key,
            "metadata": dynamodb_compatible_metadata
        }
        
        # Convert the entire item to ensure no floats remain
        item = convert_floats_to_decimal(item)
        
        table.put_item(Item=item)
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
                    "/Applications/LibreOffice.app/Contents/MacOS/soffice", "--headless", "--convert-to", "pdf",
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
                logger.error(f"Request headers: {headers}")
                logger.error(f"Request data: {data}")
                raise HTTPException(status_code=resp.status_code, detail=resp.text)

            response_json = resp.json()
            logger.info(f"API Response keys: {list(response_json.keys())}")
            result_text = response_json["choices"][0]["message"]["content"]
            parsed = extract_json_from_llm_response(result_text)

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
    

def extract_json_from_llm_response(response_text: str) -> dict:
    """Extract JSON from LLM response text."""
    try:
        # Try to parse as direct JSON first
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Look for JSON in code blocks
        match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass
        
        # Look for JSON without code blocks - more robust pattern
        match = re.search(r'(\{(?:[^{}]|{[^{}]*})*\})', response_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass
        
        # Last resort: look for any {...} block
        match = re.search(r"\{[\s\S]*\}", response_text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        
        raise HTTPException(status_code=500, detail=f"No valid JSON found in response: {response_text[:500]}...")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse JSON from LLM response: {str(e)}")

async def extract_adaptive_from_document(payload: AdaptiveExtractRequest, user: dict) -> AdaptiveExtractResponse:
    try:
        # === Step 0: Load PDF from S3, convert if needed ===
        dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
        table = dynamodb.Table(METADATA_TABLE_NAME)
        user_id = user.get("sub") or user.get("Username")
        item = table.get_item(Key={"user_id": user_id, "hash": payload.file_hash}).get("Item")
        if not item:
            raise HTTPException(status_code=404, detail="File not found")
        s3_key = item.get("s3_key")
        converted_key = s3_key + ".converted.pdf"
        s3 = boto3.client("s3", region_name=AWS_REGION)
        # Check for PDF conversion
        try:
            s3.head_object(Bucket=S3_BUCKET_NAME, Key=converted_key)
            s3_key = converted_key
        except Exception:
            pass
        s3_url = s3.generate_presigned_url("get_object", Params={"Bucket": S3_BUCKET_NAME, "Key": s3_key}, ExpiresIn=300)

        async with httpx.AsyncClient(timeout=180) as client:
            # === Single Step: Classification + Extraction ===
            prompt = """
Analyze this document step-by-step:

1. First, determine the document type by examining layout, headers, and content structure
2. Then, identify the most critical fields that should be extracted for this specific document type
3. Finally, extract those field values with high precision

Think through each step carefully before providing your final answer.

Return JSON in this exact format:
{
  "document_type": "precise label for document type (e.g., 'bank statement', 'invoice', 'medical report')",
  "description": "brief description of document purpose and key contents", 
  "confidence": 0.95,
  "extracted_fields": {
    "field_name_1": {
      "value": "extracted value",
      "confidence": 0.9,
      "reasoning": "brief explanation of why this value was chosen"
    },
    "field_name_2": {
      "value": "extracted value", 
      "confidence": 0.8,
      "reasoning": "brief explanation of why this value was chosen"
    }
  }
}

Be conservative with confidence scores - only use high confidence (>0.8) when you're very certain.
Focus on extracting the most critical fields that would be valuable for this document type.
"""
            response = await client.post(
                MISTRAL_API_URL,
                headers={"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": MISTRAL_LLM_MODEL,
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "document_url", "document_url": s3_url}
                        ]
                    }],
                    "response_format": {"type": "json_object"}
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Adaptive extraction API error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=500, detail=f"API error: {response.status_code}")
            
            response_json = response.json()
            logger.info(f"Adaptive API Response keys: {list(response_json.keys())}")
            result = extract_json_from_llm_response(response_json["choices"][0]["message"]["content"])

        # Build simplified response
        return AdaptiveExtractResponse(
            classification=ClassificationResult(
                document_type=result.get("document_type"),
                description=result.get("description"),
                confidence=result.get("confidence", 0.0)
            ),
            field_values={
                field_name: FieldValueWithConfidence(
                    value=field_data.get("value"),
                    confidence=field_data.get("confidence", 0.0)
                ) for field_name, field_data in result.get("extracted_fields", {}).items()
            },
            raw_extracted_text=response.json()["choices"][0]["message"]["content"]
        )
        
    except Exception as e:
        logger.exception("Adaptive extraction failed")
        raise HTTPException(status_code=500, detail=str(e))