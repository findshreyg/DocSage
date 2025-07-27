import os
import boto3
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")

if not AWS_REGION or not COGNITO_USER_POOL_ID:
    raise RuntimeError("Missing AWS_REGION or COGNITO_USER_POOL_ID in environment.")

client = boto3.client("cognito-idp", region_name=AWS_REGION)

def get_user_from_token(access_token: str) -> dict:
    """
    Retrieve user details from AWS Cognito using an access token.
    Args:
        access_token (str): Cognito access token.
    Raises:
        HTTPException: If token is missing, invalid, or expired.
    Returns:
        dict: User properties/attributes.
    """
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token missing.")
    try:
        response = client.get_user(AccessToken=access_token)
        return response
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired access token.")
