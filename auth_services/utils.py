# Utility functions for authentication service
# This module provides helper functions for token handling and security operations

import hmac  # HMAC (Hash-based Message Authentication Code) for secure hashing
import hashlib  # Hash algorithms (SHA-256)
import base64  # Base64 encoding for token formatting
import os  # Access environment variables
from fastapi import Request, HTTPException, status  # FastAPI request handling and HTTP responses
from dotenv import load_dotenv  # Load environment variables from .env file

# Load environment variables from .env file
load_dotenv()

# Retrieve Cognito client credentials from environment variables
# These are required for generating secure hashes for Cognito operations
COGNITO_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")  # App client identifier
COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")  # Secret key for security operations

# Validate that required credentials are present
# Without these, secure Cognito operations cannot be performed
if not COGNITO_CLIENT_ID or not COGNITO_CLIENT_SECRET:
    raise RuntimeError("Missing Cognito client credentials. Update your environment variables.")

def get_secret_hash(username: str) -> str:
    """
    Generate a base64-encoded HMAC-SHA256 hash for AWS Cognito operations.
    
    This function:
    1. Combines username with client ID to create a message
    2. Uses HMAC-SHA256 with client secret as the key
    3. Encodes the result in base64 format
    4. Returns the hash for Cognito API calls
    
    AWS Cognito requires this hash for additional security when client secret is configured.
    The hash proves that the request is coming from a legitimate client application.
    """
    # Input validation - username is required for hash generation
    if not username:
        raise ValueError("Username required for secret hash generation.")
    
    # Create message by concatenating username and client ID
    # This ensures the hash is unique for each user and client combination
    message = username + COGNITO_CLIENT_ID
    
    # Generate HMAC-SHA256 hash using client secret as the key
    dig = hmac.new(
        COGNITO_CLIENT_SECRET.encode(),  # Secret key (must be bytes)
        msg=message.encode(),  # Message to hash (must be bytes)
        digestmod=hashlib.sha256  # Use SHA-256 hash algorithm
    ).digest()
    
    # Encode the hash in base64 format as required by Cognito
    return base64.b64encode(dig).decode()

def get_access_token(request: Request) -> str:
    """
    Extract and validate Bearer access token from HTTP Authorization header.
    
    This function:
    1. Retrieves Authorization header from the request
    2. Validates the header format (must be "Bearer <token>")
    3. Extracts and returns the token portion
    4. Raises HTTP 401 error if token is missing or invalid format
    
    Used as a FastAPI dependency to automatically extract tokens from requests.
    The token is then used to authenticate users with AWS Cognito.
    """
    # Extract Authorization header from the HTTP request
    token = request.headers.get("Authorization")
    
    # Check if Authorization header is present
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token missing"
        )
    
    # Split header into parts (should be "Bearer" and the actual token)
    parts = token.split(" ")
    
    # Validate header format: must have exactly 2 parts and start with "Bearer"
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format"
        )
    
    # Return the token portion (second part after "Bearer")
    return parts[1]

