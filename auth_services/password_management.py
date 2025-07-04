# Import necessary libraries for AWS Cognito and environment management
import boto3
import os
import logging
from fastapi import HTTPException
from botocore.exceptions import ClientError, BotoCoreError
from dotenv import load_dotenv
from utils import get_secret_hash

# Load environment variables from a .env file
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Retrieve AWS and Cognito configuration from environment variables
AWS_REGION = os.getenv("AWS_REGION")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")
COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")

# Check if all required environment variables are set
if not all([AWS_REGION, COGNITO_USER_POOL_ID, COGNITO_CLIENT_ID, COGNITO_CLIENT_SECRET]):
    logger.error("One or more required environment variables are missing.")
    raise HTTPException(status_code=500, detail="Server configuration error.")

# Initialize the Cognito client
try:
    client = boto3.client("cognito-idp", region_name=AWS_REGION)
except Exception as e:
    logger.exception("Failed to initialize Cognito client.")
    raise HTTPException(status_code=500, detail="Internal server error.")

# Function to handle forgot password requests
def forgot_password(email: str):
    # Validate email input
    if not email:
        raise HTTPException(status_code=400, detail="Email is required.")
    try:
        # Check if user exists
        client.admin_get_user(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=email
        )
        # Initiate forgot password process
        client.forgot_password(
            ClientId=COGNITO_CLIENT_ID,
            SecretHash=get_secret_hash(email),
            Username=email
        )
        return {"message": "Forgot password code sent successfully."}

    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.exception(f"Forgot password failed: {error_code} - {e}")
        # Handle specific error codes
        if error_code == 'UserNotFoundException':
            raise HTTPException(status_code=404, detail="User not found.")
        elif error_code == 'InvalidParameterException':
            raise HTTPException(status_code=400, detail="Invalid email format.")
        else:
            raise HTTPException(status_code=400, detail="Failed to send forgot password code.")
    except BotoCoreError as e:
        logger.exception(f"BotoCoreError: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")

# Function to confirm password reset with a code
def confirm_forgot_password(email: str, code: str, new_password: str):
    # Validate input parameters
    if not all([email, code, new_password]):
        raise HTTPException(status_code=400, detail="Email, code, and new password are required.")
    try:
        # Confirm the password reset
        client.confirm_forgot_password(
            ClientId=COGNITO_CLIENT_ID,
            SecretHash=get_secret_hash(email),
            Username=email,
            ConfirmationCode=code,
            Password=new_password
        )
        return {"message": "Password reset successful."}

    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.exception(f"Confirm forgot password failed: {error_code} - {e}")
        # Handle specific error codes
        if error_code == 'CodeMismatchException':
            raise HTTPException(status_code=400, detail="Invalid confirmation code.")
        elif error_code == 'ExpiredCodeException':
            raise HTTPException(status_code=400, detail="Confirmation code expired.")
        elif error_code == 'InvalidPasswordException':
            raise HTTPException(status_code=400, detail="New password does not meet complexity requirements.")
        elif error_code == 'UserNotFoundException':
            raise HTTPException(status_code=404, detail="User not found.")
        else:
            raise HTTPException(status_code=400, detail="Failed to confirm forgot password.")
    except BotoCoreError as e:
        logger.exception(f"BotoCoreError: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")

# Function to change the user's password
def change_password(access_token: str, old_password: str, new_password: str):
    # Validate input parameters
    if not all([access_token, old_password, new_password]):
        raise HTTPException(status_code=400, detail="Access token, old password, and new password are required.")
    try:
        # Change the password
        client.change_password(
            PreviousPassword=old_password,
            ProposedPassword=new_password,
            AccessToken=access_token
        )
        return {"message": "Password changed successfully."}

    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.exception(f"Change password failed: {error_code} - {e}")
        # Handle specific error codes
        if error_code == 'NotAuthorizedException':
            raise HTTPException(status_code=401, detail="Invalid or expired access token.")
        elif error_code == 'InvalidParameterException':
            raise HTTPException(status_code=400, detail="Invalid password format.")
        elif error_code == 'InvalidPasswordException':
            raise HTTPException(status_code=400, detail="New password does not meet complexity requirements.")
        elif error_code == 'LimitExceededException':
            raise HTTPException(status_code=429, detail="Attempt limit exceeded, please try again later.")
        else:
            raise HTTPException(status_code=400, detail="Failed to change password.")
    except BotoCoreError as e:
        logger.exception(f"BotoCoreError: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")

# Function to resend the confirmation code to the user
def resend_confirmation_code(email: str):
    # Validate email input
    if not email:
        raise HTTPException(status_code=400, detail="Email is required.")
    try:
        # Check if user is already confirmed
        user = client.admin_get_user(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=email
        )

        if user.get("UserStatus") == "CONFIRMED":
            raise HTTPException(status_code=400, detail="User is already confirmed.")

        # Resend the confirmation code
        client.resend_confirmation_code(
            ClientId=COGNITO_CLIENT_ID,
            SecretHash=get_secret_hash(email),
            Username=email
        )
        return {"message": "Confirmation code resent successfully."}

    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.exception(f"Resend confirmation failed: {error_code} - {e}")
        # Handle specific error codes
        if error_code == 'UserNotFoundException':
            raise HTTPException(status_code=404, detail="User not found.")
        elif error_code == 'InvalidParameterException':
            raise HTTPException(status_code=400, detail="Invalid email format.")
        else:
            raise HTTPException(status_code=400, detail="Failed to resend confirmation code.")
    except BotoCoreError as e:
        logger.exception(f"BotoCoreError: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")
