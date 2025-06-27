"""Image Service API - FastAPI приложение для генерации изображений."""

import asyncio
from fastapi import FastAPI
from config import logger
from task_handler import TaskHandler
from routes import router

app = FastAPI(title="Image Service", version="2.0.0")
app.include_router(router)

task_handler = TaskHandler()


@app.on_event("startup")
async def startup_event():
    """Запуск фонового слушателя задач."""
    logger.info("Starting Image Service...")
    await task_handler.connect()
    asyncio.create_task(task_handler.listen_tasks())


@app.on_event("shutdown") 
async def shutdown_event():
    """Закрытие соединений при остановке."""
    logger.info("Shutting down Image Service...")
    await task_handler.disconnect()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "image-service", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Image Service on 0.0.0.0:8005")
    uvicorn.run("app:app", host="0.0.0.0", port=8005, reload=False)
