"""
Processing Service API - Clean FastAPI application entry point.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from config import logger
from routes import router
from task_queue import task_queue


async def start_background_worker():
    """Start background task processor."""
    # Connect to Redis
    await task_queue.connect()
    logger.info("Background worker started")


async def stop_background_worker():
    """Stop background task processor."""
    # Disconnect from Redis
    await task_queue.disconnect()
    logger.info("Background worker stopped")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - start/stop background workers."""
    # Startup
    logger.info("Starting background task processor...")
    await start_background_worker()
    
    try:
        yield
    finally:
        # Shutdown
        logger.info("Stopping background task processor...")
        await stop_background_worker()


app = FastAPI(
    title="Processing Service API",
    description="Microservice for content processing operations",
    version="1.0.0",
    lifespan=lifespan,
)

# Include routes
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Processing Service on 0.0.0.0:8001")
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=False)
