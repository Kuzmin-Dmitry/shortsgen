from datetime import datetime
from uuid import uuid4, UUID

from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse

from models import ScenarioTemplate, TaskOut
from task_queue import RedisQueue

# --- DI-singletons ----------------------------------------------------------
queue = RedisQueue()

# --- Константные шаблоны ----------------------------------------------------
SCENARIO_TEMPLATES: dict[str, ScenarioTemplate] = {
    "CreateVoice": ScenarioTemplate(
        name="CreateVoice", tasks=["GenerateText", "GenerateVoiceFromText"]
    ),
    "CreateText": ScenarioTemplate(
        name="CreateText", tasks=["GenerateText"]
    ),
    "CreateVideoFromImages": ScenarioTemplate(
        name="CreateVideoFromImages", tasks=["GenerateText", "GenerateVoiceFromText", "GenerateImages", "GenerateVideoFromImages"]
    ),
    "CreateImage": ScenarioTemplate(
        name="CreateImage", tasks=["GenerateImage"]
    )
}

# --- Router -----------------------------------------------------------------
router = APIRouter()


@router.post("/generate")
async def generate(scenario: str = Body(embed=True)):
    """
    Создаём новый Scenario instance и нужные таски. Складываем таски в очередь.
    """
    template = SCENARIO_TEMPLATES.get(scenario)
    if not template:
        raise HTTPException(status_code=404, detail="Scenario template not found")
    
    scenario_id = uuid4()
    created_tasks = []

    for task_name in template.tasks:
        task = TaskOut(scenario_id=scenario_id, name=task_name)
        await queue.save_task(task)
        await queue.push(task)
        created_tasks.append(task)

    return JSONResponse(
        status_code=201,
        content={
            "scenario_id": str(scenario_id),
            "tasks": [t.model_dump(mode="json") for t in created_tasks],
        },
    )


@router.get("/getScenario/{scenario_id}")
async def get_scenario(scenario_id: UUID):
    """
    Возвращаем все задачи по scenario_id.
    """
    tasks = await queue.get_tasks_by_scenario(scenario_id)
    if not tasks:
        raise HTTPException(404, "Scenario not found")
    return [t.model_dump(mode="json") for t in tasks]


@router.get("/getTask/{task_id}")
async def get_task(task_id: UUID):
    """
    Возвращаем конкретную задачу.
    """
    task = await queue.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task.model_dump(mode="json")


@router.get("/health")
async def healthcheck():
    """
    Health check endpoint.
    """
    return {"status": "ok", "ts": datetime.utcnow().isoformat()}
