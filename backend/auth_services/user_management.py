# User management module - handles user lifecycle operations and data cleanup
# This module manages user confirmation, profile retrieval, and complete account deletion

import boto3  # AWS SDK for Python
import os  # Access environment variables
import logging  # Application logging
from fastapi import HTTPException, status  # HTTP error responses and status codes
from botocore.exceptions import ClientError, BotoCoreError  # AWS-specific exceptions
from dotenv import load_dotenv  # Load environment variables from .env file
from utils import get_secret_hash  # Generate HMAC hash for Cognito client secret
from boto3.dynamodb.conditions import Key, Attr  # DynamoDB query conditions
from typing import Optional, Dict, Any  # Type hints for better code documentation

# Load environment variables from .env file
load_dotenv()

# Retrieve AWS service configuration from environment variables
# User management requires access to multiple AWS services
AWS_REGION = os.getenv("AWS_REGION")  # AWS region for all services
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")  # Cognito user pool identifier
COGNITO_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")  # App client for Cognito operations
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")  # S3 bucket for user file storage
DDB_TABLE = os.getenv("DDB_TABLE")  # DynamoDB table for file metadata
DYNAMODB_CONVERSATION_TABLE = os.getenv("DYNAMODB_CONVERSATION_TABLE")  # Table for conversation history

# Validate that all required configuration is present
# User management operations require access to all these AWS services
_required_envs = [
    AWS_REGION, COGNITO_USER_POOL_ID, COGNITO_CLIENT_ID,
    S3_BUCKET_NAME, DDB_TABLE, DYNAMODB_CONVERSATION_TABLE
]
if not all(_required_envs):
    raise HTTPException(status_code=500, detail="Server configuration error: Missing environment variable(s)")

# Initialize AWS service clients and resources
# These handle communication with different AWS services
try:
    client = boto3.client("cognito-idp", region_name=AWS_REGION)  # Cognito Identity Provider
    s3_client = boto3.client("s3", region_name=AWS_REGION)  # S3 for file storage
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)  # DynamoDB resource
    metadata_table = dynamodb.Table(DDB_TABLE)  # File metadata table
    conversations_table = dynamodb.Table(DYNAMODB_CONVERSATION_TABLE)  # Conversation history table
except Exception as e:
    # If we can't connect to AWS services, user management won't work
    logging.exception("Failed to initialize AWS SDK clients/resources.")
    raise HTTPException(status_code=500, detail="Failed to initialize AWS resources.")

def confirm_sign_up(email: str, code: str) -> Dict[str, str]:
    """
    Confirm user registration using the 6-digit code sent via email.
    
    This function:
    1. Verifies the user exists in Cognito
    2. Validates the confirmation code
    3. Activates the user account (changes status to CONFIRMED)
    4. Enables the user to log in
    
    This is a required step after user registration before login is allowed.
    """
    # Input validation - both email and confirmation code are required
    if not email or not code:
        raise HTTPException(status_code=400, detail="Email and confirmation code are required.")

    try:
        # First verify that the user exists in Cognito
        client.admin_get_user(UserPoolId=COGNITO_USER_POOL_ID, Username=email)
        
        # Confirm the user's signup with the provided code
        client.confirm_sign_up(
            ClientId=COGNITO_CLIENT_ID,  # App client identifier
            SecretHash=get_secret_hash(email),  # Security hash for verification
            Username=email,  # User's email address
            ConfirmationCode=code  # 6-digit code from email
        )
        
        return {"message": "User confirmed successfully."}
    
    except ClientError as e:
        # Handle specific Cognito confirmation errors
        error_code = e.response["Error"]["Code"]
        if error_code == "UserNotFoundException":
            # User account doesn't exist
            raise HTTPException(status_code=404, detail="User not found.")
        elif error_code == "CodeMismatchException":
            # Wrong confirmation code entered
            raise HTTPException(status_code=400, detail="Invalid confirmation code.")
        elif error_code == "ExpiredCodeException":
            # Confirmation code has expired (usually after 24 hours)
            raise HTTPException(status_code=400, detail="Confirmation code expired.")
        else:
            # Other Cognito-specific errors
            logging.error(f"ClientError in confirm_sign_up: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to confirm user: {error_code}")
    
    except BotoCoreError as e:
        # AWS SDK or connection errors
        logging.exception("BotoCoreError in confirm_sign_up")
        raise HTTPException(status_code=500, detail="Internal server error.")
    
    except Exception as e:
        # Any other unexpected errors
        logging.exception("Unknown error in confirm_sign_up")
        raise HTTPException(status_code=500, detail="Unexpected error confirming user.")

