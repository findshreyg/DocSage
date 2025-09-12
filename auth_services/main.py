# Import FastAPI framework and related components for building REST API
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware  # Enable Cross-Origin Resource Sharing
from fastapi.responses import JSONResponse  # For custom JSON error responses
from pydantic import ValidationError  # Handle request validation errors
import logging  # For application logging

# Import our custom modules that handle different aspects of authentication
import authentication  # Core authentication functions (login, signup, logout)
import password_management  # Password-related operations (reset, change, forgot)
import user_management  # User lifecycle management (confirm, get user info, delete)

# Import utility functions and data validation schemas
from utils import get_access_token  # Extract and validate JWT tokens from requests
from schemas import (
    # Request schemas - define the structure of incoming API requests
    SignupRequest, LoginRequest, RefreshRequest, ConfirmSignUpRequest,
    ResendRequest, ForgotPasswordRequest, ChangePasswordRequest, ConfirmForgotPasswordRequest,
    # Response schemas - define the structure of API responses
    AuthResponse, MessageResponse, UserResponse
)

# Create the FastAPI application instance with metadata
app = FastAPI(
    title="DocSage Authentication Service",  # Service name for API documentation
    description="Authentication and User Management API",  # Service description
    version="1.1.0"  # API version for tracking changes
)

# Configure structured logging to track application events and errors
logging.basicConfig(
    level=logging.INFO,  # Log INFO level and above (INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # Log format with timestamp
)
logger = logging.getLogger(__name__)  # Create logger instance for this module

# Add CORS middleware to allow cross-origin requests from web browsers
# This is essential for frontend applications running on different domains/ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from any origin (configure for production)
    allow_credentials=True,  # Allow cookies and authorization headers
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all request headers
)

