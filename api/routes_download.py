from fastapi import APIRouter, HTTPException, Depends
from auth_service.deps import get_current_user
from download.download_handler import generate_presigned_url
from models.schemas import DownloadRequest

router = APIRouter()

@router.post("/file")
def download_file(payload: DownloadRequest, user: dict = Depends(get_current_user)):
    try:
        if not payload.file_hash:
            raise HTTPException(status_code=400, detail="file_hash is required.")

        user_id = user["sub"]
        presigned_url = generate_presigned_url(user_id, payload.file_hash)

        if not presigned_url:
            raise HTTPException(status_code=404, detail="File not found or could not generate URL.")

        return {"download_url": presigned_url}

    except HTTPException:
        # Let FastAPI handle the HTTPException as is
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not generate download URL: {str(e)}")