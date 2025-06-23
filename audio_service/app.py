"""
Audio Service API - Clean FastAPI application entry point.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
from fastapi import FastAPI
from config import configure_logging, SERVICE_HOST, SERVICE_PORT
from routes import router

# Configure logging
configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Audio Service API",
    description="Microservice for text-to-speech audio generation operations",
    version="1.0.0"
)

# Include routes
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting Audio Service on {SERVICE_HOST}:{SERVICE_PORT}")
    uvicorn.run("app:app", host=SERVICE_HOST, port=SERVICE_PORT, reload=False)
