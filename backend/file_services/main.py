from fastapi import FastAPI, HTTPException, File, status, Header, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import logging
from typing import List

from file_handler import handle_upload, list_user_files, delete_user_file, generate_presigned_url
from schemas import (
    DeleteFileRequest, DownloadFileRequest, UploadResponse, 
    FileListResponse, DownloadResponse, MessageResponse
)
from utils import get_user_from_token

app = FastAPI(
    title="DocSage File Service",
    description="File Upload, Management, and Download API",
    version="1.1.0"
)

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

@app.get("/file/health")
def health():
    """Health check endpoint for the file service."""
    return {"health": "All Good"}

@app.post("/file/upload", status_code=status.HTTP_201_CREATED, response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...), authorization: str = Header(None)) -> UploadResponse:
    """Upload a file for the authenticated user."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing.")
    
    access_token = authorization.replace("Bearer ", "").strip()
    try:
        user = get_user_from_token(access_token)
    except Exception as e:
        logger.warning(f"Token validation failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")
    
    # Validate file type
    allowed_extensions = {'.pdf', '.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls', '.txt'}
    file_ext = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Validate file size (50MB limit)
    max_size = 50 * 1024 * 1024  # 50MB
    if file.size and file.size > max_size:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 50MB.")
    
    try:
        result = await handle_upload(file, user)
        logger.info(f"File uploaded successfully: {file.filename} by user {user.get('Username')}")
        return UploadResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during file upload: {e}")
        raise HTTPException(status_code=500, detail="Unexpected server error during file upload.")

@app.get("/file/list-uploads")
async def list_uploads(authorization: str = Header(None)):
    """List all files uploaded by the authenticated user."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing.")
    access_token = authorization.replace("Bearer ", "").strip()
    try:
        user = get_user_from_token(access_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    try:
        files = list_user_files(user["Username"])
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch uploaded files.")
    if not files:
        return {"message": "No uploads found."}
    return {"files": files}

@app.delete("/file/delete-file")
async def delete_file(payload: DeleteFileRequest, authorization: str = Header(None)):
    """Delete a specific file and its metadata for the authenticated user."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing.")
    access_token = authorization.replace("Bearer ", "").strip()
    try:
        user = get_user_from_token(access_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    if not payload.file_hash or payload.file_hash.strip() == "":
        raise HTTPException(status_code=400, detail="file_hash is required.")
    try:
        success, message = delete_user_file(user["Username"], payload.file_hash)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete file.")
    if not success:
        raise HTTPException(status_code=404, detail=message)
    return {"message": message}

@app.post("/file/download", status_code=status.HTTP_200_OK)
async def download_file(payload: DownloadFileRequest, authorization: str = Header(None)):
    """Generate a secure download link (presigned URL) for a file."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing.")
    access_token = authorization.replace("Bearer ", "").strip()
    try:
        user = get_user_from_token(access_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    if not payload.file_hash or payload.file_hash.strip() == "":
        raise HTTPException(status_code=400, detail="file_hash is required.")
    try:
        url = generate_presigned_url(user["Username"], payload.file_hash)
        return {"url": url}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate download link.")
