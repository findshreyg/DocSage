from pydantic import BaseModel, Field
from typing import List,Optional, Dict
from typing import Any

class DeleteConversationRequest(BaseModel):
    """Request schema for deleting a conversation."""
    access_token: str
    file_hash: str
    question: str

class DeleteAllConversationsRequest(BaseModel):
    """Request schema to delete all conversations for a file."""
    access_token: str
    file_hash: str

class GetAllConversationsRequest(BaseModel):
    """Request schema to list all user conversations."""
    access_token: str

class AskRequest(BaseModel):
    """Request schema for posing a LLM question about a file."""
    question: str
    file_hash: str

class AskResponse(BaseModel):
    """Structured answer from LLM."""
    question: str
    answer: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    source: Optional[Dict] = None
    verified: bool

class AdaptiveExtractRequest(BaseModel):
    file_hash: str

class ClassificationResult(BaseModel):
    document_type: str
    description: Optional[str]
    confidence: float

class FieldDefinition(BaseModel):
    field: str
    description: Optional[str]
    confidence: float

class FieldValueWithConfidence(BaseModel):
    value: Optional[Any]
    confidence: float

class AdaptiveExtractResponse(BaseModel):
    classification: ClassificationResult
    fields_to_extract: List[FieldDefinition]
    field_values: Dict[str, FieldValueWithConfidence]
    raw_extracted_text: Optional[str] = None