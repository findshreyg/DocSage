# models/schemas.py

from pydantic import BaseModel, Field
from typing import Optional, Dict

class AskRequest(BaseModel):
    question: str
    file_hash: str

class AskResponse(BaseModel):
    question: str
    answer: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    source: Optional[Dict] = None
    verified: bool


class SignupRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ConfirmRequest(BaseModel):
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

class DownloadRequest(BaseModel):
    file_hash: str

class DeleteConversationRequest(BaseModel):
    file_hash: str
    question: str

class DeleteAllConversationsRequest(BaseModel):
    file_hash: str

class FindConversationRequest(BaseModel):
    file_hash: str
    question: str

class DeleteFileRequest(BaseModel):
    file_hash: str
