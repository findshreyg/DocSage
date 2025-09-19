# LLM Service - Handles AI-powered document processing and question answering
# This service integrates with Mistral AI to provide intelligent document analysis

# Import FastAPI framework and related components for building REST API
from fastapi import FastAPI, HTTPException, Header, status, Request
from fastapi.middleware.cors import CORSMiddleware  # Enable Cross-Origin Resource Sharing
from fastapi.responses import JSONResponse  # For custom JSON error responses
from pydantic import ValidationError  # Handle request validation errors
import logging  # For application logging

# Import our custom modules that handle LLM operations
from mistral_llm import process_question, extract_adaptive_from_document  # Core LLM processing functions
from schemas import AskRequest, AskResponse, AdaptiveExtractRequest, AdaptiveExtractResponse  # Data validation schemas
from utils import get_user_from_token, get_stored_field_values  # Utility functions for auth and data retrieval

# Create the FastAPI application instance with metadata
app = FastAPI(
    title="DocSage LLM Service",  # Service name for API documentation
    description="Large Language Model Processing API",  # Service description
    version="1.1.0"  # API version for tracking changes
)

# Configure structured logging to track application events and errors
logging.basicConfig(
    level=logging.INFO,  # Log INFO level and above (INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # Log format with timestamp
)
logger = logging.getLogger(__name__)  # Create logger instance for this module

# Add CORS middleware to allow cross-origin requests from web browsers
# This is essential for frontend applications running on different domains/ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from any origin (configure for production)
    allow_credentials=True,  # Allow cookies and authorization headers
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"]  # Allow all request headers
)

# Global exception handlers to provide consistent error responses across all endpoints

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """
    Handle Pydantic validation errors when request data doesn't match schema requirements.
    This occurs when users send invalid data (wrong types, missing fields, etc.)
    """
    return JSONResponse(
        status_code=422,  # HTTP 422 Unprocessable Entity - validation failed
        content={
            "error": True,
            "message": "Validation error",
            "details": exc.errors()  # Detailed validation error information
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTP exceptions raised by our application logic.
    These are controlled errors with specific status codes and messages.
    """
    logger.error(f"HTTPException in {request.url}: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,  # Use the status code from the exception
        content={
            "error": True,
            "message": exc.detail,  # Error message from the exception
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle any unexpected exceptions that weren't caught by specific handlers.
    This is our safety net to prevent the service from crashing.
    """
    logger.error(f"Unhandled exception in {request.url}: {type(exc).__name__}: {str(exc)}")
    return JSONResponse(
        status_code=500,  # HTTP 500 Internal Server Error
        content={
            "error": True,
            "message": f"Internal server error: {str(exc)}",  # Include error details for debugging
            "status_code": 500
        }
    )

# API Endpoints - Each endpoint handles a specific LLM operation

@app.get("/llm/health")
def health() -> dict:
    """
    Health check endpoint to verify the LLM service is running.
    Used by load balancers and monitoring systems to check service availability.
    """
    return {"health": "All Good"}

@app.post("/llm/ask", response_model=AskResponse, status_code=status.HTTP_200_OK)
async def ask_question(payload: AskRequest, authorization: str = Header(None)) -> AskResponse:
    """
    Submit a user question to the Mistral LLM for intelligent document analysis.
    
    This endpoint:
    1. Validates user authentication with Cognito
    2. Retrieves document from S3 using file_hash
    3. Sends document and question to Mistral AI
    4. Processes LLM response with confidence scoring
    5. Saves conversation to DynamoDB for future reference
    6. Returns structured answer with source information
    
    The LLM analyzes the document content and provides detailed answers with:
    - Confidence scores for reliability assessment
    - Source locations within the document
    - Reasoning for how the answer was derived
    """
    # Validate authorization header is present
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing.")
    
    # Extract and validate access token
    access_token = authorization.replace("Bearer ", "").strip()
    try:
        user = get_user_from_token(access_token)  # Validate token with Cognito
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    
    # Validate required parameters
    if not payload.file_hash:
        raise HTTPException(status_code=400, detail="file_hash is required.")
    
    try:
        # Process question through Mistral LLM with document context
        result = await process_question(payload, user)
        if not result:
            raise HTTPException(status_code=500, detail="No response from LLM")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error processing question for {payload.file_hash}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/llm/extract-adaptive", status_code=200)
async def extract_adaptive(payload: AdaptiveExtractRequest, authorization: str = Header(None)):
    """
    Retrieve complete adaptive extraction data from IDPMetadata table.
    
    This endpoint:
    1. Validates user authentication with Cognito
    2. Queries DynamoDB IDPMetadata table using user_id and file_hash
    3. Extracts the complete adaptive_extraction data from metadata
    4. Returns the entire adaptive extraction information including:
       - Classification results (document_type, description, confidence)
       - Field values with confidence scores
       - Extraction status and timestamp
    
    The adaptive_extraction data contains pre-processed document analysis results
    that were generated during the initial file upload process.
    """
    # Validate authorization header is present
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing.")
    
    # Extract and validate access token
    access_token = authorization.replace("Bearer ", "").strip()
    try:
        user = get_user_from_token(access_token)  # Validate token with Cognito
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    
    # Validate file_hash parameter
    if not payload.file_hash:
        raise HTTPException(status_code=400, detail="file_hash is required.")
    
    try:
        # Retrieve complete adaptive extraction data from IDPMetadata table
        adaptive_data = await get_stored_field_values(payload.file_hash, user)
        return adaptive_data
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error retrieving adaptive extraction data for {payload.file_hash}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")