from pydantic import BaseModel

class SignupRequest(BaseModel):
    email: str
    password: str
    name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ConfirmSignUpRequest(BaseModel):
    email: str
    code: str

class ResendRequest(BaseModel):
    email: str

class RefreshRequest(BaseModel):
    email: str
    refresh_token: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ConfirmForgotPasswordRequest(BaseModel):
    email: str
    code: str
    new_password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str