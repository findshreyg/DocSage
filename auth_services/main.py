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
import logging

# Set up logging for the application
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize the FastAPI application
app = FastAPI()

# Add CORS middleware to allow cross-origin requests from the React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint to verify service status
@app.get("/")
def health():
    return {"health": "All Good"}

# Endpoint to handle user signup requests
@app.post("/signup", status_code=status.HTTP_201_CREATED)
def sign_up(payload: SignupRequest):
    try:
        return authentication.sign_up(payload.email, payload.password, payload.name)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Signup failed: {e}")
        raise HTTPException(status_code=400, detail="Signup failed. Check email or password format.")

# Endpoint to handle user login requests
@app.post("/login")
def login(payload: LoginRequest):
    try:
        return authentication.login(payload.email, payload.password)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Login failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid email or password.")

# Endpoint to refresh authentication tokens
@app.post("/refresh-token")
def refresh_token(payload: RefreshRequest):
    try:
        return authentication.refresh_token(payload.email, payload.refresh_token)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Refresh token failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token.")

# Endpoint to handle user logout requests
@app.post("/logout")
def logout(access_token: str = Depends(get_access_token)):
    try:
        return authentication.logout(access_token)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Logout failed: {e}")
        raise HTTPException(status_code=401, detail="Failed to logout. Invalid token.")

# Endpoint to confirm user signup with a code
@app.post("/confirm-signup")
def confirm_sign_up(payload: ConfirmSignUpRequest):
    try:
        return user_management.confirm_sign_up(payload.email, payload.code)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Confirm signup failed: {e}")
        raise HTTPException(status_code=400, detail="Failed to confirm sign up. Invalid code or user.")

# Endpoint to resend confirmation code for signup
@app.post("/resend-confirmation-code")
def resend_confirmation_code(payload: ResendRequest):
    try:
        return password_management.resend_confirmation_code(payload.email)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Resend confirmation code failed: {e}")
        raise HTTPException(status_code=400, detail="Failed to resend confirmation code.")

# Endpoint to handle forgot password requests
@app.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest):
    try:
        return password_management.forgot_password(payload.email)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Forgot password failed: {e}")
        raise HTTPException(status_code=400, detail="Failed to send forgot password code.")

# Endpoint to confirm forgot password with a code and set a new password
@app.post("/confirm-forgot-password")
def confirm_forgot_password(payload: ConfirmForgotPasswordRequest):
    try:
        return password_management.confirm_forgot_password(payload.email, payload.code, payload.new_password)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Confirm forgot password failed: {e}")
        raise HTTPException(status_code=400, detail="Failed to confirm forgot password. Check code and password format.")

# Endpoint to change user password
@app.post("/change-password")
def change_password(payload: ChangePasswordRequest, access_token: str = Depends(get_access_token)):
    try:
        return password_management.change_password(access_token, payload.old_password, payload.new_password)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Change password failed: {e}")
        raise HTTPException(status_code=400, detail="Failed to change password. Check current or new password.")

# Endpoint to retrieve user information
@app.get("/get-user")
def get_user(access_token: str = Depends(get_access_token)):
    try:
        return user_management.get_user(access_token)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Get user failed: {e}")
        raise HTTPException(status_code=401, detail="Failed to retrieve user. Invalid or expired token.")

# Endpoint to delete a user and their related data
@app.delete("/delete-user")
def delete_user(access_token: str = Depends(get_access_token)):
    try:
        return user_management.delete_user(access_token)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Delete user failed: {e}")
        raise HTTPException(status_code=400, detail="Failed to delete user and related data.")
