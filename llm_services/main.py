from fastapi import FastAPI, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from mistral_llm import process_question
from schemas import AskRequest, AskResponse
from utils import get_user_from_token

app = FastAPI()

# CORS Middleware for development - restrict origins as needed for production!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/llm/health")
def health() -> dict:
    """
    Health check endpoint for the LLM microservice.
    Returns:
        dict: Service status indicator.
    """
    return {"health": "All Good"}

@app.post("/llm/ask", response_model=AskResponse, status_code=status.HTTP_200_OK)
async def ask_question(payload: AskRequest, authorization: str = Header(None)) -> AskResponse:
    """
    Submit a user question to the Mistral LLM for processing.
    Args:
        payload (AskRequest): The file_hash and user question.
        authorization (str): Bearer token for user authentication.
    Returns:
        AskResponse: Structured LLM answer.
    Raises:
        HTTPException: On missing auth, missing fields, or server errors.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing.")
    access_token = authorization.replace("Bearer ", "").strip()
    try:
        user = get_user_from_token(access_token)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
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
