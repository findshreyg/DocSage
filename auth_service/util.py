import hmac
import hashlib
import base64
from dotenv import load_dotenv
import os

load_dotenv()
COGNITO_APP_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")
COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")

def get_secret_hash(username: str) -> str:
    """
    Generate a Cognito secret hash for secure client authentication.

    Args:
        username (str): The Cognito username.

    Returns:
        str: The base64-encoded HMAC-SHA256 hash.

    Raises:
        ValueError: If required environment variables are missing.
    """
    if not COGNITO_APP_CLIENT_ID or not COGNITO_CLIENT_SECRET:
        raise ValueError("Missing COGNITO_APP_CLIENT_ID or COGNITO_CLIENT_SECRET environment variable.")

    message = username + COGNITO_APP_CLIENT_ID
    dig = hmac.new(
        COGNITO_CLIENT_SECRET.encode('utf-8'),
        msg=message.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()