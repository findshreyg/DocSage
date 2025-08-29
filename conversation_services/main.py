import logging
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware

# Correct relative imports
from .utils import get_user_from_token
from .schemas import (
    FindConversationRequest,
    DeleteConversationRequest,
    DeleteAllConversationsRequest,
)
from .conversation_handler import (
    find_conversation,
    get_all_conversations_by_file,
    delete_conversation,
    delete_all_conversations,
)

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/conversation/health")
def check_health() -> dict:
    return {"health": "All Good"}

@app.get("/conversation/get-file-conversations")
def get_conversations(file_hash: str, authorization: str = Header(None)) -> dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        token = authorization.replace("Bearer ", "").strip()
        user = get_user_from_token(token)
        logger.info(f"Resolved user: {user.get('Username')}.")
        results = get_all_conversations_by_file(user["Username"], file_hash)
        return {"conversations": results, "message": "Conversations retrieved successfully."}
    except Exception as e:
        logger.exception("Unexpected error fetching conversations.")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error fetching conversations: {str(e)}. Check logs for traceback."
        )

@app.delete("/conversation/delete-conversation")
def delete_conversation_endpoint(payload: DeleteConversationRequest, request: Request) -> dict:
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
    except Exception as e:
        logger.exception("Unexpected error deleting conversation.")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.delete("/conversation/delete-all-conversations")
def delete_all_conversation_endpoint(payload: DeleteAllConversationsRequest, request: Request) -> dict:
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
    except Exception as e:
        logger.exception("Unexpected error deleting all conversations.")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.post("/conversation/find-conversation")
def find_conversation_endpoint(payload: FindConversationRequest, request: Request) -> dict:
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
    except Exception as e:
        logger.exception("Unexpected error finding conversation.")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")