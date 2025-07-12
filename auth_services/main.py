# Import necessary modules and dependencies for FastAPI application
from fastapi import FastAPI, Depends, HTTPException, status
import authentication
import password_management
import user_management
from utils import get_access_token
from fastapi.middleware.cors import CORSMiddleware
from schemas import (
    SignupRequest,
    LoginRequest,
    RefreshRequest,
    ConfirmSignUpRequest,
    ResendRequest,
    ForgotPasswordRequest,
    ChangePasswordRequest,
    ConfirmForgotPasswordRequest
)

# Initialize the FastAPI application
app = FastAPI()

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint to verify service status
@app.get("/auth/health")
def health():
    """
    Simple health check to verify that the authentication service is up.
    """
    return {"health": "All Good"}

# Endpoint to handle user signup requests
@app.post("/auth/signup", status_code=status.HTTP_201_CREATED)
def sign_up(payload: SignupRequest):
    """
    Register a new user with email, password, and name.

    Args:
        payload (SignupRequest): Contains email, password, and name.

    Returns:
        dict: Success message or error details.
    """
    try:
        return authentication.sign_up(payload.email, payload.password, payload.name)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail="Signup failed. Check email or password format.")

# Endpoint to handle user login requests
@app.post("/auth/login")
def login(payload: LoginRequest):
    """
    Log in a user with email and password.

    Args:
        payload (LoginRequest): Contains email and password.

    Returns:
        dict: Authentication tokens and user info.
    """
    try:
        return authentication.login(payload.email, payload.password)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

# Endpoint to refresh authentication tokens
@app.post("/auth/refresh-token")
def refresh_token(payload: RefreshRequest):
    """
    Refresh a user's tokens using a valid refresh token.

    Args:
        payload (RefreshRequest): Contains email and refresh token.

    Returns:
        dict: New tokens or error details.
    """
    try:
        return authentication.refresh_token(payload.email, payload.refresh_token)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token.")

# Endpoint to handle user logout requests
@app.post("/auth/logout")
def logout(access_token: str = Depends(get_access_token)):
    """
    Log out a user by invalidating their access token.

    Args:
        access_token (str): Bearer token from request header.

    Returns:
        dict: Confirmation message.
    """
    try:
        return authentication.logout(access_token)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=401, detail="Failed to logout. Invalid token.")

# Endpoint to confirm user signup with a code
@app.post("/auth/confirm-signup")
def confirm_sign_up(payload: ConfirmSignUpRequest):
    """
    Confirm a new user's email with a verification code.

    Args:
        payload (ConfirmSignUpRequest): Contains email and code.

    Returns:
        dict: Confirmation result.
    """
    try:
        return user_management.confirm_sign_up(payload.email, payload.code)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail="Failed to confirm sign up. Invalid code or user.")

# Endpoint to resend confirmation code for signup
@app.post("/auth/resend-confirmation-code")
def resend_confirmation_code(payload: ResendRequest):
    """
    Resend the email verification code to the user.

    Args:
        payload (ResendRequest): Contains email.

    Returns:
        dict: Confirmation code resend result.
    """
    try:
        return password_management.resend_confirmation_code(payload.email)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail="Failed to resend confirmation code.")

# Endpoint to handle forgot password requests
@app.post("/auth/forgot-password")
def forgot_password(payload: ForgotPasswordRequest):
    """
    Start the forgot password flow by sending a code.

    Args:
        payload (ForgotPasswordRequest): Contains email.

    Returns:
        dict: Forgot password code sent status.
    """
    try:
        return password_management.forgot_password(payload.email)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail="Failed to send forgot password code.")

# Endpoint to confirm forgot password with a code and set a new password
@app.post("/auth/confirm-forgot-password")
def confirm_forgot_password(payload: ConfirmForgotPasswordRequest):
    """
    Confirm forgot password with the received code and set new password.

    Args:
        payload (ConfirmForgotPasswordRequest): Contains email, code, and new password.

    Returns:
        dict: Password reset result.
    """
    try:
        return password_management.confirm_forgot_password(payload.email, payload.code, payload.new_password)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail="Failed to confirm forgot password. Check code and password format.")

# Endpoint to change user password
@app.post("/auth/change-password")
def change_password(payload: ChangePasswordRequest, access_token: str = Depends(get_access_token)):
    """
    Change the current password using valid credentials.

    Args:
        payload (ChangePasswordRequest): Contains old and new passwords.
        access_token (str): Bearer token for authentication.

    Returns:
        dict: Password change status.
    """
    try:
        return password_management.change_password(access_token, payload.old_password, payload.new_password)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail="Failed to change password. Check current or new password.")

# Endpoint to retrieve user information
@app.get("/auth/get-user")
def get_user(access_token: str = Depends(get_access_token)):
    """
    Get the current authenticated user's details.

    Args:
        access_token (str): Bearer token.

    Returns:
        dict: User information.
    """
    try:
        return user_management.get_user(access_token)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=401, detail="Failed to retrieve user. Invalid or expired token.")

# Endpoint to delete a user and their related data
@app.delete("/auth/delete-user")
def delete_user(access_token: str = Depends(get_access_token)):
    """
    Delete the authenticated user and related data.

    Args:
        access_token (str): Bearer token.

    Returns:
        dict: Deletion result.
    """
    try:
        return user_management.delete_user(access_token)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail="Failed to delete user and related data.")
