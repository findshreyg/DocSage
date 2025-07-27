import boto3
import os
import logging
from fastapi import HTTPException
from botocore.exceptions import ClientError, BotoCoreError
from dotenv import load_dotenv
from utils import get_secret_hash

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")
COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")

if not all([AWS_REGION, COGNITO_USER_POOL_ID, COGNITO_CLIENT_ID, COGNITO_CLIENT_SECRET]):
    raise HTTPException(status_code=500, detail="Server configuration error.")

try:
    client = boto3.client("cognito-idp", region_name=AWS_REGION)
except Exception as e:
    logging.exception("Failed to initialize Cognito client")
    raise HTTPException(status_code=500, detail="Internal server error.")

def forgot_password(email: str) -> dict:
    """
    Initiate forgot password flow for the Cognito user.

    Args:
        email (str): User email.

    Returns:
        dict: Success message.

    Raises:
        HTTPException: For any error condition.
    """
    if not email:
        raise HTTPException(status_code=400, detail="Email is required.")

    try:
        client.admin_get_user(UserPoolId=COGNITO_USER_POOL_ID, Username=email)
        client.forgot_password(
            ClientId=COGNITO_CLIENT_ID,
            SecretHash=get_secret_hash(email),
            Username=email
        )
        return {"message": "Forgot password code sent successfully."}
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'UserNotFoundException':
            raise HTTPException(status_code=404, detail="User not found.")
        elif error_code == 'InvalidParameterException':
            raise HTTPException(status_code=400, detail="Invalid email format.")
        else:
            logging.error(f"ClientError in forgot_password: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to send forgot password code: {error_code}")
    except BotoCoreError:
        logging.exception("BotoCoreError in forgot_password")
        raise HTTPException(status_code=500, detail="Internal server error.")
    except Exception as e:
        logging.exception("Unknown error in forgot_password")
        raise HTTPException(status_code=500, detail="Unexpected error in forgot password.")

def confirm_forgot_password(email: str, code: str, new_password: str) -> dict:
    """
    Confirm password reset with code and new password.

    Args:
        email (str): User email.
        code (str): Confirmation code.
        new_password (str): New password.

    Returns:
        dict: Success message.

    Raises:
        HTTPException: For any error condition.
    """
    if not all([email, code, new_password]):
        raise HTTPException(status_code=400, detail="Email, code, and new password are required.")

    try:
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
        if error_code == 'CodeMismatchException':
            raise HTTPException(status_code=400, detail="Invalid confirmation code.")
        elif error_code == 'ExpiredCodeException':
            raise HTTPException(status_code=400, detail="Confirmation code expired.")
        elif error_code == 'InvalidPasswordException':
            raise HTTPException(status_code=400, detail="New password does not meet complexity requirements.")
        elif error_code == 'UserNotFoundException':
            raise HTTPException(status_code=404, detail="User not found.")
        else:
            logging.error(f"ClientError in confirm_forgot_password: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to confirm forgot password: {error_code}")
    except BotoCoreError:
        logging.exception("BotoCoreError in confirm_forgot_password")
        raise HTTPException(status_code=500, detail="Internal server error.")
    except Exception as e:
        logging.exception("Unknown error in confirm_forgot_password")
        raise HTTPException(status_code=500, detail="Unexpected error in confirm forgot password.")

def change_password(access_token: str, old_password: str, new_password: str) -> dict:
    """
    Change user's password (while logged in).

    Args:
        access_token (str): User's Cognito access token.
        old_password (str): Old password.
        new_password (str): New password.

    Returns:
        dict: Success message.

    Raises:
        HTTPException: For any error condition.
    """
    if not all([access_token, old_password, new_password]):
        raise HTTPException(status_code=400, detail="Access token, old password, and new password are required.")

    try:
        client.change_password(
            PreviousPassword=old_password,
            ProposedPassword=new_password,
            AccessToken=access_token
        )
        return {"message": "Password changed successfully."}
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NotAuthorizedException':
            raise HTTPException(status_code=401, detail="Invalid or expired access token.")
        elif error_code == 'InvalidParameterException':
            raise HTTPException(status_code=400, detail="Invalid password format.")
        elif error_code == 'InvalidPasswordException':
            raise HTTPException(status_code=400, detail="New password does not meet complexity requirements.")
        elif error_code == 'LimitExceededException':
            raise HTTPException(status_code=429, detail="Attempt limit exceeded, please try again later.")
        else:
            logging.error(f"ClientError in change_password: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to change password: {error_code}")
    except BotoCoreError:
        logging.exception("BotoCoreError in change_password")
        raise HTTPException(status_code=500, detail="Internal server error.")
    except Exception as e:
        logging.exception("Unknown error in change_password")
        raise HTTPException(status_code=500, detail="Unexpected error changing password.")

def resend_confirmation_code(email: str) -> dict:
    """
    Resend signup confirmation code for the user.

    Args:
        email (str): User email.

    Returns:
        dict: Success message.

    Raises:
        HTTPException: For any error condition.
    """
    if not email:
        raise HTTPException(status_code=400, detail="Email is required.")

    try:
        user = client.admin_get_user(UserPoolId=COGNITO_USER_POOL_ID, Username=email)
        if user.get("UserStatus") == "CONFIRMED":
            raise HTTPException(status_code=400, detail="User is already confirmed.")

        client.resend_confirmation_code(
            ClientId=COGNITO_CLIENT_ID,
            SecretHash=get_secret_hash(email),
            Username=email
        )
        return {"message": "Confirmation code resent successfully."}
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'UserNotFoundException':
            raise HTTPException(status_code=404, detail="User not found.")
        elif error_code == 'InvalidParameterException':
            raise HTTPException(status_code=400, detail="Invalid email format.")
        else:
            logging.error(f"ClientError in resend_confirmation_code: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to resend confirmation code: {error_code}")
    except BotoCoreError:
        logging.exception("BotoCoreError in resend_confirmation_code")
        raise HTTPException(status_code=500, detail="Internal server error.")
    except Exception as e:
        logging.exception("Unknown error in resend_confirmation_code")
        raise HTTPException(status_code=500, detail="Unexpected error resending confirmation code.")

