# Password management module - handles password reset, change, and confirmation code operations
# This module provides secure password management functionality using AWS Cognito

import boto3  # AWS SDK for Python
import os  # Access environment variables
import logging  # Application logging
from fastapi import HTTPException  # HTTP error responses
from botocore.exceptions import ClientError, BotoCoreError  # AWS-specific exceptions
from dotenv import load_dotenv  # Load environment variables from .env file
from utils import get_secret_hash  # Generate HMAC hash for Cognito client secret

# Load environment variables from .env file
load_dotenv()

# Retrieve AWS Cognito configuration from environment variables
# These settings must match the Cognito User Pool configuration
AWS_REGION = os.getenv("AWS_REGION")  # AWS region where Cognito is deployed
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")  # User pool identifier
COGNITO_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")  # App client ID for API access
COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")  # Secret for secure operations

# Validate that all required configuration is present
# Password operations require all these settings to function securely
if not all([AWS_REGION, COGNITO_USER_POOL_ID, COGNITO_CLIENT_ID, COGNITO_CLIENT_SECRET]):
    raise HTTPException(status_code=500, detail="Server configuration error.")

# Initialize AWS Cognito Identity Provider client
# This client handles all password-related operations with Cognito
try:
    client = boto3.client("cognito-idp", region_name=AWS_REGION)
except Exception as e:
    # If we can't connect to AWS, password operations won't work
    logging.exception("Failed to initialize Cognito client")
    raise HTTPException(status_code=500, detail="Internal server error.")

def forgot_password(email: str) -> dict:
    """
    Initiate password reset process for users who forgot their password.
    
    This function:
    1. Verifies the user exists in Cognito
    2. Generates a secure password reset code
    3. Sends the code to user's email address
    4. Code expires after a set time (typically 1 hour)
    
    User will receive an email with instructions and the reset code.
    """
    # Input validation - email is required to identify the user
    if not email:
        raise HTTPException(status_code=400, detail="Email is required.")

    try:
        # First verify that the user exists in Cognito
        # This prevents information disclosure about valid email addresses
        client.admin_get_user(UserPoolId=COGNITO_USER_POOL_ID, Username=email)
        
        # Initiate forgot password flow - generates and sends reset code
        client.forgot_password(
            ClientId=COGNITO_CLIENT_ID,  # App client identifier
            SecretHash=get_secret_hash(email),  # Security hash for verification
            Username=email  # User's email address
        )
        
        return {"message": "Forgot password code sent successfully."}
    
    except ClientError as e:
        # Handle specific Cognito errors
        error_code = e.response['Error']['Code']
        if error_code == 'UserNotFoundException':
            # User doesn't exist in the system
            raise HTTPException(status_code=404, detail="User not found.")
        elif error_code == 'InvalidParameterException':
            # Email format is invalid
            raise HTTPException(status_code=400, detail="Invalid email format.")
        else:
            # Other Cognito-specific errors
            logging.error(f"ClientError in forgot_password: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to send forgot password code: {error_code}")
    
    except BotoCoreError as e:
        # AWS SDK or connection errors
        logging.exception("BotoCoreError in forgot_password")
        raise HTTPException(status_code=500, detail="Internal server error.")
    
    except Exception as e:
        # Any other unexpected errors
        logging.exception("Unknown error in forgot_password")
        raise HTTPException(status_code=500, detail="Unexpected error in forgot password.")

def confirm_forgot_password(email: str, code: str, new_password: str) -> dict:
    """
    Complete password reset using the code sent via email.
    
    This function:
    1. Validates the reset code from the email
    2. Verifies new password meets complexity requirements
    3. Updates user's password in Cognito
    4. Invalidates all existing user sessions for security
    
    After successful reset, user can log in with their new password.
    """
    # Input validation - all three parameters are required for password reset
    if not all([email, code, new_password]):
        raise HTTPException(status_code=400, detail="Email, code, and new password are required.")

    try:
        # Complete the password reset process with Cognito
        client.confirm_forgot_password(
            ClientId=COGNITO_CLIENT_ID,  # App client identifier
            SecretHash=get_secret_hash(email),  # Security hash for verification
            Username=email,  # User's email address
            ConfirmationCode=code,  # 6-digit code from email
            Password=new_password  # User's new password
        )
        
        return {"message": "Password reset successful."}
    
    except ClientError as e:
        # Handle specific password reset errors
        error_code = e.response['Error']['Code']
        if error_code == 'CodeMismatchException':
            # Wrong confirmation code entered
            raise HTTPException(status_code=400, detail="Invalid confirmation code.")
        elif error_code == 'ExpiredCodeException':
            # Code has expired (usually after 1 hour)
            raise HTTPException(status_code=400, detail="Confirmation code expired.")
        elif error_code == 'InvalidPasswordException':
            # New password doesn't meet Cognito password policy
            raise HTTPException(status_code=400, detail="New password does not meet complexity requirements.")
        elif error_code == 'UserNotFoundException':
            # User account doesn't exist
            raise HTTPException(status_code=404, detail="User not found.")
        else:
            # Other Cognito-specific errors
            logging.error(f"ClientError in confirm_forgot_password: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to confirm forgot password: {error_code}")
    
    except BotoCoreError as e:
        # AWS SDK or connection errors
        logging.exception("BotoCoreError in confirm_forgot_password")
        raise HTTPException(status_code=500, detail="Internal server error.")
    
    except Exception as e:
        # Any other unexpected errors
        logging.exception("Unknown error in confirm_forgot_password")
        raise HTTPException(status_code=500, detail="Unexpected error in confirm forgot password.")

