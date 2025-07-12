import os
import boto3
from dotenv import  load_dotenv
from fastapi import HTTPException

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
client = boto3.client("cognito-idp", region_name=AWS_REGION)

def get_user_from_token(access_token: str):
    """
    Retrieve user details from AWS Cognito using an access token.

    This helper function checks that the token is present,
    validates it against Cognito, and returns the user attributes
    if the token is valid.

    Args:
        access_token (str): A valid Cognito access token.

    Raises:
        HTTPException: If the token is missing or Cognito returns an error.

    Returns:
        dict: The user's Cognito attributes and metadata.
    """
    # Ensure the access token is provided
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token missing.")
    try:
        # Call AWS Cognito to validate token and fetch user attributes
        response = client.get_user(AccessToken=access_token)
        return response
    except Exception as e:
        # Raise unauthorized if token is invalid or expired
        raise HTTPException(status_code=401, detail="Invalid or expired access token.")