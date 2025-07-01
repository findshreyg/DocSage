import boto3
import hmac
import hashlib
import base64
import os
import logging
from fastapi import HTTPException
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

AWS_REGION = os.getenv("AWS_REGION")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")
COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")

client = boto3.client("cognito-idp", region_name=AWS_REGION)

def get_secret_hash(username: str) -> str:
    message = username + COGNITO_CLIENT_ID
    dig = hmac.new(
        COGNITO_CLIENT_SECRET.encode(),
        msg=message.encode(),
        digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()

def sign_up(email: str, password: str):
    if not email or not password:
        raise HTTPException(400, "Email and password required.")
    try:
        client.sign_up(
            ClientId=COGNITO_CLIENT_ID,
            SecretHash=get_secret_hash(email),
            Username=email,
            Password=password
        )
    except ClientError as e:
        logger.exception(f"SignUp failed: {e}")
        raise HTTPException(400, "Sign up failed. Possible duplicate email or invalid format.")

def confirm_sign_up(email: str, code: str):
    if not email or not code:
        raise HTTPException(400, "Email and confirmation code required.")
    try:
        client.admin_get_user(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=email
        )
        client.confirm_sign_up(
            ClientId=COGNITO_CLIENT_ID,
            SecretHash=get_secret_hash(email),
            Username=email,
            ConfirmationCode=code
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'UserNotFoundException':
            logger.exception(f"ConfirmSignUp failed: User not found for {email}")
            raise HTTPException(404, "User not found.")
        logger.exception(f"ConfirmSignUp failed: {e}")
        raise HTTPException(400, "Invalid confirmation code or user.")


def resend_confirmation_code(email: str):
    if not email:
        raise HTTPException(400, "Email is required.")
    try:
        user = client.admin_get_user(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=email
        )
        # Check if user is already confirmed
        if user["UserStatus"] == "CONFIRMED":
            raise HTTPException(400, "User is already confirmed.")

        client.resend_confirmation_code(
            ClientId=COGNITO_CLIENT_ID,
            SecretHash=get_secret_hash(email),
            Username=email
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'UserNotFoundException':
            logger.exception(f"Resend confirmation failed: User not found for {email}")
            raise HTTPException(404, "User not found.")
        logger.exception(f"Resend confirmation failed: {e}")
        raise HTTPException(400, "Resend confirmation failed. Possibly already confirmed.")

def login(email: str, password: str):
    if not email or not password:
        raise HTTPException(400, "Email and password required.")
    try:
        return client.initiate_auth(
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': password,
                'SECRET_HASH': get_secret_hash(email)
            }
        )
    except ClientError as e:
        logger.exception(f"Login failed: {e}")
        raise HTTPException(401, "Invalid email or password.")

def refresh_token(email: str, refresh_token: str):
    if not email or not refresh_token:
        raise HTTPException(400, "Email and refresh token required.")
    try:
        return client.initiate_auth(
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow='REFRESH_TOKEN_AUTH',
            AuthParameters={
                'REFRESH_TOKEN': refresh_token,
                'SECRET_HASH': get_secret_hash(email)
            }
        )
    except ClientError as e:
        logger.exception(f"Refresh token failed: {e}")
        raise HTTPException(401, "Invalid refresh token.")

def forgot_password(email: str):
    if not email:
        raise HTTPException(400, "Email required.")
    try:
        # Check if user exists
        client.admin_get_user(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=email
        )
        client.forgot_password(
            ClientId=COGNITO_CLIENT_ID,
            SecretHash=get_secret_hash(email),
            Username=email
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'UserNotFoundException':
            logger.exception(f"Forgot password failed: User not found for {email}")
            raise HTTPException(404, "User not found.")
        logger.exception(f"Forgot password failed: {e}")
        raise HTTPException(400, "Failed to send forgot password code.")

def confirm_forgot_password(email: str, code: str, new_password: str):
    if not email or not code or not new_password:
        raise HTTPException(400, "Email, code and new password required.")
    try:
        client.confirm_forgot_password(
            ClientId=COGNITO_CLIENT_ID,
            SecretHash=get_secret_hash(email),
            Username=email,
            ConfirmationCode=code,
            Password=new_password
        )
    except ClientError as e:
        logger.exception(f"Confirm forgot password failed: {e}")
        raise HTTPException(400, "Invalid code or new password format.")

def change_password(access_token: str, old_password: str, new_password: str):
    if not access_token or not old_password or not new_password:
        raise HTTPException(400, "All password fields required.")
    try:
        client.change_password(
            PreviousPassword=old_password,
            ProposedPassword=new_password,
            AccessToken=access_token
        )
    except ClientError as e:
        logger.exception(f"Change password failed: {e}")
        raise HTTPException(400, "Invalid current password or policy violation.")

def get_user(access_token: str):
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required.")
    try:
        response = client.get_user(AccessToken=access_token)
        return response
    except ClientError as e:
        logger.exception(f"Get user failed: {e}")
        code = e.response["Error"]["Code"]
        if code == "NotAuthorizedException":
            raise HTTPException(status_code=401, detail="Invalid or expired access token.")
        elif code == "ResourceNotFoundException":
            raise HTTPException(status_code=404, detail="User not found.")
        else:
            raise HTTPException(status_code=400, detail="Failed to retrieve user.")
    except Exception as e:
        logger.exception(f"Unexpected error in get_user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")

def delete_user(user_id: str):
    from upload.upload_handler import delete_all_user_files_and_metadata

    if not user_id:
        raise HTTPException(400, "User ID required.")
    try:
        # Try to delete all user files, metadata, and conversations FIRST
        delete_all_user_files_and_metadata(user_id)
        logger.info("Deleted all files, metadata, and conversations for user")

        # Only if that succeeds, delete the Cognito user
        client.admin_delete_user(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=user_id
        )
    except ClientError as e:
        logger.exception(f"Delete user failed: {e}")
        raise HTTPException(400, "Failed to delete user.")
    except Exception as e:
        logger.exception(f"Failed to clean up all user data for {user_id}: {e}")
        raise HTTPException(400, "Failed to delete all related user data. User account was not deleted.")

# Logout function for Cognito
def logout(access_token: str):
    if not access_token:
        raise HTTPException(status_code=400, detail="Access token required for logout.")
    try:
        client.global_sign_out(
            AccessToken=access_token
        )
    except ClientError as e:
        logger.exception(f"Logout failed: {e}")
        raise HTTPException(status_code=400, detail="Failed to log out. Token might be invalid or expired.")