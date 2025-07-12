from fastapi import HTTPException, FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from mistral_llm import process_question
from schemas import AskRequest, AskResponse
from utils import get_user_from_token

app = FastAPI()

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/llm/health")
def health():
    """
    Health check endpoint for the LLM microservice.

    Returns:
        dict: Simple status indicating the service is online.
    """
    return {"health": "All Good"}

@app.post("/llm/ask" , response_model=AskResponse, status_code=200)
async def ask_question(payload: AskRequest, authorization: str = Header(None)):
    """
    Submit a user question to the Mistral LLM for processing.

    This endpoint authenticates the user via the access token,
    checks for required fields, and forwards the question and file hash
    to the LLM handler to generate a structured answer.

    Args:
        payload (AskRequest): The input payload containing the file_hash and question.
        authorization (str): Bearer token for user authentication.

    Returns:
        AskResponse: The generated structured answer from the LLM.

    Raises:
        HTTPException:
            - 401 if the Authorization header is missing or the token is invalid.
            - 400 if the file_hash is missing in the request.
            - 500 for unexpected internal errors or empty LLM response.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing.")
    access_token = authorization.replace("Bearer ", "").strip()
    try:
        user = get_user_from_token(access_token)
    except Exception as e:
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