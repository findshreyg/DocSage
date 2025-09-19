import os
import logging
from fastapi import HTTPException
import boto3
from dotenv import load_dotenv

load_dotenv()

COGNITO_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")
COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")
AWS_REGION = os.getenv("AWS_REGION")

def get_user_from_token(access_token: str) -> dict:
    """
    Retrieve user details directly from Cognito using a provided access token.

    Args:
        access_token (str): AWS Cognito access token.

    Raises:
        HTTPException: If token is missing, invalid, or expired.

    Returns:
        dict: User attributes/claims as returned by Cognito.
    """
    logger = logging.getLogger(__name__)
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token missing.")
    try:
        client = boto3.client("cognito-idp", region_name=AWS_REGION)
        response = client.get_user(AccessToken=access_token)
        return response
    except Exception as e:
        logger.error(f"Failed to get user from token: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid or expired access token.")
