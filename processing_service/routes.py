"""
API routes for processing service.
"""

from fastapi import APIRouter, HTTPException, status
from config import logger
from models import (
    CreateScenarioRequest,
    CreateScenarioResponse,
    TaskStatusUpdate,
    TaskStatus
)
from scenario_generator import ScenarioGenerator
from task_queue import task_queue

router = APIRouter()

# Initialize scenario generator
scenario_generator = ScenarioGenerator()


@router.post(
    "/generate",
    response_model=CreateScenarioResponse,
    status_code=status.HTTP_201_CREATED
)
async def generate_scenario(request: CreateScenarioRequest) -> CreateScenarioResponse:
    """Generate scenario and publish tasks to Redis.
    
    Creates a deterministic task list from scenario template and publishes
    them to Redis queues with proper dependency management.
    
    Args:
        request: Scenario creation request
        
    Returns:
        Response with scenario ID and task count
    """
    try:
        logger.info(
            f"Generating scenario: {request.scenario} "
            f"(description: '{request.description}', slides: {request.slides_count})"
        )
        
        # Generate scenario based on type
        if request.scenario == "CreateVideo":
            scenario = scenario_generator.create_video_scenario(
                description=request.description,
                slides_count=request.slides_count
            )
        elif request.scenario == "CreateVoice":
            scenario = scenario_generator.create_voice_scenario(
                description=request.description
            )
        elif request.scenario == "CreateSlides":
            scenario = scenario_generator.create_slides_scenario(
                base_prompt=request.description,
                slides_count=request.slides_count
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown scenario type: {request.scenario}. Supported types: CreateVideo, CreateVoice, CreateSlides"
            )
        
        # Publish tasks to Redis with dependency management
        tasks_published = await task_queue.publish_tasks(scenario.tasks)
        
        logger.info(
            f"Created scenario {scenario.scenario_id} with {tasks_published} tasks. "
            f"Ready tasks queued for execution."
        )
        
        return CreateScenarioResponse(
            scenario_id=scenario.scenario_id,
            tasks_created=tasks_published,
            status="pending"
        )
        
    except Exception as e:
        logger.error(f"Failed to generate scenario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate scenario: {str(e)}"
        )


@router.get("/scenarios/{scenario_id}")
async def get_scenario_status(scenario_id: str):
    """Get scenario status and task progress.
    
    Args:
        scenario_id: Scenario ID
        
    Returns:
        Scenario status with task details
    """
    try:
        tasks = await task_queue.get_scenario_tasks(scenario_id)
        
        if not tasks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario {scenario_id} not found"
            )
        
        # Calculate status summary
        total_tasks = len(tasks)
        pending_tasks = sum(1 for t in tasks if t.get("status") == "pending")
        processing_tasks = sum(1 for t in tasks if t.get("status") == "processing")
        success_tasks = sum(1 for t in tasks if t.get("status") == "success")
        failed_tasks = sum(1 for t in tasks if t.get("status") == "failed")
        
        # Determine overall status
        if failed_tasks > 0:
            overall_status = "failed"
        elif success_tasks == total_tasks:
            overall_status = "completed"
        elif processing_tasks > 0 or pending_tasks < total_tasks:
            overall_status = "processing"
        else:
            overall_status = "pending"
        
        return {
            "scenario_id": scenario_id,
            "status": overall_status,
            "progress": {
                "total": total_tasks,
                "pending": pending_tasks,
                "processing": processing_tasks,
                "success": success_tasks,
                "failed": failed_tasks
            },
            "tasks": tasks
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scenario status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scenario status: {str(e)}"
        )


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get individual task status.
    
    Args:
        task_id: Task ID
        
    Returns:
        Task details
    """
    try:
        task_data = await task_queue.get_task(task_id)
        
        if not task_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
        
        return task_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.patch("/tasks/{task_id}/status")
async def update_task_status(task_id: str, update: TaskStatusUpdate):
    """Update task status (for microservices).
    
    Args:
        task_id: Task ID
        update: Status update data
        
    Returns:
        Success confirmation
    """
    try:
        await task_queue.update_task_status(
            task_id=task_id,
            status=update.status,
            result_ref=update.result_ref
        )
        
        return {"message": f"Task {task_id} status updated to {update.status.value}"}
        
    except Exception as e:
        logger.error(f"Failed to update task status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task status: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "processing-service"}


@router.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "processing-service",
        "version": "1.0.0",
        "description": "Microservice for scenario generation and task orchestration",
        "endpoints": {
            "POST /generate": "Generate scenario and publish tasks to Redis",
            "GET /scenarios/{id}": "Get scenario status and progress",
            "GET /tasks/{id}": "Get individual task status",
            "PATCH /tasks/{id}/status": "Update task status",
            "GET /health": "Health check"
        }
    }
