from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, status
from auth_service.deps import get_current_user
from upload.upload_handler import (
    handle_upload,
    list_user_files,
    delete_user_file
)
from models.schemas import DeleteFileRequest

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    try:
        if not file:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file uploaded.")
        return await handle_upload(file, user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list-uploads")
async def list_uploads(user: dict = Depends(get_current_user)):
    try:
        # If list_user_files is async, await it; otherwise, call directly
        files = list_user_files(user["sub"])
        if files is None or not files:
            return {"message": "No uploads found."}
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete-file")
async def delete_file(payload: DeleteFileRequest, user: dict = Depends(get_current_user)):
    try:
        if not payload.file_hash or payload.file_hash.strip() == "":
            raise HTTPException(status_code=400, detail="file_hash is required.")
        success, message = delete_user_file(user["sub"], payload.file_hash)
        if not success:
            raise HTTPException(status_code=404, detail=message)
        return {"message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))