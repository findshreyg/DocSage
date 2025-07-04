# Import necessary modules for cryptographic operations, environment variable loading, and logging
import hmac
import hashlib
import base64
import os
from fastapi import Request, HTTPException, status
from dotenv import load_dotenv
import logging

# Load environment variables from a .env file
load_dotenv()

# Retrieve Cognito client ID and secret from environment variables
COGNITO_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")
COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")

# Function to generate a secret hash using HMAC and SHA-256
def get_secret_hash(username: str) -> str:
    message = username + COGNITO_CLIENT_ID
    dig = hmac.new(
        COGNITO_CLIENT_SECRET.encode(),
        msg=message.encode(),
        digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()

# Set up logging for the module
logger = logging.getLogger(__name__)

# Function to extract the access token from the request headers
def get_access_token(request: Request):
    token = request.headers.get("Authorization")
    logger.debug(f"Authorization header: {token}")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token missing",
        )
    # Assuming the token is in the format "Bearer <token>"
    extracted_token = token.split(" ")[1]
    logger.debug(f"Extracted token: {extracted_token}")
    return extracted_token
