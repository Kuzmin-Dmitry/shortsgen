from fastapi import FastAPI, BackgroundTasks, HTTPException, status
from pydantic import BaseModel
import logging
import os
from services.generator import Generator
from utils.logger import LoggerConfigurator

# Configure logging
logger_configurator = LoggerConfigurator()
logger = logger_configurator.get_logger()

app = FastAPI(title="ShortsGen API", description="API for generating short videos")

# Track job status
jobs = {}
current_job_id = 0

class GenerationRequest(BaseModel):
    """Request model for generation jobs"""
    custom_prompt: str = None  # Optional custom prompt

class JobStatus(BaseModel):
    """Response model for job status"""
    job_id: int
    status: str
    message: str = None
    output_file: str = None

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "online", "service": "ShortsGen API"}

@app.post("/generate", response_model=JobStatus, status_code=status.HTTP_202_ACCEPTED)
async def generate_video(request: GenerationRequest, background_tasks: BackgroundTasks):
    """Start a video generation job"""
    global current_job_id
    job_id = current_job_id
    current_job_id += 1
    
    logger.info(f"Received generation request, assigned job ID: {job_id}")
    
    # Initialize job status
    jobs[job_id] = {
        "status": "queued",
        "message": "Job queued for processing",
        "output_file": None
    }
    
    # Add job to background tasks
    background_tasks.add_task(
        process_generation_job, 
        job_id=job_id, 
        custom_prompt=request.custom_prompt
    )
    
    return JobStatus(
        job_id=job_id,
        status="queued",
        message="Job queued for processing"
    )

@app.post("/generateFromInternet", response_model=JobStatus, status_code=status.HTTP_202_ACCEPTED)
async def generate_from_internet(request: GenerationRequest, background_tasks: BackgroundTasks):
    """Start a video generation job using internet images"""
    global current_job_id
    job_id = current_job_id
    current_job_id += 1
    
    logger.info(f"Received generate from internet request, assigned job ID: {job_id}")
    
    # Initialize job status
    jobs[job_id] = {
        "status": "queued",
        "message": "Job queued for processing",
        "output_file": None
    }
    
    # Add job to background tasks
    background_tasks.add_task(
        process_generation_job, 
        job_id=job_id, 
        custom_prompt=request.custom_prompt,
        use_internet=True
    )
    
    return JobStatus(
        job_id=job_id,
        status="queued",
        message="Job queued for processing"
    )

@app.get("/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: int):
    """Get status of a generation job"""
    if job_id not in jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found"
        )
    
    job = jobs[job_id]
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        message=job["message"],
        output_file=job["output_file"]
    )

def process_generation_job(job_id: int, custom_prompt: str = None, use_internet: bool = False):
    """Process a generation job in the background"""
    try:
        logger.info(f"Starting processing for job {job_id}")
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["message"] = "Video generation in progress"
        
        # Create generator and generate
        generator = Generator()
        
        if use_internet:
            success = generator.find_and_generate()
        else:
            success = generator.generate()
        
        if success:
            # Get the output file path from the configuration
            from config import VIDEO_FILE_PATH
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["message"] = "Video generation completed successfully"
            jobs[job_id]["output_file"] = VIDEO_FILE_PATH
            logger.info(f"Job {job_id} completed successfully")
        else:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["message"] = "Video generation failed"
            logger.error(f"Job {job_id} failed during generation")
    except Exception as e:
        logger.exception(f"Error processing job {job_id}: {str(e)}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = f"Error: {str(e)}"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