def get_user(access_token: str) -> Dict[str, Optional[str]]:
    """
    Retrieve current user's profile information using their access token.
    
    This function:
    1. Validates the access token with Cognito
    2. Extracts user attributes (ID, email, name)
    3. Returns user profile data
    
    Used by frontend applications to display user information and verify authentication.
    """
    # Input validation - access token is required to identify the user
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required.")

    try:
        # Get user information from Cognito using the access token
        response = client.get_user(AccessToken=access_token)
        
        # Extract email attribute from user attributes array
        email_attr = next(
            (attr['Value'] for attr in response['UserAttributes'] if attr['Name'] == 'email'), 
            None
        )
        
        # Extract name attribute from user attributes array
        name_attr = next(
            (attr['Value'] for attr in response['UserAttributes'] if attr['Name'] == 'name'), 
            None
        )
        
        # Get the username (which is the user's unique identifier)
        username_attr = response.get('Username')
        
        # Return structured user profile information
        return {
            "id": username_attr,  # Unique user identifier
            "email": email_attr,  # User's email address
            "name": name_attr  # User's display name
        }
    
    except ClientError as e:
        # Handle specific Cognito user retrieval errors
        code = e.response["Error"]["Code"]
        if code == "NotAuthorizedException":
            # Access token is invalid or expired
            raise HTTPException(status_code=401, detail="Invalid or expired access token.")
        elif code == "ResourceNotFoundException":
            # User account no longer exists
            raise HTTPException(status_code=404, detail="User not found.")
        else:
            # Other Cognito-specific errors
            logging.error(f"ClientError in get_user: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to retrieve user details: {code}")
    
    except BotoCoreError as e:
        # AWS SDK or connection errors
        logging.exception("BotoCoreError in get_user")
        raise HTTPException(status_code=500, detail="Internal server error.")
    
    except Exception as e:
        # Any other unexpected errors
        logging.exception("Unknown error in get_user")
        raise HTTPException(status_code=500, detail="Unexpected error retrieving user details.")

