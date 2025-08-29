import boto3
import os
import logging
from fastapi import HTTPException, status
from botocore.exceptions import ClientError, BotoCoreError
from dotenv import load_dotenv
from .utils import get_secret_hash
from boto3.dynamodb.conditions import Key, Attr
from typing import Optional, Dict, Any

load_dotenv()

# Environment variable loading and validation
AWS_REGION = os.getenv("AWS_REGION")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
DDB_TABLE = os.getenv("DDB_TABLE")
DYNAMODB_CONVERSATION_TABLE = os.getenv("DYNAMODB_CONVERSATION_TABLE")

_required_envs = [
    AWS_REGION, COGNITO_USER_POOL_ID, COGNITO_CLIENT_ID,
    S3_BUCKET_NAME, DDB_TABLE, DYNAMODB_CONVERSATION_TABLE
]
if not all(_required_envs):
    raise HTTPException(status_code=500, detail="Server configuration error: Missing environment variable(s)")

# Resource initialization with error handling
try:
    client = boto3.client("cognito-idp", region_name=AWS_REGION)
    s3_client = boto3.client("s3", region_name=AWS_REGION)
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    metadata_table = dynamodb.Table(DDB_TABLE)
    conversations_table = dynamodb.Table(DYNAMODB_CONVERSATION_TABLE)
except Exception as e:
    logging.exception("Failed to initialize AWS SDK clients/resources.")
    raise HTTPException(status_code=500, detail="Failed to initialize AWS resources.")

def confirm_sign_up(email: str, code: str) -> Dict[str, str]:
    """
    Confirm a user's Cognito registration with a confirmation code.
    Args:
        email (str): User's email address.
        code  (str): Confirmation code received by the user.
    Returns:
        dict: Success message.
    Raises:
        HTTPException: For invalid input, AWS errors, or code issues.
    """
    if not email or not code:
        raise HTTPException(status_code=400, detail="Email and confirmation code are required.")

    try:
        client.admin_get_user(UserPoolId=COGNITO_USER_POOL_ID, Username=email)
        client.confirm_sign_up(
            ClientId=COGNITO_CLIENT_ID,
            SecretHash=get_secret_hash(email),
            Username=email,
            ConfirmationCode=code
        )
        return {"message": "User confirmed successfully."}
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "UserNotFoundException":
            raise HTTPException(status_code=404, detail="User not found.")
        elif error_code == "CodeMismatchException":
            raise HTTPException(status_code=400, detail="Invalid confirmation code.")
        elif error_code == "ExpiredCodeException":
            raise HTTPException(status_code=400, detail="Confirmation code expired.")
        else:
            logging.error(f"ClientError in confirm_sign_up: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to confirm user: {error_code}")
    except BotoCoreError:
        logging.exception("BotoCoreError in confirm_sign_up")
        raise HTTPException(status_code=500, detail="Internal server error.")
    except Exception as e:
        logging.exception("Unknown error in confirm_sign_up")
        raise HTTPException(status_code=500, detail="Unexpected error confirming user.")

def get_user(access_token: str) -> Dict[str, Optional[str]]:
    """
    Retrieve user details using a Cognito access token.
    Args:
        access_token (str): User's Cognito access token.
    Returns:
        dict: User's id (username), email, and name.
    Raises:
        HTTPException: For invalid/expired tokens or AWS errors.
    """
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required.")

    try:
        response = client.get_user(AccessToken=access_token)
        email_attr = next((attr['Value'] for attr in response['UserAttributes'] if attr['Name'] == 'email'), None)
        name_attr = next((attr['Value'] for attr in response['UserAttributes'] if attr['Name'] == 'name'), None)
        username_attr = response.get('Username')
        return {
            "id": username_attr,
            "email": email_attr,
            "name": name_attr
        }
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "NotAuthorizedException":
            raise HTTPException(status_code=401, detail="Invalid or expired access token.")
        elif code == "ResourceNotFoundException":
            raise HTTPException(status_code=404, detail="User not found.")
        else:
            logging.error(f"ClientError in get_user: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to retrieve user details: {code}")
    except BotoCoreError:
        logging.exception("BotoCoreError in get_user")
        raise HTTPException(status_code=500, detail="Internal server error.")
    except Exception as e:
        logging.exception("Unknown error in get_user")
        raise HTTPException(status_code=500, detail="Unexpected error retrieving user details.")

