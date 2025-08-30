from fastapi import FastAPI, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware

# Correct relative imports
from .mistral_llm import process_question, extract_adaptive_from_document, get_cached_extraction
from .schemas import AskRequest, AskResponse, AdaptiveExtractRequest, AdaptiveExtractResponse
from .utils import get_user_from_token

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/llm/health")
def health() -> dict:
    return {"health": "All Good"}

@app.post("/llm/ask", response_model=AskResponse, status_code=status.HTTP_200_OK)
async def ask_question(payload: AskRequest, authorization: str = Header(None)) -> AskResponse:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing.")
    access_token = authorization.replace("Bearer ", "").strip()
    try:
        user = get_user_from_token(access_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    if not payload.file_hash:
        raise HTTPException(status_code=400, detail="file_hash is required.")
    try:
        result = await process_question(payload, user)
        if not result:
            raise HTTPException(status_code=500, detail="No response from LLM")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/llm/extract-adaptive", status_code=200)
async def extract_adaptive(payload: AdaptiveExtractRequest, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing.")
    user = get_user_from_token(authorization.replace("Bearer ", "").strip())
    return await extract_adaptive_from_document(payload, user)

@app.get("/llm/get-extraction/{file_hash}")
def get_extraction_result(file_hash: str, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing.")

    user = get_user_from_token(authorization.replace("Bearer ", "").strip())
    return get_cached_extraction(file_hash, user)