from fastapi import FastAPI, HTTPException, File, status, Header, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from .file_handler import handle_upload, list_user_files, delete_user_file, generate_presigned_url
from .schemas import DeleteFileRequest, DownloadFileRequest
from .utils import get_user_from_token

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/file/health")
def health():
    return {"health": "All Good"}

@app.post("/file/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...), authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing.")
    access_token = authorization.replace("Bearer ", "").strip()
    try:
        user = get_user_from_token(access_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    if not file:
        raise HTTPException(status_code=400, detail="No file provided.")
    try:
        # THIS IS THE ONLY LINE THAT CHANGES
        result = await handle_upload(file, user, authorization)
        return result
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected server error during file upload.")

# ... (all your other original endpoints for this file) ...
@app.get("/file/list-uploads")
async def list_uploads(authorization: str = Header(None)):
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