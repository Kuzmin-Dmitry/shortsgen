"""
Text Service API - FastAPI приложение для генерации текста
"""

import asyncio
from fastapi import FastAPI
from config import logger
from task_handler import TaskHandler

app = FastAPI(
    title="Text Service API",
    description="Микросервис для генерации текста с Redis очередями",
    version="2.0.0"
)

# Глобальный обработчик задач
task_handler = TaskHandler()


@app.on_event("startup")
async def startup_event():
    """Запуск фонового слушателя задач"""
    logger.info("Starting Text Service...")
    await task_handler.connect()
    asyncio.create_task(task_handler.listen_tasks())


@app.on_event("shutdown")
async def shutdown_event():
    """Закрытие соединений при остановке"""
    logger.info("Shutting down Text Service...")
    await task_handler.disconnect()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "text-service", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Text Service on 0.0.0.0:8002")
    uvicorn.run("app:app", host="0.0.0.0", port=8002, reload=False)