def delete_user(access_token: str) -> Dict[str, str]:
    """
    Delete a Cognito user, their uploaded files/metadata, and all DynamoDB conversation entries.
    Args:
        access_token (str): Cognito access token of the user to delete.
    Returns:
        dict: Success message.
    Raises:
        HTTPException: For missing tokens or AWS errors.
    """
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required for deletion.")

    try:
        user_info = get_user(access_token)
        user_id = user_info.get('id')
        if not user_id:
            raise HTTPException(status_code=400, detail="Failed to extract user ID from access token.")

        # 1. Delete user files and related metadata
        response = metadata_table.scan(FilterExpression=Key("user_id").eq(user_id))
        file_hashes = []
        for item in response.get("Items", []):
            s3_key = item.get("s3_key")
            file_hash = item.get("hash")
            if s3_key:
                # Delete original file
                try:
                    s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
                except Exception as ex:
                    logging.warning(f"Failed to delete S3 object {s3_key}: {ex}")
                # Attempt to delete ".converted.pdf"
                converted_key = f"{s3_key}.converted.pdf"
                try:
                    s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=converted_key)
                except Exception as ex:
                    logging.debug(f"No converted S3 object for {converted_key}: {ex}")
            if file_hash:
                file_hashes.append(file_hash)
                try:
                    metadata_table.delete_item(Key={"user_id": user_id, "hash": file_hash})
                except Exception as ex:
                    logging.warning(f"Failed to delete metadata item {file_hash} for user {user_id}: {ex}")

        # 2. Delete conversations per file_hash
        for file_hash in file_hashes:
            convo_response = conversations_table.scan(
                FilterExpression=Key("user_id").eq(user_id) & Attr("file_hash_timestamp").begins_with(file_hash)
            )
            for convo_item in convo_response.get("Items", []):
                file_hash_ts = convo_item.get("file_hash_timestamp")
                if file_hash_ts:
                    try:
                        conversations_table.delete_item(
                            Key={"user_id": user_id, "file_hash_timestamp": file_hash_ts}
                        )
                    except Exception as ex:
                        logging.warning(f"Failed to delete conversation item {file_hash_ts}: {ex}")

        # 3. Clean up any leftover conversations for this user
        leftover_convos = conversations_table.scan(FilterExpression=Key("user_id").eq(user_id))
        for leftover in leftover_convos.get("Items", []):
            file_hash_ts = leftover.get("file_hash_timestamp")
            if file_hash_ts:
                try:
                    conversations_table.delete_item(
                        Key={"user_id": user_id, "file_hash_timestamp": file_hash_ts}
                    )
                except Exception as ex:
                    logging.warning(f"Failed to delete leftover conversation {file_hash_ts}: {ex}")

        # 4. Delete the Cognito user account itself
        client.admin_delete_user(UserPoolId=COGNITO_USER_POOL_ID, Username=user_id)

        return {"message": f"User {user_id} and all related data deleted successfully."}

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == "UserNotFoundException":
            raise HTTPException(status_code=404, detail="User not found.")
        elif error_code == "NotAuthorizedException":
            raise HTTPException(status_code=401, detail="Invalid or expired access token.")
        else:
            logging.error(f"ClientError in delete_user: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to delete user account: {error_code}")
    except BotoCoreError:
        logging.exception("BotoCoreError in delete_user")
        raise HTTPException(status_code=500, detail="Internal server error during deletion.")
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Unknown error in delete_user")
        raise HTTPException(status_code=500, detail="Failed to delete all user data. User account may not be fully removed.")
