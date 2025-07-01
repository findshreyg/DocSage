from fastapi import APIRouter, HTTPException, Depends
from auth_service.deps import get_current_user
from conversation.conversation_handler import (
    find_conversation, get_all_conversations, delete_conversation, delete_all_conversations
)
from models.schemas import FindConversationRequest,DeleteConversationRequest, DeleteAllConversationsRequest

router = APIRouter()

@router.post("/get-all-conversations")
def get_conversations(user: dict = Depends(get_current_user)):
    try:
        results = get_all_conversations(user["sub"])
        return {
            "conversations": results,
            "message": "Conversations retrieved successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/delete-conversation")
def delete_conversation_endpoint(payload: DeleteConversationRequest, user: dict = Depends(get_current_user)):
    try:
        success, message = delete_conversation(user["sub"], payload.file_hash, payload.question)
        if not success:
            raise HTTPException(status_code=404, detail=message)
        return {"message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/delete-all-conversations")
def delete_all_conversation_endpoint(payload: DeleteAllConversationsRequest, user: dict = Depends(get_current_user)):
    try:
        success, message = delete_all_conversations(user["sub"], payload.file_hash)
        if not success:
            raise HTTPException(status_code=404, detail=message)
        return {"message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/find-conversation")
def find_conversation_endpoint(payload: FindConversationRequest, user: dict = Depends(get_current_user)):
    try:
        result = find_conversation(user["sub"], payload.file_hash, payload.question)
        if not result:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {
            "conversation": result,
            "message": "Conversation found successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")