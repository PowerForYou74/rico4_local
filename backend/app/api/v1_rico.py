from fastapi import APIRouter
from pydantic import BaseModel
from app.services.orchestrator import RicoOrchestrator

router = APIRouter()
_orch = RicoOrchestrator()

from typing import Optional

class Task(BaseModel):
    prompt: str
    task_type: Optional[str] = "analysis"

@router.post("/task")
def create_task(task: Task):
    result = _orch.run_rico_loop(task.prompt)
    return {"ok": True, "task_type": task.task_type, "result": result}