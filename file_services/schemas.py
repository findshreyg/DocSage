from pydantic import BaseModel

class DeleteFileRequest(BaseModel):
    file_hash: str

class DownloadFileRequest(BaseModel):
    file_hash: str
