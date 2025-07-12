from pydantic import BaseModel, Field
from typing import Optional, Dict

class DeleteConversationRequest(BaseModel):
    access_token: str
    file_hash: str
    question: str

class DeleteAllConversationsRequest(BaseModel):
    access_token: str
    file_hash: str

class GetAllConversationsRequest(BaseModel):
    access_token: str

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