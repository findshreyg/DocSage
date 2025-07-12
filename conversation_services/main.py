from fastapi import HTTPException, Request, FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from utils import get_user_from_token
from dotenv import load_dotenv
import os

load_dotenv()

from conversation_handler import (
    find_conversation, get_all_conversations, delete_conversation, delete_all_conversations
)
from schemas import FindConversationRequest,DeleteConversationRequest, DeleteAllConversationsRequest

app = FastAPI()

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/conversation/health")
def check_health():
    """
    Health check endpoint for the conversation service.

    Returns:
        dict: Health status.
    """
    return {
        "health": "All Good"
    }

@app.get("/conversation/get-all-conversations")
def get_conversations(authorization: str = Header(None)):
    """
    Retrieve all conversation records for the authenticated user.

    Returns:
        dict: List of conversations and a success message.

    Raises:
        HTTPException: If authorization is missing or any unexpected error occurs.
    """
    try:
        import logging
        import traceback
        logger = logging.getLogger(__name__)

        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        token = authorization.replace("Bearer ", "").strip()
        user = get_user_from_token(token)
        logger.info(f"Resolved user: {user}. Using AWS_REGION={os.environ.get('AWS_REGION')}")
        results = get_all_conversations(user["Username"])
        return {"conversations": results, "message": "Conversations retrieved successfully."}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("Unexpected error fetching conversations:\n" + traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Unexpected error fetching conversations: {str(e)}. Check logs for traceback.")

@app.delete("/conversation/delete-conversation")
def delete_conversation_endpoint(payload: DeleteConversationRequest, request: Request):
    """
    Delete a specific conversation matching the given file hash and question.

    Args:
        payload (DeleteConversationRequest): Contains file hash and question.
        request (Request): Incoming HTTP request with Authorization header.

    Returns:
        dict: Deletion status message.

    Raises:
        HTTPException: If auth is missing or deletion fails.
    """
    try:
        access_token = request.headers.get("Authorization")
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        token = access_token.replace("Bearer ", "").strip()
        user = get_user_from_token(token)
        success, message = delete_conversation(user["Username"], payload.file_hash, payload.question)
        if not success:
            raise HTTPException(status_code=404, detail=message)
        return {"message": message}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.delete("/conversation/delete-all-conversations")
def delete_all_conversation_endpoint(payload: DeleteAllConversationsRequest, request: Request):
    """
    Delete all conversations for a given file hash for the authenticated user.

    Args:
        payload (DeleteAllConversationsRequest): Contains file hash.
        request (Request): Incoming HTTP request with Authorization header.

    Returns:
        dict: Deletion status message.

    Raises:
        HTTPException: If auth is missing or deletion fails.
    """
    try:
        access_token = request.headers.get("Authorization")
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        token = access_token.replace("Bearer ", "").strip()
        user = get_user_from_token(token)
        success, message = delete_all_conversations(user["Username"], payload.file_hash)
        if not success:
            raise HTTPException(status_code=404, detail=message)
        return {"message": message}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.post("/conversation/find-conversation")
def find_conversation_endpoint(payload: FindConversationRequest, request: Request):
    """
    Find a specific conversation for a file hash and question.

    Args:
        payload (FindConversationRequest): Contains file hash and question.
        request (Request): Incoming HTTP request with Authorization header.

    Returns:
        dict: The found conversation and a message.

    Raises:
        HTTPException: If auth is missing or conversation not found.
    """
    try:
        access_token = request.headers.get("Authorization")
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        token = access_token.replace("Bearer ", "").strip()
        user = get_user_from_token(token)
        result = find_conversation(user["Username"], payload.file_hash, payload.question)
        if not result:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"conversation_services": result, "message": "Conversation found successfully."}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")