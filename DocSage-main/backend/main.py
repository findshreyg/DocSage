from fastapi import FastAPI

from api.routes_upload import router as upload_router
from api.routes_download import router as download_router
from conversation_services.main import router as conversation_router
from api.routes_ask import router as ask_router

app = FastAPI()


app.include_router(upload_router, prefix="/upload")
app.include_router(download_router, prefix="/download")
app.include_router(conversation_router, prefix="/conversation_services")
app.include_router(ask_router, prefix="/ask")

@app.get("/")
def health():
    return {"status": "ok"}