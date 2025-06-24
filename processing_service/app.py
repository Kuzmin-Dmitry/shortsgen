"""
Processing Service API - Clean FastAPI application entry point.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from config import logger
from routes import router

app = FastAPI(
    title="Processing Service API",
    description="Microservice for content processing operations",
    version="1.0.0"
)

# Include routes
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Processing Service on 0.0.0.0:8001")
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=False)
