# Core authentication module - handles user signup, login, logout, and token refresh
# This module interfaces with AWS Cognito Identity Provider for user management

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
# These are required for connecting to the specific Cognito User Pool
AWS_REGION = os.getenv("AWS_REGION")  # AWS region where Cognito is deployed
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")  # Unique identifier for user pool
COGNITO_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")  # App client ID for API access
COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")  # Secret key for secure operations

# Validate that all required configuration is present
# Without these, the service cannot function properly
if not all([AWS_REGION, COGNITO_USER_POOL_ID, COGNITO_CLIENT_ID, COGNITO_CLIENT_SECRET]):
    raise HTTPException(status_code=500, detail="Server configuration error.")

# Initialize AWS Cognito Identity Provider client
# This client handles all communication with AWS Cognito service
try:
    client = boto3.client("cognito-idp", region_name=AWS_REGION)
except Exception as e:
    # If we can't connect to AWS, the service is non-functional
    logging.exception("Failed to initialize Cognito client")
    raise HTTPException(status_code=500, detail="Internal server error.")

def sign_up(email: str, password: str, name: str) -> dict:
    """
    Create a new user account in AWS Cognito.
    
    This function:
    1. Validates input parameters are provided
    2. Creates user in Cognito with email as username
    3. Sets user attributes (name and email)
    4. Triggers email confirmation process
    5. Returns success message
    
    The user will receive a confirmation email and must verify before they can log in.
    """
    # Input validation - ensure all required fields are provided
    if not email or not password or not name:
        raise HTTPException(status_code=400, detail="Email, password, and name are required.")

    try:
        # Create user account in Cognito
        client.sign_up(
            ClientId=COGNITO_CLIENT_ID,  # Identifies which app is making the request
            SecretHash=get_secret_hash(email),  # HMAC hash for additional security
            Username=email,  # Use email as the username
            Password=password,  # User's chosen password
            UserAttributes=[  # Additional user profile information
                {"Name": "name", "Value": name},  # User's display name
                {"Name": "email", "Value": email}  # Email attribute (required for verification)
            ]
        )
        return {"message": f"User account created for {email}."}
    
    except ClientError as e:
        # Handle specific AWS Cognito errors with appropriate HTTP responses
        error_code = e.response['Error']['Code']
        if error_code == 'UsernameExistsException':
            # User already exists - return 409 Conflict
            raise HTTPException(status_code=409, detail="Email already exists.")
        elif error_code == 'InvalidPasswordException':
            # Password doesn't meet Cognito password policy
            raise HTTPException(status_code=400, detail="Password does not meet requirements.")
        elif error_code == 'InvalidParameterException':
            # Invalid email format or other parameter issues
            raise HTTPException(status_code=400, detail="Invalid parameters. Check email or name format.")
        else:
            # Other Cognito-specific errors
            logging.error(f"ClientError in sign_up: {e}")
            raise HTTPException(status_code=400, detail="Sign up failed. Please try again.")
    
    except BotoCoreError as e:
        # AWS SDK connection or configuration errors
        logging.exception("BotoCoreError in sign_up")
        raise HTTPException(status_code=500, detail="Internal server error.")
    
    except Exception as e:
        # Catch any other unexpected errors
        logging.exception("Unknown error in sign_up")
        raise HTTPException(status_code=500, detail="Unexpected error during signup.")

def login(email: str, password: str) -> dict:
    """
    Authenticate user credentials and return JWT tokens.
    
    This function:
    1. Validates email and password against Cognito
    2. Generates JWT tokens (access, ID, refresh)
    3. Retrieves user profile information
    4. Returns tokens and user data for client storage
    
    The tokens are used for subsequent API calls to prove user identity.
    """
    # Input validation - both email and password are required
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required.")

    try:
        # Authenticate user with Cognito and get tokens
        auth_response = client.initiate_auth(
            ClientId=COGNITO_CLIENT_ID,  # App client identifier
            AuthFlow='USER_PASSWORD_AUTH',  # Use username/password authentication flow
            AuthParameters={
                'USERNAME': email,  # User's email address
                'PASSWORD': password,  # User's password
                'SECRET_HASH': get_secret_hash(email)  # Security hash for client secret
            }
        )
        
        # Extract tokens from authentication response
        tokens = auth_response['AuthenticationResult']
        
        # Get additional user profile information from Cognito
        user_response = client.admin_get_user(
            UserPoolId=COGNITO_USER_POOL_ID,  # Which user pool to query
            Username=email  # User to retrieve information for
        )
        
        # Extract the user's display name from their attributes
        name_attr = next(
            (attr['Value'] for attr in user_response['UserAttributes'] if attr['Name'] == 'name'),
            None  # Default to None if name attribute not found
        )
        
        # Return all authentication data needed by the client
        return {
            "access_token": tokens.get("AccessToken"),  # For API authorization
            "id_token": tokens.get("IdToken"),  # Contains user identity claims
            "refresh_token": tokens.get("RefreshToken"),  # For token renewal
            "name": name_attr,  # User's display name
            "email": email  # User's email address
        }
    
    except ClientError as e:
        # Handle specific authentication errors
        error_code = e.response['Error']['Code']
        if error_code == 'NotAuthorizedException':
            # Wrong email or password
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        elif error_code == 'UserNotFoundException':
            # User account doesn't exist
            raise HTTPException(status_code=404, detail="User does not exist.")
        elif error_code == 'PasswordResetRequiredException':
            # User must reset password before logging in
            raise HTTPException(status_code=403, detail="Password reset required. Please reset your password.")
        else:
            # Other Cognito authentication errors
            logging.error(f"ClientError in login: {e}")
            raise HTTPException(status_code=400, detail="Login failed. Please try again.")
    
    except BotoCoreError as e:
        # AWS SDK or connection errors
        logging.exception("BotoCoreError in login")
        raise HTTPException(status_code=500, detail="Internal server error.")
    
    except Exception as e:
        # Any other unexpected errors
        logging.exception("Unknown error in login")
        raise HTTPException(status_code=500, detail="Unexpected error during login.")

