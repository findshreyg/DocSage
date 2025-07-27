from fastapi import FastAPI, Depends, HTTPException, status, Request
import logging

import authentication
import password_management
import user_management

from utils import get_access_token
from fastapi.middleware.cors import CORSMiddleware
from schemas import (
    SignupRequest, LoginRequest, RefreshRequest, ConfirmSignUpRequest,
    ResendRequest, ForgotPasswordRequest, ChangePasswordRequest, ConfirmForgotPasswordRequest
)

app = FastAPI()
logging.basicConfig(level=logging.INFO)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/auth/health")
def health():
    """Health check endpoint."""
    return {"health": "All Good"}

@app.post("/auth/signup", status_code=status.HTTP_201_CREATED)
def sign_up(payload: SignupRequest):
    """
    Register a new user in Cognito.
    """
    try:
        return authentication.sign_up(payload.email, payload.password, payload.name)
    except HTTPException as e:
        raise e
    except Exception:
        logging.exception("Unexpected error during signup.")
        raise HTTPException(status_code=500, detail="Unexpected error during signup.")

@app.post("/auth/login")
def login(payload: LoginRequest):
    """
    Authenticate a user and return JWT tokens.
    """
    try:
        return authentication.login(payload.email, payload.password)
    except HTTPException as e:
        raise e
    except Exception:
        logging.exception("Unexpected error during login.")
        raise HTTPException(status_code=500, detail="Unexpected error during login.")

@app.post("/auth/refresh-token")
def refresh_token(payload: RefreshRequest):
    """
    Refresh authentication tokens using a refresh token.
    """
    try:
        return authentication.refresh_token(payload.email, payload.refresh_token)
    except HTTPException as e:
        raise e
    except Exception:
        logging.exception("Unexpected error refreshing token.")
        raise HTTPException(status_code=500, detail="Unexpected error refreshing token.")

@app.post("/auth/logout")
def logout(access_token: str = Depends(get_access_token)):
    """
    Log the user out (global sign-out).
    """
    try:
        return authentication.logout(access_token)
    except HTTPException as e:
        raise e
    except Exception:
        logging.exception("Unexpected error during logout.")
        raise HTTPException(status_code=500, detail="Unexpected error during logout.")

@app.post("/auth/confirm-signup")
def confirm_sign_up(payload: ConfirmSignUpRequest):
    """
    Confirm a user's signup with a code.
    """
    try:
        return user_management.confirm_sign_up(payload.email, payload.code)
    except HTTPException as e:
        raise e
    except Exception:
        logging.exception("Unexpected error during confirmation.")
        raise HTTPException(status_code=500, detail="Unexpected error during confirmation.")

@app.post("/auth/resend-confirmation-code")
def resend_confirmation_code(payload: ResendRequest):
    """
    Resend the signup confirmation code.
    """
    try:
        return password_management.resend_confirmation_code(payload.email)
    except HTTPException as e:
        raise e
    except Exception:
        logging.exception("Unexpected error resending code.")
        raise HTTPException(status_code=500, detail="Unexpected error resending code.")

@app.post("/auth/forgot-password")
def forgot_password(payload: ForgotPasswordRequest):
    """
    Send a forgot password code to the user.
    """
    try:
        return password_management.forgot_password(payload.email)
    except HTTPException as e:
        raise e
    except Exception:
        logging.exception("Unexpected error sending forgot password code.")
        raise HTTPException(status_code=500, detail="Unexpected error sending forgot password code.")

@app.post("/auth/confirm-forgot-password")
def confirm_forgot_password(payload: ConfirmForgotPasswordRequest):
    """
    Confirm a password reset using code and set a new password.
    """
    try:
        return password_management.confirm_forgot_password(payload.email, payload.code, payload.new_password)
    except HTTPException as e:
        raise e
    except Exception:
        logging.exception("Unexpected error during password reset confirmation.")
        raise HTTPException(status_code=500, detail="Unexpected error during password reset confirmation.")

@app.post("/auth/change-password")
def change_password(payload: ChangePasswordRequest, access_token: str = Depends(get_access_token)):
    """
    Change the user's password.
    """
    try:
        return password_management.change_password(access_token, payload.old_password, payload.new_password)
    except HTTPException as e:
        raise e
    except Exception:
        logging.exception("Unexpected error during password change.")
        raise HTTPException(status_code=500, detail="Unexpected error during password change.")

@app.get("/auth/get-user")
def get_user(access_token: str = Depends(get_access_token)):
    """
    Get the user's details from Cognito.
    """
    try:
        return user_management.get_user(access_token)
    except HTTPException as e:
        raise e
    except Exception:
        logging.exception("Unexpected error retrieving user info.")
        raise HTTPException(status_code=500, detail="Unexpected error retrieving user info.")

@app.delete("/auth/delete-user")
def delete_user(access_token: str = Depends(get_access_token)):
    """
    Delete the user's Cognito account.
    """
    try:
        return user_management.delete_user(access_token)
    except HTTPException as e:
        raise e
    except Exception:
        logging.exception("Unexpected error deleting user.")
        raise HTTPException(status_code=500, detail="Unexpected error deleting user.")
