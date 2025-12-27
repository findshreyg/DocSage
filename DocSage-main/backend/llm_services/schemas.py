from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
import re

class AskRequest(BaseModel):
    """Request schema for posing a LLM question about a file."""
    question: str = Field(..., min_length=1, max_length=2000, strip_whitespace=True)
    file_hash: str = Field(..., min_length=1, max_length=256)

    @field_validator('file_hash')
    @classmethod
    def validate_file_hash(cls, v):
        """Validate file hash format."""
        if not re.match(r'^[a-fA-F0-9]+$', v):
            raise ValueError('File hash must be a valid hexadecimal string')
        return v

    @field_validator('question')
    @classmethod
    def validate_question(cls, v):
        """Validate question content."""
        if not v.strip():
            raise ValueError('Question cannot be empty')
        return v.strip()

class SourceInfo(BaseModel):
    location: Optional[str] = None
    search_anchor: Optional[str] = None
    page_number: Optional[int] = None
    context: Optional[str] = None
    extraction_method: Optional[str] = None
class AskResponse(BaseModel):
    question: str
    answer: str
    confidence: float
    reasoning: str
    source: Optional[SourceInfo] = None
    verified: bool
    total_pages: Optional[int] = None
    data_quality_notes: Optional[str] = None
    alternative_interpretations: Optional[List[str]] = None

class AdaptiveExtractRequest(BaseModel):
    """Request schema for adaptive document extraction."""
    file_hash: str = Field(..., min_length=1, max_length=256)

    @field_validator('file_hash')
    @classmethod
    def validate_file_hash(cls, v):
        """Validate file hash format."""
        if not re.match(r'^[a-fA-F0-9]+$', v):
            raise ValueError('File hash must be a valid hexadecimal string')
        return v

class ClassificationResult(BaseModel):
    """Document classification result."""
    document_type: str
    description: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)

class FieldDefinition(BaseModel):
    """Field definition for extraction."""
    field: str
    description: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)

class FieldValueWithConfidence(BaseModel):
    """Field value with confidence score."""
    value: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)

class AdaptiveExtractResponse(BaseModel):
    """Response schema for adaptive extraction."""
    classification: ClassificationResult
    fields_to_extract: List[FieldDefinition]
    field_values: Dict[str, FieldValueWithConfidence]
    raw_extracted_text: Optional[str] = None