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

def sign_up(email: str, password: str, name: str) -> dict:
    """
    Register new user with Cognito.

    Args:
        email (str): Email address.
        password (str): Password.
        name (str): User's full name.

    Returns:
        dict: Confirmation message.

    Raises:
        HTTPException: For AWS or validation errors.
    """
    if not email or not password or not name:
        raise HTTPException(status_code=400, detail="Email, password, and name are required.")

    try:
        client.sign_up(
            ClientId=COGNITO_CLIENT_ID,
            SecretHash=get_secret_hash(email),
            Username=email,
            Password=password,
            UserAttributes=[
                {"Name": "name", "Value": name},
                {"Name": "email", "Value": email}
            ]
        )
        return {"message": f"User account created for {email}."}
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'UsernameExistsException':
            raise HTTPException(status_code=409, detail="Email already exists.")
        elif error_code == 'InvalidPasswordException':
            raise HTTPException(status_code=400, detail="Password does not meet requirements.")
        elif error_code == 'InvalidParameterException':
            raise HTTPException(status_code=400, detail="Invalid parameters. Check email or name format.")
        else:
            logging.error(f"ClientError in sign_up: {e}")
            raise HTTPException(status_code=400, detail="Sign up failed. Please try again.")
    except BotoCoreError:
        logging.exception("BotoCoreError in sign_up")
        raise HTTPException(status_code=500, detail="Internal server error.")
    except Exception as e:
        logging.exception("Unknown error in sign_up")
        raise HTTPException(status_code=500, detail="Unexpected error during signup.")

def login(email: str, password: str) -> dict:
    """
    Authenticate user against Cognito.

    Args:
        email (str): Email address.
        password (str): Password.

    Returns:
        dict: Tokens and basic user info.

    Raises:
        HTTPException: For login or AWS errors.
    """
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required.")

    try:
        auth_response = client.initiate_auth(
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': password,
                'SECRET_HASH': get_secret_hash(email)
            }
        )
        tokens = auth_response['AuthenticationResult']
        user_response = client.admin_get_user(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=email
        )
        name_attr = next(
            (attr['Value'] for attr in user_response['UserAttributes'] if attr['Name'] == 'name'),
            None
        )
        return {
            "access_token": tokens.get("AccessToken"),
            "id_token": tokens.get("IdToken"),
            "refresh_token": tokens.get("RefreshToken"),
            "name": name_attr,
            "email": email
        }
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NotAuthorizedException':
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        elif error_code == 'UserNotFoundException':
            raise HTTPException(status_code=404, detail="User does not exist.")
        elif error_code == 'PasswordResetRequiredException':
            raise HTTPException(status_code=403, detail="Password reset required. Please reset your password.")
        else:
            logging.error(f"ClientError in login: {e}")
            raise HTTPException(status_code=400, detail="Login failed. Please try again.")
    except BotoCoreError:
        logging.exception("BotoCoreError in login")
        raise HTTPException(status_code=500, detail="Internal server error.")
    except Exception as e:
        logging.exception("Unknown error in login")
        raise HTTPException(status_code=500, detail="Unexpected error during login.")

def refresh_token(email: str, refresh_token: str) -> dict:
    """
    Refresh JWT tokens using Cognito.

    Args:
        email (str): User's email.
        refresh_token (str): Refresh token.

    Returns:
        dict: New tokens.

    Raises:
        HTTPException: For errors.
    """
    if not email or not refresh_token:
        raise HTTPException(status_code=400, detail="Email and refresh token required.")

    try:
        response = client.initiate_auth(
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow='REFRESH_TOKEN_AUTH',
            AuthParameters={
                'REFRESH_TOKEN': refresh_token,
                'SECRET_HASH': get_secret_hash(email)
            }
        )
        if 'AuthenticationResult' not in response:
            raise HTTPException(status_code=400, detail="Failed to refresh token, response invalid.")
        result = response["AuthenticationResult"]
        return {
            "access_token": result.get("AccessToken"),
            "id_token": result.get("IdToken"),
            "refresh_token": result.get("RefreshToken")
        }
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NotAuthorizedException':
            raise HTTPException(status_code=401, detail="Invalid refresh token.")
        else:
            logging.error(f"ClientError in refresh_token: {e}")
            raise HTTPException(status_code=400, detail="Token refresh failed. Please try again.")
    except BotoCoreError:
        logging.exception("BotoCoreError in refresh_token")
        raise HTTPException(status_code=500, detail="Internal server error.")
    except Exception as e:
        logging.exception("Unknown error in refresh_token")
        raise HTTPException(status_code=500, detail="Unexpected error refreshing token.")

def logout(access_token: str) -> dict:
    """
    Log the user out globally by invalidating tokens.

    Args:
        access_token (str): Cognito access token.

    Returns:
        dict: Message on success.

    Raises:
        HTTPException: For AWS errors.
    """
    if not access_token:
        raise HTTPException(status_code=400, detail="Access token required for logout.")

    try:
        client.global_sign_out(AccessToken=access_token)
        return {"message": "Account Logged Out"}
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NotAuthorizedException':
            raise HTTPException(status_code=401, detail="Invalid or expired token.")
        else:
            logging.error(f"ClientError in logout: {e}")
            raise HTTPException(status_code=400, detail="Logout failed. Please try again.")
    except BotoCoreError:
        logging.exception("BotoCoreError in logout")
        raise HTTPException(status_code=500, detail="Internal server error.")
    except Exception as e:
        logging.exception("Unknown error in logout")
        raise HTTPException(status_code=500, detail="Unexpected error during logout.")