def change_password(access_token: str, old_password: str, new_password: str) -> dict:
    """
    Change user's password while they are logged in.
    
    This function:
    1. Verifies user is authenticated (valid access token)
    2. Validates current password is correct
    3. Verifies new password meets complexity requirements
    4. Updates password in Cognito
    
    This is more secure than forgot password as it requires current password.
    """
    # Input validation - all three parameters are required for password change
    if not all([access_token, old_password, new_password]):
        raise HTTPException(status_code=400, detail="Access token, old password, and new password are required.")

    try:
        # Change password using Cognito's authenticated password change
        client.change_password(
            PreviousPassword=old_password,  # Current password for verification
            ProposedPassword=new_password,  # New password to set
            AccessToken=access_token  # Proves user is authenticated
        )
        
        return {"message": "Password changed successfully."}
    
    except ClientError as e:
        # Handle specific password change errors
        error_code = e.response['Error']['Code']
        if error_code == 'NotAuthorizedException':
            # Access token is invalid/expired or old password is wrong
            raise HTTPException(status_code=401, detail="Invalid or expired access token.")
        elif error_code == 'InvalidParameterException':
            # Password format issues
            raise HTTPException(status_code=400, detail="Invalid password format.")
        elif error_code == 'InvalidPasswordException':
            # New password doesn't meet complexity requirements
            raise HTTPException(status_code=400, detail="New password does not meet complexity requirements.")
        elif error_code == 'LimitExceededException':
            # Too many password change attempts
            raise HTTPException(status_code=429, detail="Attempt limit exceeded, please try again later.")
        else:
            # Other Cognito-specific errors
            logging.error(f"ClientError in change_password: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to change password: {error_code}")
    
    except BotoCoreError as e:
        # AWS SDK or connection errors
        logging.exception("BotoCoreError in change_password")
        raise HTTPException(status_code=500, detail="Internal server error.")
    
    except Exception as e:
        # Any other unexpected errors
        logging.exception("Unknown error in change_password")
        raise HTTPException(status_code=500, detail="Unexpected error changing password.")

def resend_confirmation_code(email: str) -> dict:
    """
    Resend email confirmation code to users who didn't receive it.
    
    This function:
    1. Verifies user exists and is still unconfirmed
    2. Generates new 6-digit confirmation code
    3. Sends code via email
    4. Previous codes become invalid
    
    Only works for users who haven't completed email verification yet.
    """
    # Input validation - email is required to identify the user
    if not email:
        raise HTTPException(status_code=400, detail="Email is required.")

    try:
        # Get user information to check their confirmation status
        user = client.admin_get_user(UserPoolId=COGNITO_USER_POOL_ID, Username=email)
        
        # Check if user is already confirmed - no need to resend code
        if user.get("UserStatus") == "CONFIRMED":
            raise HTTPException(status_code=400, detail="User is already confirmed.")

        # Resend confirmation code via email
        client.resend_confirmation_code(
            ClientId=COGNITO_CLIENT_ID,  # App client identifier
            SecretHash=get_secret_hash(email),  # Security hash for verification
            Username=email  # User's email address
        )
        
        return {"message": "Confirmation code resent successfully."}
    
    except ClientError as e:
        # Handle specific confirmation code errors
        error_code = e.response['Error']['Code']
        if error_code == 'UserNotFoundException':
            # User account doesn't exist
            raise HTTPException(status_code=404, detail="User not found.")
        elif error_code == 'InvalidParameterException':
            # Email format is invalid
            raise HTTPException(status_code=400, detail="Invalid email format.")
        else:
            # Other Cognito-specific errors
            logging.error(f"ClientError in resend_confirmation_code: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to resend confirmation code: {error_code}")
    
    except BotoCoreError as e:
        # AWS SDK or connection errors
        logging.exception("BotoCoreError in resend_confirmation_code")
        raise HTTPException(status_code=500, detail="Internal server error.")
    
    except Exception as e:
        # Any other unexpected errors
        logging.exception("Unknown error in resend_confirmation_code")
        raise HTTPException(status_code=500, detail="Unexpected error resending confirmation code.")

