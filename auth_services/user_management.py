# Import necessary libraries for AWS Cognito, S3, and DynamoDB
import boto3
import os
import logging
from fastapi import HTTPException
from botocore.exceptions import ClientError, BotoCoreError
from dotenv import load_dotenv
from utils import get_secret_hash

from boto3.dynamodb.conditions import Key, Attr

# Load environment variables from a .env file
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Retrieve AWS and Cognito configuration from environment variables
AWS_REGION = os.getenv("AWS_REGION")  # Default to us-east-1 if not set
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
DDB_TABLE = os.getenv("DDB_TABLE")
DYNAMODB_CONVERSATION_TABLE = os.getenv("DYNAMODB_CONVERSATION_TABLE")

# Check if all required environment variables are set
if not all([AWS_REGION, COGNITO_USER_POOL_ID, COGNITO_CLIENT_ID, S3_BUCKET_NAME, DDB_TABLE, DYNAMODB_CONVERSATION_TABLE]):
    logger.error("One or more required environment variables are missing.")
    raise HTTPException(status_code=500, detail="Server configuration error.")

# Initialize AWS clients for Cognito, S3, and DynamoDB
client = boto3.client("cognito-idp", region_name=AWS_REGION)
s3_client = boto3.client("s3", region_name=AWS_REGION)
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
metadata_table = dynamodb.Table(DDB_TABLE)
conversations_table = dynamodb.Table(DYNAMODB_CONVERSATION_TABLE)

# Function to confirm user sign-up with a confirmation code
def confirm_sign_up(email: str, code: str):
    # Validate email and code input
    if not email or not code:
        raise HTTPException(status_code=400, detail="Email and confirmation code are required.")
    try:
        # Check if user exists
        client.admin_get_user(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=email
        )

        # Confirm user sign-up
        client.confirm_sign_up(
            ClientId=COGNITO_CLIENT_ID,
            SecretHash=get_secret_hash(email),
            Username=email,
            ConfirmationCode=code
        )
        return {"message": "User confirmed successfully."}

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        logger.exception(f"ConfirmSignUp failed for {email}: {error_code} - {e}")

        # Handle specific error codes
        if error_code == "UserNotFoundException":
            raise HTTPException(status_code=404, detail="User not found.")
        elif error_code == "CodeMismatchException":
            raise HTTPException(status_code=400, detail="Invalid confirmation code.")
        elif error_code == "ExpiredCodeException":
            raise HTTPException(status_code=400, detail="Confirmation code expired.")
        else:
            raise HTTPException(status_code=400, detail="Failed to confirm user. Please check the code and try again.")

    except BotoCoreError as e:
        logger.exception(f"BotoCoreError in confirm_sign_up: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")

# Function to retrieve user details using an access token
def get_user(access_token: str):
    # Validate access token input
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required.")

    try:
        # Retrieve user information
        response = client.get_user(AccessToken=access_token)
        logger.debug(f"Get user response: {response}")

        # Extract user attributes
        email_attr = next(
            (attr['Value'] for attr in response['UserAttributes'] if attr['Name'] == 'email'),
            None
        )
        name_attr = next(
            (attr['Value'] for attr in response['UserAttributes'] if attr['Name'] == 'name'),
            None
        )
        username_attr = response.get('Username')
        logger.debug(f"Extracted username: {username_attr}")

        logger.info(f"Retrieved user profile: email={email_attr}, name={name_attr}")

        return {
            "username": username_attr,
            "email": email_attr,
            "name": name_attr
        }

    except ClientError as e:
        code = e.response["Error"]["Code"]
        logger.exception(f"Get user failed: {code} - {e}")

        # Handle specific error codes
        if code == "NotAuthorizedException":
            raise HTTPException(status_code=401, detail="Invalid or expired access token.")
        elif code == "ResourceNotFoundException":
            raise HTTPException(status_code=404, detail="User not found.")
        else:
            raise HTTPException(status_code=400, detail="Failed to retrieve user details.")

    except BotoCoreError as e:
        logger.exception(f"BotoCoreError in get_user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")

# Function to delete a user and all associated data
def delete_user(access_token: str):
    user_info = None
    try:
        # Retrieve user information
        user_info = get_user(access_token)
        user_id = user_info.get('username')

        if not user_id:
            raise HTTPException(status_code=400, detail="Failed to extract user ID from access token.")

        logger.info(f"Deleting all data for user_id: {user_id}")

        # 1️⃣ Delete user files + metadata
        response = metadata_table.scan(
            FilterExpression=Key("user_id").eq(user_id)
        )

        for item in response.get("Items", []):
            s3_key = item.get("s3_key")
            file_hash = item.get("hash")

            if s3_key:
                # Delete S3 objects
                s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
                logger.info(f"Deleted S3 object: {s3_key}")

                converted_key = s3_key + ".converted.pdf"
                s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=converted_key)
                logger.info(f"Deleted converted PDF: {converted_key}")

            if file_hash:
                # Delete metadata from DynamoDB
                metadata_table.delete_item(
                    Key={"user_id": user_id, "hash": file_hash}
                )
                logger.info(f"Deleted metadata for file hash: {file_hash}")

                # Delete related conversations
                convo_response = conversations_table.scan(
                    FilterExpression=Key("user_id").eq(user_id) & Attr("file_hash_timestamp").begins_with(file_hash)
                )
                for convo_item in convo_response.get("Items", []):
                    file_hash_ts = convo_item.get("file_hash_timestamp")
                    if file_hash_ts:
                        conversations_table.delete_item(
                            Key={"user_id": user_id, "file_hash_timestamp": file_hash_ts}
                        )
                        logger.info(f"Deleted related conversation: {file_hash_ts}")
                    else:
                        logger.warning(f"Missing file_hash_timestamp in conversation item: {convo_item}")

        # 2️⃣ Extra safety: Delete leftover conversations
        leftover_convos = conversations_table.scan(
            FilterExpression=Key("user_id").eq(user_id)
        )
        for leftover in leftover_convos.get("Items", []):
            file_hash_ts = leftover.get("file_hash_timestamp")
            if file_hash_ts:
                conversations_table.delete_item(
                    Key={"user_id": user_id, "file_hash_timestamp": file_hash_ts}
                )
                logger.info(f"Deleted leftover conversation: {file_hash_ts}")
            else:
                logger.warning(f"Missing file_hash_timestamp in leftover conversation: {leftover}")

        logger.info(f"✅ Completed cleanup for user_id: {user_id}")

        # 3️⃣ Delete the Cognito user
        client.admin_delete_user(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=user_id
        )
        logger.info(f"Deleted Cognito user: {user_id}")

        return {"message": f"User {user_id} and all related data deleted successfully."}

    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.exception(f"Delete user failed: {error_code} - {e}")

        # Handle specific error codes
        if error_code == "UserNotFoundException":
            raise HTTPException(status_code=404, detail="User not found.")
        elif error_code == "NotAuthorizedException":
            raise HTTPException(status_code=401, detail="Invalid or expired access token.")
        else:
            raise HTTPException(status_code=400, detail="Failed to delete user account.")

    except BotoCoreError as e:
        logger.exception(f"BotoCoreError in delete_user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during deletion.")

    except HTTPException:
        raise 

    except Exception as e:
        logger.exception(f"Unexpected error during user cleanup: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete all user data. User account may not be fully removed.")