def delete_user(access_token: str) -> Dict[str, str]:
    """
    Permanently delete user account and all associated data across all AWS services.
    
    This function performs a complete data cleanup:
    1. Validates user authentication
    2. Deletes all user files from S3 storage
    3. Deletes all file metadata from DynamoDB
    4. Deletes all conversation history from DynamoDB
    5. Deletes user account from Cognito
    
    This operation is irreversible - all user data is permanently removed.
    """
    # Input validation - access token is required to identify and authenticate the user
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required for deletion.")

    try:
        # Step 1: Get user information and validate authentication
        user_info = get_user(access_token)  # This validates the token and gets user details
        user_id = user_info.get('id')
        if not user_id:
            raise HTTPException(status_code=400, detail="Failed to extract user ID from access token.")

        # Step 2: Find and delete all user files and metadata
        # Scan DynamoDB metadata table for all files belonging to this user
        response = metadata_table.scan(FilterExpression=Key("user_id").eq(user_id))
        file_hashes = []  # Keep track of file hashes for conversation cleanup
        
        # Process each file the user has uploaded
        for item in response.get("Items", []):
            s3_key = item.get("s3_key")  # S3 location of the file
            file_hash = item.get("hash")  # Unique identifier for the file
            
            # Delete files from S3 storage
            if s3_key:
                # Delete original uploaded file
                try:
                    s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
                except Exception as ex:
                    # Log warning but continue - file might already be deleted
                    logging.warning(f"Failed to delete S3 object {s3_key}: {ex}")
                
                # Delete converted PDF version if it exists
                converted_key = f"{s3_key}.converted.pdf"
                try:
                    s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=converted_key)
                except Exception as ex:
                    # This is expected if no converted version exists
                    logging.debug(f"No converted S3 object for {converted_key}: {ex}")
            
            # Delete file metadata from DynamoDB and track file hash
            if file_hash:
                file_hashes.append(file_hash)  # Save for conversation cleanup
                try:
                    metadata_table.delete_item(Key={"user_id": user_id, "hash": file_hash})
                except Exception as ex:
                    # Log warning but continue with other files
                    logging.warning(f"Failed to delete metadata item {file_hash} for user {user_id}: {ex}")

        # Step 3: Delete all conversations associated with user's files
        # For each file the user uploaded, delete all related conversations
        for file_hash in file_hashes:
            # Find all conversations for this specific file
            convo_response = conversations_table.scan(
                FilterExpression=Key("user_id").eq(user_id) & Attr("file_hash_timestamp").begins_with(file_hash)
            )
            
            # Delete each conversation record
            for convo_item in convo_response.get("Items", []):
                file_hash_ts = convo_item.get("file_hash_timestamp")  # Composite key for conversation
                if file_hash_ts:
                    try:
                        conversations_table.delete_item(
                            Key={"user_id": user_id, "file_hash_timestamp": file_hash_ts}
                        )
                    except Exception as ex:
                        # Log warning but continue with other conversations
                        logging.warning(f"Failed to delete conversation item {file_hash_ts}: {ex}")

        # Step 4: Clean up any leftover conversations (safety measure)
        # This catches any conversations that might not be linked to files
        leftover_convos = conversations_table.scan(FilterExpression=Key("user_id").eq(user_id))
        for leftover in leftover_convos.get("Items", []):
            file_hash_ts = leftover.get("file_hash_timestamp")
            if file_hash_ts:
                try:
                    conversations_table.delete_item(
                        Key={"user_id": user_id, "file_hash_timestamp": file_hash_ts}
                    )
                except Exception as ex:
                    # Log warning but continue - this is cleanup
                    logging.warning(f"Failed to delete leftover conversation {file_hash_ts}: {ex}")

        # Step 5: Finally, delete the user account from Cognito
        # This removes the user's authentication credentials and profile
        client.admin_delete_user(UserPoolId=COGNITO_USER_POOL_ID, Username=user_id)

        return {"message": f"User {user_id} and all related data deleted successfully."}

    except ClientError as e:
        # Handle specific AWS service errors
        error_code = e.response['Error']['Code']
        if error_code == "UserNotFoundException":
            # User account doesn't exist in Cognito
            raise HTTPException(status_code=404, detail="User not found.")
        elif error_code == "NotAuthorizedException":
            # Access token is invalid or expired
            raise HTTPException(status_code=401, detail="Invalid or expired access token.")
        else:
            # Other AWS service errors
            logging.error(f"ClientError in delete_user: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to delete user account: {error_code}")
    
    except BotoCoreError as e:
        # AWS SDK or connection errors
        logging.exception("BotoCoreError in delete_user")
        raise HTTPException(status_code=500, detail="Internal server error during deletion.")
    
    except HTTPException:
        # Re-raise HTTP exceptions (these have proper error messages)
        raise
    
    except Exception as e:
        # Any other unexpected errors during the deletion process
        logging.exception("Unknown error in delete_user")
        raise HTTPException(status_code=500, detail="Failed to delete all user data. User account may not be fully removed.")
