# Import necessary modules for cryptographic operations, environment variable loading, and logging
import os
from fastapi import HTTPException
import boto3
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Retrieve Cognito client ID and secret from environment variables
COGNITO_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")
COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")
AWS_REGION = os.getenv("AWS_REGION")

def get_user_from_token(access_token: str):
    """
    Retrieve user details directly from Cognito using a provided access token.

    This function validates the token and fetches the user's profile from AWS Cognito.

    Args:
        access_token (str): A valid AWS Cognito access token.

    Raises:
        HTTPException: If the token is missing, invalid, or expired.

    Returns:
        dict: User attributes and details returned by Cognito.
    """
    import logging
    logger = logging.getLogger(__name__)

    if not access_token:
        # Access token was not provided
        raise HTTPException(status_code=401, detail="Access token missing.")
    try:
        # Create a Cognito IDP client for the specified AWS region
        client = boto3.client("cognito-idp", region_name=AWS_REGION)

        # Call AWS Cognito to get the user's attributes for this token
        response = client.get_user(AccessToken=access_token)
        return response

    except Exception as e:
        # Log the real AWS exception to help debugging in container logs
        logger.error(f"Failed to get user from token: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid or expired access token.")
