from fastapi import FastAPI
from api.routes_auth import router as auth_router
from api.routes_upload import router as upload_router
from api.routes_download import router as download_router
from api.routes_conversation import router as conversation_router
from api.routes_ask import router as ask_router

app = FastAPI()

app.include_router(auth_router, prefix="/auth")
app.include_router(upload_router, prefix="/upload")
app.include_router(download_router, prefix="/download")
app.include_router(conversation_router, prefix="/conversation")
app.include_router(ask_router, prefix="/ask")

@app.get("/")
def health():
    return {"status": "ok"}