# Global exception handlers to provide consistent error responses across all endpoints

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """
    Handle Pydantic validation errors when request data doesn't match schema requirements.
    This occurs when users send invalid data (wrong types, missing fields, etc.)
    """
    return JSONResponse(
        status_code=422,  # HTTP 422 Unprocessable Entity - validation failed
        content={
            "error": True,
            "message": "Validation error",
            "details": exc.errors()  # Detailed validation error information
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTP exceptions raised by our application logic.
    These are controlled errors with specific status codes and messages.
    """
    return JSONResponse(
        status_code=exc.status_code,  # Use the status code from the exception
        content={
            "error": True,
            "message": exc.detail,  # Error message from the exception
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle any unexpected exceptions that weren't caught by specific handlers.
    This is our safety net to prevent the service from crashing.
    """
    logger.exception(f"Unhandled exception in {request.url}")  # Log full stack trace
    return JSONResponse(
        status_code=500,  # HTTP 500 Internal Server Error
        content={
            "error": True,
            "message": "Internal server error",  # Generic message for security
            "status_code": 500
        }
    )

# API Endpoints - Each endpoint handles a specific authentication operation

@app.get("/auth/health")
def health():
    """
    Health check endpoint to verify the service is running.
    Used by load balancers and monitoring systems to check service availability.
    """
    return {"health": "All Good"}

@app.post("/auth/signup", status_code=status.HTTP_201_CREATED, response_model=MessageResponse)
def sign_up(payload: SignupRequest) -> MessageResponse:
    """
    Register a new user account in AWS Cognito.
    
    Process:
    1. Validate input data (email, password complexity, name format)
    2. Create user account in Cognito with email and name attributes
    3. Send confirmation email to user
    4. Return success message
    """
    try:
        # Call the authentication module to handle Cognito user creation
        result = authentication.sign_up(payload.email, payload.password, payload.name)
        logger.info(f"User signup successful: {payload.email}")
        return MessageResponse(**result)
    except HTTPException:
        # Re-raise HTTP exceptions (these have proper error messages)
        raise
    except Exception as e:
        # Log unexpected errors and return generic error message
        logger.exception(f"Unexpected error during signup for {payload.email}")
        raise HTTPException(status_code=500, detail="Unexpected error during signup.")

@app.post("/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    """
    Authenticate user credentials and return JWT tokens.
    
    Process:
    1. Validate email and password against Cognito
    2. Generate access token, ID token, and refresh token
    3. Retrieve user profile information (name, email)
    4. Return tokens and user info for client-side storage
    """
    try:
        # Call authentication module to verify credentials and get tokens
        result = authentication.login(payload.email, payload.password)
        logger.info(f"User login successful: {payload.email}")
        return AuthResponse(**result)
    except HTTPException:
        # Re-raise HTTP exceptions with specific error details
        raise
    except Exception as e:
        # Log unexpected errors for debugging
        logger.exception(f"Unexpected error during login for {payload.email}")
        raise HTTPException(status_code=500, detail="Unexpected error during login.")

@app.post("/auth/refresh-token")
def refresh_token(payload: RefreshRequest):
    """
    Generate new access and ID tokens using a refresh token.
    
    Process:
    1. Validate the refresh token with Cognito
    2. Generate new access token and ID token
    3. Return new tokens (refresh token may also be rotated)
    
    This allows users to stay logged in without re-entering credentials.
    """
    try:
        # Use refresh token to get new access tokens from Cognito
        return authentication.refresh_token(payload.email, payload.refresh_token)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error refreshing token.")
        raise HTTPException(status_code=500, detail="Unexpected error refreshing token.")

@app.post("/auth/logout")
def logout(access_token: str = Depends(get_access_token)):
    """
    Log out user by invalidating all their tokens globally.
    
    Process:
    1. Extract access token from Authorization header
    2. Call Cognito global sign-out to invalidate all user sessions
    3. User will need to log in again on all devices
    
    The Depends(get_access_token) automatically extracts and validates the Bearer token.
    """
    try:
        # Perform global logout in Cognito (invalidates all user sessions)
        return authentication.logout(access_token)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error during logout.")
        raise HTTPException(status_code=500, detail="Unexpected error during logout.")

@app.post("/auth/confirm-signup")
def confirm_sign_up(payload: ConfirmSignUpRequest):
    """
    Confirm user registration using the 6-digit code sent via email.
    
    Process:
    1. Validate the confirmation code against Cognito
    2. Activate the user account (change status from UNCONFIRMED to CONFIRMED)
    3. User can now log in with their credentials
    
    This step is required after signup before the user can authenticate.
    """
    try:
        # Confirm user account with the email verification code
        return user_management.confirm_sign_up(payload.email, payload.code)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error during confirmation.")
        raise HTTPException(status_code=500, detail="Unexpected error during confirmation.")

@app.post("/auth/resend-confirmation-code")
def resend_confirmation_code(payload: ResendRequest):
    """
    Resend the email confirmation code to users who didn't receive it.
    
    Process:
    1. Check if user exists and is still unconfirmed
    2. Generate and send new 6-digit confirmation code via email
    3. Previous codes become invalid
    
    Useful when users don't receive the initial confirmation email.
    """
    try:
        # Request new confirmation code from Cognito
        return password_management.resend_confirmation_code(payload.email)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error resending code.")
        raise HTTPException(status_code=500, detail="Unexpected error resending code.")

@app.post("/auth/forgot-password")
def forgot_password(payload: ForgotPasswordRequest):
    """
    Initiate password reset process for users who forgot their password.
    
    Process:
    1. Verify user exists in Cognito
    2. Generate and send password reset code via email
    3. Code expires after a set time (usually 1 hour)
    
    User will receive email with code to reset their password.
    """
    try:
        # Initiate forgot password flow in Cognito
        return password_management.forgot_password(payload.email)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error sending forgot password code.")
        raise HTTPException(status_code=500, detail="Unexpected error sending forgot password code.")

@app.post("/auth/confirm-forgot-password")
def confirm_forgot_password(payload: ConfirmForgotPasswordRequest):
    """
    Complete password reset using the code sent via email.
    
    Process:
    1. Validate the reset code from email
    2. Verify new password meets complexity requirements
    3. Update user's password in Cognito
    4. Invalidate all existing user sessions
    
    User can then log in with their new password.
    """
    try:
        # Complete password reset with code and new password
        return password_management.confirm_forgot_password(payload.email, payload.code, payload.new_password)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error during password reset confirmation.")
        raise HTTPException(status_code=500, detail="Unexpected error during password reset confirmation.")

@app.post("/auth/change-password")
def change_password(payload: ChangePasswordRequest, access_token: str = Depends(get_access_token)):
    """
    Change user's password while they are logged in.
    
    Process:
    1. Verify user is authenticated (valid access token)
    2. Validate current password is correct
    3. Verify new password meets complexity requirements
    4. Update password in Cognito
    
    Requires user to be logged in and know their current password.
    """
    try:
        # Change password using current access token and old password verification
        return password_management.change_password(access_token, payload.old_password, payload.new_password)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error during password change.")
        raise HTTPException(status_code=500, detail="Unexpected error during password change.")

@app.get("/auth/get-user", response_model=UserResponse)
def get_user(access_token: str = Depends(get_access_token)) -> UserResponse:
    """
    Retrieve current user's profile information.
    
    Process:
    1. Validate access token with Cognito
    2. Extract user attributes (ID, email, name)
    3. Return user profile data
    
    Used by frontend to display user information and verify authentication status.
    """
    try:
        # Get user profile information from Cognito using access token
        result = user_management.get_user(access_token)
        logger.info(f"User info retrieved successfully: {result.get('email')}")
        return UserResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error retrieving user info")
        raise HTTPException(status_code=500, detail="Unexpected error retrieving user info.")

@app.delete("/auth/delete-user")
def delete_user(access_token: str = Depends(get_access_token)):
    """
    Permanently delete user account and all associated data.
    
    Process:
    1. Verify user is authenticated
    2. Delete all user's uploaded files from S3
    3. Delete all file metadata from DynamoDB
    4. Delete all conversation history from DynamoDB
    5. Delete user account from Cognito
    
    This is irreversible - all user data is permanently removed.
    """
    try:
        # Perform complete user account and data deletion
        return user_management.delete_user(access_token)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error deleting user.")
        raise HTTPException(status_code=500, detail="Unexpected error deleting user.")
