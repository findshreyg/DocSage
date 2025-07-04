# Import necessary libraries for AWS Cognito and environment management
import boto3
import os
import logging
from fastapi import HTTPException
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from utils import get_secret_hash

# Load environment variables from a .env file
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# Retrieve AWS and Cognito configuration from environment variables
AWS_REGION = os.getenv("AWS_REGION")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")
COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")

if not all([AWS_REGION, COGNITO_USER_POOL_ID, COGNITO_CLIENT_ID, COGNITO_CLIENT_SECRET]):
    logger.error("One or more environment variables are missing.")
    raise HTTPException(status_code=500, detail="Server configuration error.")

# Initialize the Cognito client
try:
    client = boto3.client("cognito-idp", region_name=AWS_REGION)
except Exception as e:
    logger.exception("Failed to initialize Boto3 client.")
    raise HTTPException(status_code=500, detail="Internal server error.")

def sign_up(email: str, password: str, name: str):
    if not email or not password or not name:
        raise HTTPException(status_code=400, detail="Email, password, and name are required.")
    try:
        response = client.sign_up(
            ClientId=COGNITO_CLIENT_ID,
            SecretHash=get_secret_hash(email),
            Username=email,
            Password=password,
            UserAttributes=[
                {"Name": "name", "Value": name},
                {"Name": "email", "Value": email}
            ]
        )
        logger.info(f"User sign up initiated for {email} with name {name}. Cognito response: {response}")

    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.exception(f"SignUp failed for {email}: {error_code} - {e}")

        if error_code == 'UsernameExistsException':
            raise HTTPException(status_code=409, detail="Email already exists.")
        elif error_code == 'InvalidPasswordException':
            raise HTTPException(status_code=400, detail="Password does not meet requirements.")
        elif error_code == 'InvalidParameterException':
            raise HTTPException(status_code=400, detail="Invalid parameters. Check email or name format.")
        else:
            raise HTTPException(status_code=400, detail="Sign up failed. Please try again.")

    return {"message": f"User account created for {email}."}

def login(email: str, password: str):
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required.")

    try:
        # 1️⃣ Authenticate user
        auth_response = client.initiate_auth(
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': password,
                'SECRET_HASH': get_secret_hash(email)
            }
        )

        id_token = auth_response['AuthenticationResult']['IdToken']
        access_token = auth_response['AuthenticationResult']['AccessToken']
        refresh_token = auth_response['AuthenticationResult']['RefreshToken']

        user_response = client.admin_get_user(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=email
        )

        name_attr = next(
            (attr['Value'] for attr in user_response['UserAttributes'] if attr['Name'] == 'name'),
            None
        )

        logger.info(f"User {email} logged in successfully with name: {name_attr}")

        return {
            "access_token": access_token,
            "id_token": id_token,
            "refresh_token": refresh_token,
            "name": name_attr,
            "email": email
        }

    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.exception(f"Login failed for {email}: {error_code} - {e}")

        if error_code == 'NotAuthorizedException':
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        elif error_code == 'UserNotFoundException':
            raise HTTPException(status_code=404, detail="User does not exist.")
        elif error_code == 'PasswordResetRequiredException':
            raise HTTPException(status_code=403, detail="Password reset required. Please reset your password.")
        else:
            raise HTTPException(status_code=400, detail="Login failed. Please try again.")

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
        error_code = e.response['Error']['Code']
        logger.exception(f"Refresh token failed: {e}")
        if error_code == 'NotAuthorizedException':
            raise HTTPException(401, "Invalid refresh token.")
        else:
            raise HTTPException(400, "Token refresh failed. Please try again.")


def logout(access_token: str):
    if not access_token:
        raise HTTPException(status_code=400, detail="Access token required for logout.")
    try:
        client.global_sign_out(
            AccessToken=access_token
        )
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.exception(f"Logout failed: {e}")
        if error_code == 'NotAuthorizedException':
            raise HTTPException(401, "Invalid or expired token.")
        else:
            raise HTTPException(400, "Logout failed. Please try again.")
    return {"message": "Account Logged Out"}
