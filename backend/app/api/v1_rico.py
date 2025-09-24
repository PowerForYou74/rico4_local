# backend/app/api/v1_rico.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Literal

from ..services.orchestrator import RicoOrchestrator

router = APIRouter()
_orch = RicoOrchestrator()

class Task(BaseModel):
    prompt: str
    task_type: Optional[str] = "analysis"
    provider: Optional[Literal["openai", "claude", "perplexity", "auto"]] = "auto"

@router.post("/task")
async def create_task(task: Task):
    result = await _orch.run_rico_loop(
        prompt=task.prompt,
        task_type=task.task_type or "analysis",
        provider=task.provider or "auto",
    )
    return result