import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

from config import PROCESSING_SERVICE_URL

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('gateway.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="ShortsGen API Gateway", description="Routes requests to the processing service")

class GenerationRequest(BaseModel):
    custom_prompt: Optional[str] = None
    mock: Optional[bool] = False

class JobStatus(BaseModel):
    job_id: int
    status: str
    message: Optional[str] = None
    output_file: Optional[str] = None

async def _post(endpoint: str, payload: dict) -> dict:
    url = f"{PROCESSING_SERVICE_URL}{endpoint}"
    logger.info(f"Forwarding request to {url}")
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload)
    if resp.status_code >= 400:
        logger.error(f"Error from processing service: {resp.text}")
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

async def _get(endpoint: str) -> dict:
    url = f"{PROCESSING_SERVICE_URL}{endpoint}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
    if resp.status_code >= 400:
        logger.error(f"Error from processing service: {resp.text}")
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

@app.get("/")
async def root():
    return {"status": "online", "service": "API Gateway"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "API Gateway"}

@app.post("/generate", response_model=JobStatus, status_code=202)
async def generate(request: GenerationRequest):
    if request.mock:
        logger.info("Mock mode enabled - simulating generation without actual processing")
        # Возвращаем фиктивный ответ без обращения к processing service
        return JobStatus(
            job_id=999999,
            status="completed",
            message="Mock generation completed successfully",
            output_file="mock_output.mp4"
        )
    
    return await _post("/generate", request.dict())

@app.post("/generateFromInternet", response_model=JobStatus, status_code=202)
async def generate_from_internet(request: GenerationRequest):
    if request.mock:
        logger.info("Mock mode enabled - simulating internet generation without actual processing")
        return JobStatus(
            job_id=999998,
            status="completed", 
            message="Mock internet generation completed successfully",
            output_file="mock_internet_output.mp4"
        )
    
    return await _post("/generateFromInternet", request.dict())

@app.get("/status/{job_id}", response_model=JobStatus)
async def status(job_id: int):
    return await _get(f"/status/{job_id}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_gateway.app:app", host="0.0.0.0", port=8000, reload=False)
