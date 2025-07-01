from fastapi import HTTPException, Depends
from jose import jwt
from jose.exceptions import JWTError
import requests
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
import os
from functools import lru_cache

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

load_dotenv()
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_APP_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")
COGNITO_REGION = os.getenv("COGNITO_REGION")

JWKS_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json"

@lru_cache()
def get_jwks():
    return requests.get(JWKS_URL).json()


def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Validates and decodes a JWT token from the Authorization header.
    Returns the decoded payload if valid.
    Raises HTTPException with 401 status if invalid.
    """
    # Explicit check for missing or empty token
    if not token:
        raise HTTPException(status_code=401, detail="Authorization token is missing.")

    # Attempt to get the JWT unverified header, handle malformed token
    try:
        jwks = get_jwks()
        unverified_header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token header. Token may be malformed.")

    # Find the public key with matching kid
    public_key = None
    for key in jwks["keys"]:
        if key.get("kid") == unverified_header.get("kid"):
            public_key = key
            break

    if public_key is None:
        raise HTTPException(status_code=401, detail="Public key not found. Token signature cannot be verified.")

    # Attempt to decode and validate the JWT token
    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=COGNITO_APP_CLIENT_ID,
            issuer=f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Token is invalid or has expired.")

    # Attach raw token for downstream use
    payload["token"] = token
    return payload