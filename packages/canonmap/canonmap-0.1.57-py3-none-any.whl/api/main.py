from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pathlib import Path

from canonmap import CanonMap
from api.routes import match, generate

app = FastAPI(
    title="CanonMap API",
    description="API for entity matching and artifact generation",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(match, prefix="/api/v1", tags=["matching"])
app.include_router(generate, prefix="/api/v1", tags=["generation"])

@app.get("/")
async def root():
    """Root endpoint that returns API information."""
    return {
        "name": "CanonMap API",
        "version": "1.0.0",
        "description": "API for entity matching and artifact generation",
        "endpoints": {
            "match": "/api/v1/match",
            "generate": "/api/v1/generate"
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 