# Import necessary libraries for AWS Cognito and environment management
import boto3
import os
from fastapi import HTTPException
from botocore.exceptions import ClientError, BotoCoreError
from dotenv import load_dotenv
from utils import get_secret_hash

# Load environment variables from a .env file
load_dotenv()


# Retrieve AWS and Cognito configuration from environment variables
AWS_REGION = os.getenv("AWS_REGION")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")
COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")

# Check if all required environment variables are set
if not all([AWS_REGION, COGNITO_USER_POOL_ID, COGNITO_CLIENT_ID, COGNITO_CLIENT_SECRET]):
    raise HTTPException(status_code=500, detail="Server configuration error.")

# Initialize the Cognito client
try:
    client = boto3.client("cognito-idp", region_name=AWS_REGION)
except Exception as e:
    raise HTTPException(status_code=500, detail="Internal server error.")

# Function to handle forgot password requests
def forgot_password(email: str):
    """
    Start the forgot password flow for a user.
    This verifies the user exists, then triggers Cognito to send a reset code.

    Args:
        email (str): The user's email address.

    Raises:
        HTTPException: For missing email or Cognito errors.

    Returns:
        dict: Success message if the code is sent.
    """
    # Validate email input
    if not email:
        raise HTTPException(status_code=400, detail="Email is required.")
    try:
        # Verify the user exists in the User Pool
        client.admin_get_user(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=email
        )
        # Request Cognito to send a forgot password confirmation code to the user
        client.forgot_password(
            ClientId=COGNITO_CLIENT_ID,
            SecretHash=get_secret_hash(email),
            Username=email
        )
        return {"message": "Forgot password code sent successfully."}

    except ClientError as e:
        error_code = e.response['Error']['Code']
        # Handle user not found or invalid input
        if error_code == 'UserNotFoundException':
            raise HTTPException(status_code=404, detail="User not found.")
        elif error_code == 'InvalidParameterException':
            raise HTTPException(status_code=400, detail="Invalid email format.")
        else:
            raise HTTPException(status_code=400, detail="Failed to send forgot password code.")
    except BotoCoreError:
        raise HTTPException(status_code=500, detail="Internal server error.")

# Function to confirm password reset with a code
def confirm_forgot_password(email: str, code: str, new_password: str):
    """
    Confirm the user's password reset by providing the received code and new password.

    Args:
        email (str): The user's email address.
        code (str): The confirmation code received by email.
        new_password (str): The new password to set.

    Raises:
        HTTPException: For missing input, invalid code, or Cognito errors.

    Returns:
        dict: Success message if the password is reset.
    """
    # Validate input parameters
    if not all([email, code, new_password]):
        raise HTTPException(status_code=400, detail="Email, code, and new password are required.")
    try:
        # Call Cognito to confirm the password reset using the code
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
        # Handle invalid or expired code, invalid password, or user not found
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
    except BotoCoreError:
        raise HTTPException(status_code=500, detail="Internal server error.")

# Function to change the user's password when logged in
def change_password(access_token: str, old_password: str, new_password: str):
    """
    Change the password for a signed-in user using their current password.

    Args:
        access_token (str): The valid access token for the authenticated user.
        old_password (str): The user's current password.
        new_password (str): The new password to be set.

    Raises:
        HTTPException: For missing input, auth issues, or Cognito errors.

    Returns:
        dict: Success message if the password is changed.
    """
    # Validate input parameters
    if not all([access_token, old_password, new_password]):
        raise HTTPException(status_code=400, detail="Access token, old password, and new password are required.")
    try:
        # Call Cognito to change the password using the access token
        client.change_password(
            PreviousPassword=old_password,
            ProposedPassword=new_password,
            AccessToken=access_token
        )
        return {"message": "Password changed successfully."}

    except ClientError as e:
        error_code = e.response['Error']['Code']
        # Handle token or password errors
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
    except BotoCoreError:
        raise HTTPException(status_code=500, detail="Internal server error.")

# Function to resend the signup confirmation code to the user
def resend_confirmation_code(email: str):
    """
    Resend the confirmation code for email verification during signup.

    Args:
        email (str): The user's email address.

    Raises:
        HTTPException: For missing email, already confirmed users, or Cognito errors.

    Returns:
        dict: Success message if the code is resent.
    """
    # Validate email input
    if not email:
        raise HTTPException(status_code=400, detail="Email is required.")
    try:
        # Check user status to ensure they are not already confirmed
        user = client.admin_get_user(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=email
        )

        if user.get("UserStatus") == "CONFIRMED":
            # User already confirmed, so do not resend code
            raise HTTPException(status_code=400, detail="User is already confirmed.")

        # Request Cognito to resend the confirmation code
        client.resend_confirmation_code(
            ClientId=COGNITO_CLIENT_ID,
            SecretHash=get_secret_hash(email),
            Username=email
        )
        return {"message": "Confirmation code resent successfully."}

    except ClientError as e:
        error_code = e.response['Error']['Code']
        # Handle errors like user not found or invalid email
        if error_code == 'UserNotFoundException':
            raise HTTPException(status_code=404, detail="User not found.")
        elif error_code == 'InvalidParameterException':
            raise HTTPException(status_code=400, detail="Invalid email format.")
        else:
            raise HTTPException(status_code=400, detail="Failed to resend confirmation code.")
    except BotoCoreError:
        raise HTTPException(status_code=500, detail="Internal server error.")
