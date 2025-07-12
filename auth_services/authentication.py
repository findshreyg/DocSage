# Import necessary libraries for AWS Cognito and environment management
import boto3
import os
from fastapi import HTTPException
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from utils import get_secret_hash

# Load environment variables from a .env file
load_dotenv()

# Retrieve AWS and Cognito configuration from environment variables
AWS_REGION = os.getenv("AWS_REGION")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")
COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")

# Validate configuration
if not all([AWS_REGION, COGNITO_USER_POOL_ID, COGNITO_CLIENT_ID, COGNITO_CLIENT_SECRET]):
    raise HTTPException(status_code=500, detail="Server configuration error.")

# Initialize the Cognito client
try:
    client = boto3.client("cognito-idp", region_name=AWS_REGION)
except Exception as e:
    raise HTTPException(status_code=500, detail="Internal server error.")

# Function to sign up a new user
def sign_up(email: str, password: str, name: str):
    """
    Sign up a new user in the Cognito User Pool.

    Args:
        email (str): User's email address.
        password (str): User's password.
        name (str): User's full name.

    Raises:
        HTTPException: If required fields are missing or Cognito returns an error.

    Returns:
        dict: Success message with the created email.
    """
    if not email or not password or not name:
        raise HTTPException(status_code=400, detail="Email, password, and name are required.")
    try:
        # Call Cognito's sign up API with email, password, and name
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
    except ClientError as e:
        error_code = e.response['Error']['Code']
        # Handle common signup errors gracefully
        if error_code == 'UsernameExistsException':
            raise HTTPException(status_code=409, detail="Email already exists.")
        elif error_code == 'InvalidPasswordException':
            raise HTTPException(status_code=400, detail="Password does not meet requirements.")
        elif error_code == 'InvalidParameterException':
            raise HTTPException(status_code=400, detail="Invalid parameters. Check email or name format.")
        else:
            raise HTTPException(status_code=400, detail="Sign up failed. Please try again.")
    return {"message": f"User account created for {email}."}

# Function to log in an existing user
def login(email: str, password: str):
    """
    Authenticate a user and retrieve tokens.

    Args:
        email (str): User's email address.
        password (str): User's password.

    Raises:
        HTTPException: If authentication fails or input is invalid.

    Returns:
        dict: Tokens (ID, access, refresh) and user profile info.
    """
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required.")
    try:
        # Call Cognito to initiate the authentication flow
        auth_response = client.initiate_auth(
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': password,
                'SECRET_HASH': get_secret_hash(email)
            }
        )

        # Extract returned JWT tokens
        id_token = auth_response['AuthenticationResult']['IdToken']
        access_token = auth_response['AuthenticationResult']['AccessToken']
        refresh_token = auth_response['AuthenticationResult']['RefreshToken']

        # Get user attributes to retrieve the 'name'
        user_response = client.admin_get_user(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=email
        )

        # Extract the 'name' field from user attributes
        name_attr = next(
            (attr['Value'] for attr in user_response['UserAttributes'] if attr['Name'] == 'name'),
            None
        )

        return {
            "access_token": access_token,
            "id_token": id_token,
            "refresh_token": refresh_token,
            "name": name_attr,
            "email": email
        }
    except ClientError as e:
        error_code = e.response['Error']['Code']
        # Handle authentication-specific errors
        if error_code == 'NotAuthorizedException':
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        elif error_code == 'UserNotFoundException':
            raise HTTPException(status_code=404, detail="User does not exist.")
        elif error_code == 'PasswordResetRequiredException':
            raise HTTPException(status_code=403, detail="Password reset required. Please reset your password.")
        else:
            raise HTTPException(status_code=400, detail="Login failed. Please try again.")

# Function to refresh tokens for an existing user session
def refresh_token(email: str, refresh_token: str):
    """
    Refresh authentication tokens using a valid refresh token.

    Args:
        email (str): User's email address.
        refresh_token (str): Valid refresh token.

    Raises:
        HTTPException: If refresh fails or input is invalid.

    Returns:
        dict: New authentication tokens.
    """
    if not email or not refresh_token:
        raise HTTPException(400, "Email and refresh token required.")
    try:
        # Call Cognito's refresh token API to get new tokens
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
        if error_code == 'NotAuthorizedException':
            raise HTTPException(401, "Invalid refresh token.")
        else:
            raise HTTPException(400, "Token refresh failed. Please try again.")

# Function to sign out a user globally from all devices
def logout(access_token: str):
    """
    Perform a global sign-out for the user, invalidating all active sessions.

    Args:
        access_token (str): User's valid access token.

    Raises:
        HTTPException: If logout fails or token is invalid.

    Returns:
        dict: Success message.
    """
    if not access_token:
        raise HTTPException(status_code=400, detail="Access token required for logout.")
    try:
        # Use Cognito's global sign-out to invalidate all sessions
        client.global_sign_out(
            AccessToken=access_token
        )
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NotAuthorizedException':
            raise HTTPException(401, "Invalid or expired token.")
        else:
            raise HTTPException(400, "Logout failed. Please try again.")
    return {"message": "Account Logged Out"}
