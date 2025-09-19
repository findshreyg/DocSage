import os
import logging
from fastapi import HTTPException, Request, FastAPI, Header, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from dotenv import load_dotenv

from utils import get_user_from_token
from schemas import (
    FindConversationRequest, DeleteConversationRequest, DeleteAllConversationsRequest,
    GetAllConversationsPerUserPerFile, ConversationResponse, ConversationFoundResponse, MessageResponse
)
from conversation_handler import (
    find_conversation, get_all_conversations_by_file, delete_conversation, delete_all_conversations
)

load_dotenv()

app = FastAPI(
    title="DocSage Conversation Service",
    description="Conversation Management API",
    version="1.1.0"
)

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors."""
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "Validation error",
            "details": exc.errors()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.get("/conversation/health")
def check_health() -> dict:
    """
    Health check endpoint for the conversation service.
    Returns:
        dict: Health status.
    """
    return {"health": "All Good"}

@app.get("/conversation/get-file-conversations")
def get_conversations(
    file_hash: str,
    authorization: str = Header(None)
) -> dict:
    """
    Retrieve all conversation records for the authenticated user and file.

    Args:
        file_hash (str): The hash of the file.
        authorization (str): Bearer token in the Authorization header.

    Returns:
        dict: List of conversations.

    Raises:
        HTTPException: If authorization is missing or fetch fails.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        token = authorization.replace("Bearer ", "").strip()
        user = get_user_from_token(token)
        logger.info(f"Resolved user: {user.get('Username')}.")
        results = get_all_conversations_by_file(user["Username"], file_hash)
        return {"conversations": results, "message": "Conversations retrieved successfully."}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception("Unexpected error fetching conversations.")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error fetching conversations: {str(e)}. Check logs for traceback."
        )

@app.delete("/conversation/delete-conversation")
def delete_conversation_endpoint(
    payload: DeleteConversationRequest,
    request: Request
) -> dict:
    """
    Delete a specific conversation for a file hash and question.

    Args:
        payload (DeleteConversationRequest): Contains file hash and question.
        request (Request): HTTP request object.

    Returns:
        dict: Deletion message.

    Raises:
        HTTPException: For errors and unauthorized use.
    """
    access_token = request.headers.get("Authorization")
    if not access_token:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        token = access_token.replace("Bearer ", "").strip()
        user = get_user_from_token(token)
        success, message = delete_conversation(user["Username"], payload.file_hash, payload.question)
        if not success:
            raise HTTPException(status_code=404, detail=message)
        return {"message": message}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception("Unexpected error deleting conversation.")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.delete("/conversation/delete-all-conversations")
def delete_all_conversation_endpoint(
    payload: DeleteAllConversationsRequest,
    request: Request
) -> dict:
    """
    Delete all conversations for a specific file hash for the user.

    Args:
        payload (DeleteAllConversationsRequest): Contains file hash.
        request (Request): HTTP request.

    Returns:
        dict: Deletion message.

    Raises:
        HTTPException: For errors and unauthorized access.
    """
    access_token = request.headers.get("Authorization")
    if not access_token:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        token = access_token.replace("Bearer ", "").strip()
        user = get_user_from_token(token)
        success, message = delete_all_conversations(user["Username"], payload.file_hash)
        if not success:
            raise HTTPException(status_code=404, detail=message)
        return {"message": message}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception("Unexpected error deleting all conversations.")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.post("/conversation/find-conversation")
def find_conversation_endpoint(
    payload: FindConversationRequest,
    request: Request
) -> dict:
    """
    Find a specific conversation for a file hash and question.

    Args:
        payload (FindConversationRequest): Contains file hash and question.
        request (Request): HTTP request.

    Returns:
        dict: The found conversation and a message.

    Raises:
        HTTPException: If conversation not found or on auth error.
    """
    access_token = request.headers.get("Authorization")
    if not access_token:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        token = access_token.replace("Bearer ", "").strip()
        user = get_user_from_token(token)
        result = find_conversation(user["Username"], payload.file_hash, payload.question)
        if not result:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"conversation_services": result, "message": "Conversation found successfully."}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception("Unexpected error finding conversation.")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