def refresh_token(email: str, refresh_token: str) -> dict:
    """
    Generate new access and ID tokens using a refresh token.
    
    This function:
    1. Validates the refresh token with Cognito
    2. Generates new access token and ID token
    3. May return a new refresh token (token rotation)
    4. Allows users to stay authenticated without re-entering credentials
    
    Refresh tokens have longer expiration times than access tokens.
    """
    # Input validation - both email and refresh token are required
    if not email or not refresh_token:
        raise HTTPException(status_code=400, detail="Email and refresh token required.")

    try:
        # Use refresh token to get new access tokens from Cognito
        response = client.initiate_auth(
            ClientId=COGNITO_CLIENT_ID,  # App client identifier
            AuthFlow='REFRESH_TOKEN_AUTH',  # Use refresh token authentication flow
            AuthParameters={
                'REFRESH_TOKEN': refresh_token,  # The refresh token to exchange
                'SECRET_HASH': get_secret_hash(email)  # Security hash for verification
            }
        )
        
        # Validate that Cognito returned authentication tokens
        if 'AuthenticationResult' not in response:
            raise HTTPException(status_code=400, detail="Failed to refresh token, response invalid.")
        
        # Extract new tokens from response
        result = response["AuthenticationResult"]
        return {
            "access_token": result.get("AccessToken"),  # New access token for API calls
            "id_token": result.get("IdToken"),  # New ID token with user claims
            "refresh_token": result.get("RefreshToken")  # May be new refresh token or same one
        }
    
    except ClientError as e:
        # Handle Cognito-specific errors
        error_code = e.response['Error']['Code']
        if error_code == 'NotAuthorizedException':
            # Refresh token is invalid or expired
            raise HTTPException(status_code=401, detail="Invalid refresh token.")
        else:
            # Other Cognito errors
            logging.error(f"ClientError in refresh_token: {e}")
            raise HTTPException(status_code=400, detail="Token refresh failed. Please try again.")
    
    except BotoCoreError as e:
        # AWS SDK or connection errors
        logging.exception("BotoCoreError in refresh_token")
        raise HTTPException(status_code=500, detail="Internal server error.")
    
    except Exception as e:
        # Any other unexpected errors
        logging.exception("Unknown error in refresh_token")
        raise HTTPException(status_code=500, detail="Unexpected error refreshing token.")

def logout(access_token: str) -> dict:
    """
    Log out user by invalidating all their tokens globally.
    
    This function:
    1. Validates the access token
    2. Performs global sign-out in Cognito
    3. Invalidates all user sessions across all devices
    4. User must log in again to access protected resources
    
    This is more secure than just deleting tokens client-side.
    """
    # Input validation - access token is required for logout
    if not access_token:
        raise HTTPException(status_code=400, detail="Access token required for logout.")

    try:
        # Perform global logout in Cognito - invalidates all user sessions
        client.global_sign_out(AccessToken=access_token)
        return {"message": "Account Logged Out"}
    
    except ClientError as e:
        # Handle Cognito-specific errors
        error_code = e.response['Error']['Code']
        if error_code == 'NotAuthorizedException':
            # Access token is invalid or expired
            raise HTTPException(status_code=401, detail="Invalid or expired token.")
        else:
            # Other Cognito errors
            logging.error(f"ClientError in logout: {e}")
            raise HTTPException(status_code=400, detail="Logout failed. Please try again.")
    
    except BotoCoreError as e:
        # AWS SDK or connection errors
        logging.exception("BotoCoreError in logout")
        raise HTTPException(status_code=500, detail="Internal server error.")
    
    except Exception as e:
        # Any other unexpected errors
        logging.exception("Unknown error in logout")
        raise HTTPException(status_code=500, detail="Unexpected error during logout.")