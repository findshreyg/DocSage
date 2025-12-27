from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
import re

class DeleteFileRequest(BaseModel):
    """Request schema for deleting a file."""
    file_hash: str = Field(..., min_length=1, max_length=256)
    
    @field_validator('file_hash')
    @classmethod
    def validate_file_hash(cls, v):
        """Validate file hash format."""
        if not re.match(r'^[a-fA-F0-9]+$', v):
            raise ValueError('File hash must be a valid hexadecimal string')
        return v

class DownloadFileRequest(BaseModel):
    """Request schema for downloading a file."""
    file_hash: str = Field(..., min_length=1, max_length=256)
    
    @field_validator('file_hash')
    @classmethod
    def validate_file_hash(cls, v):
        """Validate file hash format."""
        if not re.match(r'^[a-fA-F0-9]+$', v):
            raise ValueError('File hash must be a valid hexadecimal string')
        return v

# Response schemas
class UploadResponse(BaseModel):
    """Response schema for file upload."""
    message: str
    s3_key: str
    file_hash: str
    result: Optional[Dict[str, Any]] = None

class FileListResponse(BaseModel):
    """Response schema for file listing."""
    files: List[Dict[str, Any]]
    message: Optional[str] = None

class DownloadResponse(BaseModel):
    """Response schema for download URL generation."""
    url: str

class MessageResponse(BaseModel):
    """Standard message response."""
    message: str

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

class FieldValueWithConfidence(BaseModel):
    """Field value with confidence score."""
    value: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    
    @field_validator('value', mode='before')
    @classmethod
    def convert_value_to_string(cls, v):
        """Convert various types to string, including lists."""
        if isinstance(v, list):
            # Join list items with commas
            return ', '.join(str(item) for item in v)
        elif v is None:
            return ""
        else:
            return str(v)

class ClassificationResult(BaseModel):
    """Document classification result."""
    document_type: str
    description: str
    confidence: float = Field(..., ge=0.0, le=1.0)

class AdaptiveExtractResponse(BaseModel):
    """Response schema for adaptive document extraction."""
    classification: ClassificationResult
    field_values: Dict[str, FieldValueWithConfidence]
    raw_extracted_text: Optional[str] = None