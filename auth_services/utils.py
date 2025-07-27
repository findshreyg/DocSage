import hmac
import hashlib
import base64
import os
from fastapi import Request, HTTPException, status
from dotenv import load_dotenv

load_dotenv()

COGNITO_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")
COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")

if not COGNITO_CLIENT_ID or not COGNITO_CLIENT_SECRET:
    raise RuntimeError("Missing Cognito client credentials. Update your environment variables.")

def get_secret_hash(username: str) -> str:
    """
    Generate a base64-encoded HMAC-SHA256 hash using Cognito client secret.

    Args:
        username (str): Cognito user's username (email).

    Returns:
        str: The base64-encoded secret hash.

    Raises:
        ValueError: If username is missing.
    """
    if not username:
        raise ValueError("Username required for secret hash generation.")
    message = username + COGNITO_CLIENT_ID
    dig = hmac.new(
        COGNITO_CLIENT_SECRET.encode(),
        msg=message.encode(),
        digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()

def get_access_token(request: Request) -> str:
    """
    Extract and validate the Bearer access token from request headers.

    Args:
        request (Request): FastAPI request context.

    Returns:
        str: Access token if valid.

    Raises:
        HTTPException: If missing or improperly formatted Authorization header.
    """
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token missing"
        )
    parts = token.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format"
        )
    return parts[1]

