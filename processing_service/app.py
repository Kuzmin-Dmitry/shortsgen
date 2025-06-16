from fastapi import FastAPI, BackgroundTasks, HTTPException, status, Depends
from pydantic import BaseModel
from generator import Generator
from config import VIDEO_FILE_PATH
import logging
from typing import Dict, Optional
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('shortsgen.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Processing Service API", description="Background processing service")

# Job status models
class JobStatus(BaseModel):
    """Response model for job status"""
    job_id: int
    status: str
    message: Optional[str] = None
    output_file: Optional[str] = None

class GenerationRequest(BaseModel):
    """Request model for generation jobs"""
    custom_prompt: Optional[str] = None  # Optional custom prompt

@dataclass
class JobData:
    """Internal data structure for job tracking"""
    status: str
    message: str
    output_file: Optional[str] = None

class JobManager:
    """Class responsible for job management and tracking"""
    def __init__(self):
        self.jobs: Dict[int, JobData] = {}
        self.current_job_id: int = 0
    
    def create_job(self) -> int:
        """Create a new job and return its ID"""
        job_id = self.current_job_id
        self.current_job_id += 1

        self.jobs[job_id] = JobData(
            status="queued",
            message="Job queued for processing"
        )

        return job_id

    def get_job(self, job_id: int) -> Optional[JobData]:
        """Get job data by ID"""
        return self.jobs.get(job_id)
    
    def update_job(self, job_id: int, **kwargs) -> None:
        """Update job with provided attributes"""
        if job_id in self.jobs:
            for key, value in kwargs.items():
                if hasattr(self.jobs[job_id], key):
                    setattr(self.jobs[job_id], key, value)

# Create a job manager instance
job_manager = JobManager()

# Dependency for generator service
def get_generator() -> Generator:
    """Dependency injection for the Generator service"""
    return Generator()

# Dependency for job manager
def get_job_manager() -> JobManager:
    """Dependency injection for the JobManager"""
    return job_manager

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "online", "service": "Processing Service"}

@app.post("/generate", response_model=JobStatus, status_code=status.HTTP_202_ACCEPTED)
async def generate_video(
    request: GenerationRequest, 
    background_tasks: BackgroundTasks,
    job_manager: JobManager = Depends(get_job_manager)
):
    """Start a video generation job"""
    job_id = job_manager.create_job()
    logger.info(f"Received generation request, assigned job ID: {job_id}")
      # Add job to background tasks
    background_tasks.add_task(
        process_generation_job, 
        job_id=job_id, 
        custom_prompt=request.custom_prompt,
        use_internet=False,
        job_manager=job_manager
    )
    
    job_data = job_manager.get_job(job_id)
    if job_data is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job"
        )
    return JobStatus(
        job_id=job_id,
        status=job_data.status,
        message=job_data.message
    )

@app.post("/generateFromInternet", response_model=JobStatus, status_code=status.HTTP_202_ACCEPTED)
async def generate_from_internet(
    request: GenerationRequest, 
    background_tasks: BackgroundTasks,
    job_manager: JobManager = Depends(get_job_manager)
):
    """Start a video generation job using internet images"""
    job_id = job_manager.create_job()
    logger.info(f"Received generate from internet request, assigned job ID: {job_id}")
      # Add job to background tasks
    background_tasks.add_task(
        process_generation_job, 
        job_id=job_id, 
        custom_prompt=request.custom_prompt,
        use_internet=True,
        job_manager=job_manager
    )
    
    job_data = job_manager.get_job(job_id)
    if job_data is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job"
        )
    return JobStatus(
        job_id=job_id,
        status=job_data.status,
        message=job_data.message
    )

@app.get("/status/{job_id}", response_model=JobStatus)
async def get_job_status(
    job_id: int,
    job_manager: JobManager = Depends(get_job_manager)
):
    """Get status of a generation job"""
    job_data = job_manager.get_job(job_id)
    if not job_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found"
        )
    
    return JobStatus(
        job_id=job_id,
        status=job_data.status,
        message=job_data.message,
        output_file=job_data.output_file
    )

def process_generation_job(
    job_id: int, 
    custom_prompt: Optional[str] = None, 
    use_internet: bool = False,
    job_manager: Optional[JobManager] = None,
    generator: Optional[Generator] = None
):
    """Process a generation job in the background"""
    if generator is None:
        generator = Generator()
    if job_manager is None:
        raise ValueError("job_manager is required")
        
    try:
        logger.info(f"Starting processing for job {job_id}")
        job_manager.update_job(
            job_id, 
            status="processing",
            message="Video generation in progress"
        )

        # Generate based on the method requested
        if use_internet:
            success = generator.find_and_generate(custom_prompt=custom_prompt)
        else:            # Call generate() without the custom_prompt parameter
            success = generator.generate()
        
        if success:
            # Get the output file path from the configuration
            job_manager.update_job(
                job_id,
                status="completed",
                message="Video generation completed successfully",
                output_file=VIDEO_FILE_PATH
            )
            logger.info(f"Job {job_id} completed successfully")
        else:
            job_manager.update_job(
                job_id,
                status="failed",
                message="Video generation failed"
            )
            logger.error(f"Job {job_id} failed during generation")
    except Exception as e:
        logger.exception(f"Error processing job {job_id}: {str(e)}")
        job_manager.update_job(
            job_id,
            status="failed",
            message=f"Error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=False)
