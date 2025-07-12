# models/schemas.py

from pydantic import BaseModel


class DeleteConversationRequest(BaseModel):
    file_hash: str
    question: str

class DeleteAllConversationsRequest(BaseModel):
    file_hash: str

class FindConversationRequest(BaseModel):
    file_hash: str
    question: str


