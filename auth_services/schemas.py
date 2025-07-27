from pydantic import BaseModel

class SignupRequest(BaseModel):
    """
    Schema for user registration request.
    """
    email: str
    password: str
    name: str

class LoginRequest(BaseModel):
    """
    Schema for login request.
    """
    email: str
    password: str

class ConfirmSignUpRequest(BaseModel):
    """
    Schema for sign up confirmation.
    """
    email: str
    code: str

class ResendRequest(BaseModel):
    """
    Schema for requesting resend of confirmation code.
    """
    email: str

class RefreshRequest(BaseModel):
    """
    Schema for token refresh.
    """
    email: str
    refresh_token: str

class ForgotPasswordRequest(BaseModel):
    """
    Schema for requesting password reset.
    """
    email: str

class ConfirmForgotPasswordRequest(BaseModel):
    """
    Schema for confirming password reset.
    """
    email: str
    code: str
    new_password: str

class ChangePasswordRequest(BaseModel):
    """
    Schema for password change.
    """
    old_password: str
    new_password: str

