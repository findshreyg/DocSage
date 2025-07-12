# Import necessary modules for cryptographic operations, environment variable loading, and logging
import hmac
import hashlib
import base64
import os
from fastapi import Request, HTTPException, status
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Retrieve Cognito client ID and secret from environment variables
COGNITO_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")
COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")

def get_secret_hash(username: str) -> str:
    """
    Generate a secret hash using the Cognito app client ID and secret.

    This hash is used when signing up or signing in a user with AWS Cognito
    to securely verify the request.

    Args:
        username (str): The username or email of the Cognito user.

    Returns:
        str: The base64-encoded HMAC-SHA256 hash string.
    """
    # Concatenate username and client ID to form the message
    message = username + COGNITO_CLIENT_ID

    # Create HMAC using the client secret and SHA-256
    dig = hmac.new(
        COGNITO_CLIENT_SECRET.encode(),
        msg=message.encode(),
        digestmod=hashlib.sha256
    ).digest()

    # Encode the binary digest to a base64 string
    return base64.b64encode(dig).decode()


def get_access_token(request: Request):
    """
    Extract the access token from the Authorization header in the request.

    This token is used to authenticate the user in protected routes.

    Args:
        request (Request): The incoming FastAPI request object.

    Raises:
        HTTPException: If the Authorization header is missing or invalid.

    Returns:
        str: The extracted raw access token string.
    """
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token missing",
        )
    # Split the header to get the token part from 'Bearer <token>'
    extracted_token = token.split(" ")[1]
    return extracted_token
