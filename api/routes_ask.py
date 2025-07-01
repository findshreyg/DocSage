from fastapi import APIRouter, HTTPException, Depends
from models.schemas import AskRequest, AskResponse
from auth_service.deps import get_current_user
from services.mistral_llm import process_question

router = APIRouter()

# 🔒 Protected ASK endpoint
@router.post("/", response_model=AskResponse, status_code=200)
async def ask_question(payload: AskRequest, user: dict = Depends(get_current_user)):
    """
    Handle a question for a specific file.
    """
    if not payload.file_hash:
        raise HTTPException(status_code=400, detail="file_hash is required.")
    try:
        result = await process_question(payload, user)
        if not result:
            raise HTTPException(status_code=500, detail="No response from LLM")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

