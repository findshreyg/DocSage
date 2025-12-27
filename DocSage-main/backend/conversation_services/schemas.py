from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
import re

class DeleteConversationRequest(BaseModel):
    """Schema for deleting a specific conversation."""
    file_hash: str = Field(..., min_length=1, max_length=256)
    question: str = Field(..., min_length=1, max_length=1000, strip_whitespace=True)

    @field_validator('file_hash')
    @classmethod
    def validate_file_hash(cls, v):
        """Validate file hash format."""
        if not re.match(r'^[a-fA-F0-9]+$', v):
            raise ValueError('File hash must be a valid hexadecimal string')
        return v

class DeleteAllConversationsRequest(BaseModel):
    """Schema for deleting all conversations for a file."""
    file_hash: str = Field(..., min_length=1, max_length=256)

    @field_validator('file_hash')
    @classmethod
    def validate_file_hash(cls, v):
        """Validate file hash format."""
        if not re.match(r'^[a-fA-F0-9]+$', v):
            raise ValueError('File hash must be a valid hexadecimal string')
        return v

class GetAllConversationsPerUserPerFile(BaseModel):
    """Schema for retrieving all conversations for a user/file."""
    file_hash: str = Field(..., min_length=1, max_length=256)

    @field_validator('file_hash')
    @classmethod
    def validate_file_hash(cls, v):
        """Validate file hash format."""
        if not re.match(r'^[a-fA-F0-9]+$', v):
            raise ValueError('File hash must be a valid hexadecimal string')
        return v

class FindConversationRequest(BaseModel):
    """Schema for finding a conversation given a file hash and question."""
    file_hash: str = Field(..., min_length=1, max_length=256)
    question: str = Field(..., min_length=1, max_length=1000, strip_whitespace=True)

    @field_validator('file_hash')
    @classmethod
    def validate_file_hash(cls, v):
        """Validate file hash format."""
        if not re.match(r'^[a-fA-F0-9]+$', v):
            raise ValueError('File hash must be a valid hexadecimal string')
        return v

# Response schemas
class ConversationResponse(BaseModel):
    """Response schema for conversation operations."""
    conversations: List[Dict[str, Any]]
    message: str

class ConversationFoundResponse(BaseModel):
    """Response schema for found conversation."""
    conversation_services: Dict[str, Any]
    message: str

class MessageResponse(BaseModel):
    """Standard message response."""
    message: str
