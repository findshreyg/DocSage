# Design Document

## Overview

This design addresses critical issues in the file services module by fixing import dependencies, completing schema definitions, correcting environment variable usage, and ensuring proper integration between components. The solution focuses on maintaining existing functionality while resolving structural problems that prevent the service from operating correctly.

## Architecture

The file services module consists of three main components that need fixes:

1. **file_handler.py** - Main business logic for file operations
2. **utils.py** - Utility functions for AWS operations and LLM integration  
3. **schemas.py** - Pydantic models for request/response validation

The current issues stem from:
- Missing imports between services (file_services trying to use llm_services schemas)
- Incomplete schema definitions in file_services/schemas.py
- Hardcoded constants instead of environment variables
- Missing utility functions

## Components and Interfaces

### Schema Definitions

**Problem:** file_services/schemas.py is incomplete and missing adaptive extraction schemas that are defined in llm_services/schemas.py.

**Solution:** Complete the file_services/schemas.py with all necessary Pydantic models:

```python
# Additional schemas needed in file_services/schemas.py
class AdaptiveExtractRequest(BaseModel)
class ClassificationResult(BaseModel) 
class FieldValueWithConfidence(BaseModel)
class AdaptiveExtractResponse(BaseModel)
```

### Import Dependencies

**Problem:** file_handler.py imports classes that don't exist in the local schemas.py.

**Solution:** Add missing imports and ensure all required classes are available:

```python
# file_handler.py needs:
from datetime import datetime
from schemas import AdaptiveExtractRequest, AdaptiveExtractResponse
```

### Environment Variables and Constants

**Problem:** utils.py uses undefined constants and hardcoded table names.

**Solution:** Properly load and use environment variables:

```python
# Constants that need to be defined in utils.py:
DDB_TABLE = os.getenv("DDB_TABLE")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME") 
METADATA_TABLE_NAME = os.getenv("DDB_TABLE")  # Alias for consistency
```

### Utility Functions

**Problem:** utils.py calls extract_json_from_llm_response which doesn't exist locally.

**Solution:** Implement the missing utility function within utils.py:

```python
def extract_json_from_llm_response(text: str) -> dict:
    """Extract JSON from LLM response text"""
    # Implementation to parse JSON from text response
```

## Data Models

### Enhanced Schema Structure

The schemas.py file needs to include all models used by the file service:

1. **Existing Models** (already present):
   - DeleteFileRequest
   - DownloadFileRequest  
   - UploadResponse
   - FileListResponse
   - DownloadResponse
   - MessageResponse

2. **Missing Models** (need to be added):
   - AdaptiveExtractRequest
   - ClassificationResult
   - FieldDefinition
   - FieldValueWithConfidence
   - AdaptiveExtractResponse

### DynamoDB Integration

**Current Issue:** save_metadata function uses hardcoded table name 'IDPMetadata' instead of environment variable.

**Solution:** Use DDB_TABLE environment variable consistently and fix the DynamoDB client initialization to include the region parameter.

## Error Handling

### Import Error Prevention

- Ensure all imports are available before use
- Add proper error handling for missing dependencies
- Provide fallback behavior when optional features fail

### AWS Service Error Handling

- Maintain existing error handling patterns for S3 and DynamoDB operations
- Ensure proper logging of AWS service errors
- Handle missing environment variables gracefully

### LLM Integration Error Handling

- Handle cases where adaptive extraction fails
- Provide fallback metadata when LLM services are unavailable
- Maintain data integrity even when advanced features fail

## Testing Strategy

### Unit Testing Approach

1. **Schema Validation Tests**
   - Test all Pydantic models with valid and invalid data
   - Verify field validation rules work correctly
   - Test serialization/deserialization

2. **Import and Dependency Tests**
   - Verify all modules can be imported without errors
   - Test that all required classes and functions are accessible
   - Validate environment variable loading

3. **Integration Tests**
   - Test file upload flow with metadata extraction
   - Test adaptive extraction integration
   - Test error handling and fallback scenarios

### Environment Testing

- Test with missing environment variables
- Test with invalid AWS credentials
- Test with unreachable external services

## Implementation Notes

### Backward Compatibility

All fixes maintain backward compatibility with existing API contracts and database schemas. No breaking changes to external interfaces.

### Performance Considerations

The fixes do not introduce performance overhead. The main changes are structural improvements that should have minimal runtime impact.

### Security Considerations

- Environment variables continue to be used for sensitive configuration
- No changes to authentication or authorization mechanisms
- AWS service access patterns remain unchanged