# Pydantic schemas for request/response validation in the authentication service
# These schemas define the structure and validation rules for all API endpoints

from pydantic import BaseModel, EmailStr, Field, field_validator  # Pydantic for data validation
from typing import Optional  # Type hints for optional fields
import re  # Regular expressions for pattern validation

# REQUEST SCHEMAS - Define the structure of incoming API requests

class SignupRequest(BaseModel):
    """
    Schema for user registration requests.
    
    Validates:
    - Email format and validity
    - Password complexity requirements
    - Name format and length
    """
    email: EmailStr  # Automatically validates email format
    password: str = Field(..., min_length=8, max_length=128)  # Password length constraints
    name: str = Field(..., min_length=1, max_length=100)  # Name length constraints

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """
        Enforce strong password requirements for security.
        
        Password must contain:
        - At least one uppercase letter (A-Z)
        - At least one lowercase letter (a-z)
        - At least one digit (0-9)
        - At least one special character
        
        This matches AWS Cognito's default password policy.
        """
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """
        Validate name format to prevent injection attacks and ensure proper display.
        
        Allowed characters:
        - Letters (a-z, A-Z)
        - Spaces
        - Hyphens (-)
        - Apostrophes (')
        - Periods (.)
        
        This covers most legitimate name formats while preventing malicious input.
        """
        if not re.match(r'^[a-zA-Z\s\-\'\.]+$', v):
            raise ValueError('Name can only contain letters, spaces, hyphens, apostrophes, and periods')
        return v

class LoginRequest(BaseModel):
    """
    Schema for user login requests.
    
    Simple validation - just ensures email format and password presence.
    Actual credential validation happens in AWS Cognito.
    """
    email: EmailStr  # Validates email format
    password: str = Field(..., min_length=1)  # Ensures password is not empty

class ConfirmSignUpRequest(BaseModel):
    """
    Schema for confirming user registration with email verification code.
    
    Code must be exactly 6 digits as sent by AWS Cognito.
    """
    email: EmailStr  # User's email address
    code: str = Field(..., pattern=r'^\d{6}$')  # Exactly 6 digits

class ResendRequest(BaseModel):
    """
    Schema for requesting resend of confirmation code.
    
    Only requires email to identify the user.
    """
    email: EmailStr  # User's email address

class RefreshRequest(BaseModel):
    """
    Schema for refreshing JWT tokens using refresh token.
    
    Requires both email (for identification) and refresh token.
    """
    email: EmailStr  # User's email address
    refresh_token: str = Field(..., min_length=1)  # Refresh token from previous login

class ForgotPasswordRequest(BaseModel):
    """
    Schema for initiating password reset process.
    
    Only requires email to send reset code.
    """
    email: EmailStr  # User's email address

class ConfirmForgotPasswordRequest(BaseModel):
    """
    Schema for completing password reset with code and new password.
    
    Validates new password with same complexity rules as signup.
    """
    email: EmailStr  # User's email address
    code: str = Field(..., pattern=r'^\d{6}$')  # 6-digit reset code from email
    new_password: str = Field(..., min_length=8, max_length=128)  # New password

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        """
        Enforce same password complexity rules as signup.
        Ensures consistent security standards across all password operations.
        """
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

class ChangePasswordRequest(BaseModel):
    """
    Schema for changing password while logged in.
    
    Requires both old password (for verification) and new password.
    """
    old_password: str = Field(..., min_length=1)  # Current password for verification
    new_password: str = Field(..., min_length=8, max_length=128)  # New password

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        """
        Enforce password complexity rules for new password.
        Same validation as signup and forgot password for consistency.
        """
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

# RESPONSE SCHEMAS - Define the structure of API responses

class AuthResponse(BaseModel):
    """
    Schema for successful authentication responses (login, refresh token).
    
    Contains all tokens and user information needed by client applications:
    - access_token: For API authorization (short-lived, ~1 hour)
    - id_token: Contains user identity claims (JWT format)
    - refresh_token: For getting new access tokens (long-lived, ~30 days)
    - name: User's display name
    - email: User's email address
    """
    access_token: str  # JWT token for API authorization
    id_token: str  # JWT token with user identity claims
    refresh_token: str  # Token for refreshing access tokens
    name: str  # User's display name
    email: str  # User's email address

class MessageResponse(BaseModel):
    """
    Schema for simple success/status responses.
    
    Used for operations that don't return complex data:
    - Signup confirmation
    - Password reset confirmation
    - Logout confirmation
    - Account deletion confirmation
    """
    message: str  # Human-readable status message

class UserResponse(BaseModel):
    """
    Schema for user profile information responses.
    
    Contains user details retrieved from AWS Cognito:
    - id: Unique user identifier (username in Cognito)
    - email: User's email address
    - name: User's display name (optional, may be None)
    """
    id: str  # Unique user identifier
    email: str  # User's email address
    name: Optional[str] = None  # Display name (optional)