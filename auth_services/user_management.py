# Import necessary libraries for AWS Cognito, S3, and DynamoDB
import boto3
import os
from fastapi import HTTPException
from botocore.exceptions import ClientError, BotoCoreError
from dotenv import load_dotenv
from utils import get_secret_hash

from boto3.dynamodb.conditions import Key, Attr

# Load environment variables from a .env file
load_dotenv()



# Retrieve AWS and Cognito configuration from environment variables
AWS_REGION = os.getenv("AWS_REGION") 
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
DDB_TABLE = os.getenv("DDB_TABLE")
DYNAMODB_CONVERSATION_TABLE = os.getenv("DYNAMODB_CONVERSATION_TABLE")

# Check if all required environment variables are set
if not all([AWS_REGION, COGNITO_USER_POOL_ID, COGNITO_CLIENT_ID, S3_BUCKET_NAME, DDB_TABLE, DYNAMODB_CONVERSATION_TABLE]):
    raise HTTPException(status_code=500, detail="Server configuration error.")

# Initialize AWS clients for Cognito, S3, and DynamoDB
client = boto3.client("cognito-idp", region_name=AWS_REGION)
s3_client = boto3.client("s3", region_name=AWS_REGION)
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
metadata_table = dynamodb.Table(DDB_TABLE)
conversations_table = dynamodb.Table(DYNAMODB_CONVERSATION_TABLE)

# Function to confirm user sign-up with a confirmation code
def confirm_sign_up(email: str, code: str):
    """
    Confirm a new user's sign-up by validating their email and confirmation code.

    Args:
        email (str): The user's email address.
        code (str): The confirmation code received by email.

    Raises:
        HTTPException: If inputs are missing, user not found, or code is invalid/expired.

    Returns:
        dict: Success message if the user is confirmed.
    """
    # Validate email and code input
    if not email or not code:
        raise HTTPException(status_code=400, detail="Email and confirmation code are required.")
    try:
        # Check if user exists in Cognito
        client.admin_get_user(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=email
        )

        # Confirm user sign-up using the provided code
        client.confirm_sign_up(
            ClientId=COGNITO_CLIENT_ID,
            SecretHash=get_secret_hash(email),
            Username=email,
            ConfirmationCode=code
        )
        return {"message": "User confirmed successfully."}

    except ClientError as e:
        error_code = e.response["Error"]["Code"]

        # Handle specific error codes returned by Cognito
        if error_code == "UserNotFoundException":
            raise HTTPException(status_code=404, detail="User not found.")
        elif error_code == "CodeMismatchException":
            raise HTTPException(status_code=400, detail="Invalid confirmation code.")
        elif error_code == "ExpiredCodeException":
            raise HTTPException(status_code=400, detail="Confirmation code expired.")
        else:
            raise HTTPException(status_code=400, detail="Failed to confirm user. Please check the code and try again.")

    except BotoCoreError:
        raise HTTPException(status_code=500, detail="Internal server error.")

# Function to retrieve user details using an access token
def get_user(access_token: str):
    """
    Retrieve user information based on a valid access token.

    Args:
        access_token (str): A valid Cognito access token.

    Raises:
        HTTPException: If the token is missing, invalid, or expired.

    Returns:
        dict: User details including ID, email, and name.
    """
    # Validate access token input
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required.")

    try:
        # Call Cognito to get user attributes using the token
        response = client.get_user(AccessToken=access_token)

        # Extract specific attributes: email and name
        email_attr = next(
            (attr['Value'] for attr in response['UserAttributes'] if attr['Name'] == 'email'),
            None
        )
        name_attr = next(
            (attr['Value'] for attr in response['UserAttributes'] if attr['Name'] == 'name'),
            None
        )
        username_attr = response.get('Username')

        return {
            "id": username_attr,
            "email": email_attr,
            "name": name_attr
        }

    except ClientError as e:
        code = e.response["Error"]["Code"]

        # Handle possible errors like expired token or user not found
        if code == "NotAuthorizedException":
            raise HTTPException(status_code=401, detail="Invalid or expired access token.")
        elif code == "ResourceNotFoundException":
            raise HTTPException(status_code=404, detail="User not found.")
        else:
            raise HTTPException(status_code=400, detail="Failed to retrieve user details.")

    except BotoCoreError:
        raise HTTPException(status_code=500, detail="Internal server error.")

# Function to delete a user and all associated metadata, files, and conversations
def delete_user(access_token: str):
    """
    Delete a user and all related S3 files, DynamoDB metadata, and conversation records.

    Args:
        access_token (str): A valid Cognito access token.

    Raises:
        HTTPException: If user not found, unauthorized, or any step fails.

    Returns:
        dict: Confirmation message after successful deletion.
    """
    user_info = None
    try:
        # Retrieve user information based on access token
        user_info = get_user(access_token)
        user_id = user_info.get('id')

        if not user_id:
            raise HTTPException(status_code=400, detail="Failed to extract user ID from access token.")

        # 1️⃣ Delete user files and related metadata
        response = metadata_table.scan(
            FilterExpression=Key("user_id").eq(user_id)
        )

        for item in response.get("Items", []):
            s3_key = item.get("s3_key")
            file_hash = item.get("hash")

            if s3_key:
                # Delete the original file in S3
                s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=s3_key)

                # Delete any converted version if it exists
                converted_key = s3_key + ".converted.pdf"
                s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=converted_key)

            if file_hash:
                # Delete metadata from DynamoDB
                metadata_table.delete_item(
                    Key={"user_id": user_id, "hash": file_hash}
                )

                # Delete related conversations for the file
                convo_response = conversations_table.scan(
                    FilterExpression=Key("user_id").eq(user_id) & Attr("file_hash_timestamp").begins_with(file_hash)
                )
                for convo_item in convo_response.get("Items", []):
                    file_hash_ts = convo_item.get("file_hash_timestamp")
                    if file_hash_ts:
                        conversations_table.delete_item(
                            Key={"user_id": user_id, "file_hash_timestamp": file_hash_ts}
                        )

        # 2️⃣ Extra safety: Remove any leftover conversations for this user
        leftover_convos = conversations_table.scan(
            FilterExpression=Key("user_id").eq(user_id)
        )
        for leftover in leftover_convos.get("Items", []):
            file_hash_ts = leftover.get("file_hash_timestamp")
            if file_hash_ts:
                conversations_table.delete_item(
                    Key={"user_id": user_id, "file_hash_timestamp": file_hash_ts}
                )

        # 3️⃣ Finally, delete the Cognito user account itself
        client.admin_delete_user(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=user_id
        )

        return {"message": f"User {user_id} and all related data deleted successfully."}

    except ClientError as e:
        error_code = e.response['Error']['Code']

        # Handle specific Cognito errors
        if error_code == "UserNotFoundException":
            raise HTTPException(status_code=404, detail="User not found.")
        elif error_code == "NotAuthorizedException":
            raise HTTPException(status_code=401, detail="Invalid or expired access token.")
        else:
            raise HTTPException(status_code=400, detail="Failed to delete user account.")

    except BotoCoreError:
        raise HTTPException(status_code=500, detail="Internal server error during deletion.")

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete all user data. User account may not be fully removed.")
