from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the router from each service's main.py file
from auth_services.main import router as auth_router
from llm_services.main import router as llm_router
from file_services.main import router as file_router
from conversation_services.main import router as conversation_router

# Create the main FastAPI application
app = FastAPI(title="DocSage Main API")

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include the routers from each service into the main app
app.include_router(auth_router, prefix="/auth", tags=["1. Authentication Service"])
app.include_router(file_router, prefix="/files", tags=["2. File Service"])
app.include_router(llm_router, prefix="/llm", tags=["3. LLM Service"])
app.include_router(conversation_router, prefix="/conversation", tags=["4. Conversation Service"])


@app.get("/", tags=["Health Check"])
def health_check():
    """
    A simple endpoint to confirm the API is running.
    """
    return {"status": "ok", "message": "Welcome to the DocSage API"}