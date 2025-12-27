# Utility functions for LLM service operations
# This module provides helper functions for authentication, data retrieval, and JSON processing

import os  # Access environment variables
import boto3  # AWS SDK for Python
from dotenv import load_dotenv  # Load environment variables from .env file
from fastapi import HTTPException  # HTTP error responses
import json  # JSON parsing and manipulation
import re  # Regular expressions for text processing
import logging  # Application logging

# Load environment variables from .env file
load_dotenv()

# Configure logging for debugging and monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables for AWS services
# These are required for connecting to different AWS services
AWS_REGION = os.getenv("AWS_REGION")  # AWS region where services are deployed
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")  # Cognito user pool for authentication
METADATA_TABLE_NAME = os.getenv("DDB_TABLE")  # DynamoDB table storing file metadata

# Validate required environment variables
# Without these, the service cannot function properly
if not AWS_REGION or not COGNITO_USER_POOL_ID:
    raise RuntimeError("Missing AWS_REGION or COGNITO_USER_POOL_ID in environment.")

if not METADATA_TABLE_NAME:
    raise RuntimeError("Missing DDB_TABLE environment variable.")

# Initialize AWS clients for different services
# These handle communication with AWS services
client = boto3.client("cognito-idp", region_name=AWS_REGION)  # Cognito Identity Provider
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)  # DynamoDB resource
metadata_table = dynamodb.Table(METADATA_TABLE_NAME)  # File metadata table

def get_user_from_token(access_token: str) -> dict:
    """
    Retrieve user details from AWS Cognito using an access token.
    
    This function:
    1. Validates the access token is present
    2. Calls Cognito to verify token and get user information
    3. Returns user attributes for authorization checks
    4. Includes test mode for development/debugging
    
    Args:
        access_token (str): JWT access token from Cognito authentication
        
    Returns:
        dict: User properties and attributes from Cognito
        
    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    # Input validation - access token is required
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token missing.")
    
    # Test mode for debugging - bypass auth with specific test token
    # This allows testing without valid Cognito tokens during development
    logger.error(f"🔍 TOKEN CHECK: Received token: '{access_token}'")
    if access_token == "test-debug-token":
        logger.error("🧪 USING TEST MODE - BYPASSING AUTHENTICATION")
        return {
            "Username": "test-user",
            "UserAttributes": [
                {"Name": "email", "Value": "test@example.com"},
                {"Name": "name", "Value": "Test User"}
            ]
        }
    
    try:
        # Validate token with Cognito and retrieve user information
        response = client.get_user(AccessToken=access_token)
        return response
    except Exception:
        # Token is invalid, expired, or Cognito is unreachable
        raise HTTPException(status_code=401, detail="Invalid or expired access token.")

def extract_json_from_llm_response(response_text: str) -> dict:
    """Extract JSON object from LLM response text safely."""

    logger.error(f"=== LLM JSON PARSING DEBUG ===")
    logger.error(f"Raw response length: {len(response_text)}")
    logger.error(f"Raw response first 1000 chars: {response_text[:1000]}")
    logger.error(f"Raw response last 500 chars: {response_text[-500:]}")

    # 1. Try direct parse (if it's already valid JSON)
    try:
        return json.loads(clean_json_string(response_text))
    except json.JSONDecodeError:
        pass

    # 2. Extract the first JSON object with regex
    match = re.search(r'\{[\s\S]*\}', response_text)
    if match:
        raw_json = clean_json_string(match.group(0))
        try:
            return json.loads(raw_json)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Regex JSON parsing failed: {e}")
            logger.error(f"Failed JSON snippet (first 500 chars): {raw_json[:500]}")

    logger.error("❌ All JSON parsing attempts failed")
    logger.error("Full response text for manual inspection:")
    logger.error(response_text)

    raise HTTPException(
        status_code=500,
        detail="No valid JSON found in LLM response."
    )


def clean_json_string(json_str: str) -> str:
    """Clean JSON string by removing markdown fences and invalid control characters."""

    # Remove common Markdown fences (```json ... ```)
    json_str = re.sub(r"^```(?:json)?", "", json_str.strip(), flags=re.IGNORECASE)
    json_str = re.sub(r"```$", "", json_str.strip())

    # Remove problematic ASCII control characters (except valid escapes like \n, \t, etc.)
    json_str = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', json_str)

    return json_str.strip()

async def get_stored_field_values(file_hash: str, user: dict) -> dict:
    """
    Retrieve complete adaptive extraction data from DynamoDB IDPMetadata table.
    
    This function:
    1. Gets user ID from the user object
    2. Queries DynamoDB IDPMetadata table using user_id and file_hash
    3. Extracts the complete adaptive_extraction data from metadata
    4. Returns the entire adaptive extraction information
    
    Args:
        file_hash (str): The hash identifier of the file
        user (dict): User information from Cognito token
        
    Returns:
        dict: Complete adaptive extraction data including classification, field_values, etc.
        
    Raises:
        HTTPException: If file not found, no extraction data, or database errors
    """
    try:
        # Extract user ID from user object (handle different formats)
        user_id = user.get("sub") or user.get("Username")
        if not user_id:
            raise HTTPException(status_code=400, detail="User identifier not found in token")
        
        logger.info(f"Retrieving adaptive extraction data for user {user_id}, file {file_hash}")
        
        # Query DynamoDB IDPMetadata table for the file
        response = metadata_table.get_item(
            Key={
                "user_id": user_id,
                "hash": file_hash
            }
        )
        
        # Check if file exists in metadata table
        if "Item" not in response:
            raise HTTPException(status_code=404, detail="File not found or user does not have access")
        
        item = response["Item"]
        
        # Navigate to adaptive extraction data in the nested metadata structure
        metadata = item.get("metadata", {})
        adaptive_extraction = metadata.get("adaptive_extraction", {})
        
        # Check if adaptive extraction data exists
        if not adaptive_extraction:
            raise HTTPException(status_code=404, detail="No adaptive extraction data found for this file")
        
        logger.info(f"Successfully retrieved adaptive extraction data for file {file_hash}")
        
        # Return the complete adaptive_extraction data with file_hash for reference
        return {
            "file_hash": file_hash,
            "adaptive_extraction": adaptive_extraction
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.exception(f"Error retrieving adaptive extraction data for file {file_hash}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve stored adaptive extraction data")