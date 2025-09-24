"""
Rico 4.0 - Monitor API
Task-Monitor für Autopilot-Übersicht und -Details
"""

import json
import time
import yaml
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..autopilot import autopilot_manager
from ..services.result_store import read_latest, read_many
from ..services.health_check import health_check_2

router = APIRouter()


class TaskStatus(BaseModel):
    """Task-Status-Modell"""
    id: str
    title: Optional[str] = None
    schedule: str
    enabled: bool
    provider: str
    type: str
    last_run: Optional[str] = None
    last_status: str  # success|error|pending|stale
    last_duration_sec: Optional[float] = None


class MonitorStatus(BaseModel):
    """Monitor-Status-Modell"""
    autopilot_running: bool
    total_tasks: int
    active_tasks: int
    next_runs: List[Dict[str, str]]
    last_updated: str


class TaskLog(BaseModel):
    """Task-Log-Modell"""
    ts: str
    status: str  # success|error
    duration_sec: Optional[float] = None
    provider: Optional[str] = None
    notes: Optional[str] = None
    error: Optional[str] = None


def _get_utc_now() -> str:
    """Gibt aktuelle UTC-Zeit als ISO8601Z zurück"""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _determine_task_status(task_id: str, schedule: str) -> tuple[str, Optional[str], Optional[float]]:
    """
    Bestimmt Task-Status basierend auf letztem Run und Schedule
    
    Returns:
        (status, last_run, duration_sec)
    """
    latest_result = read_latest(task_id)
    
    if not latest_result:
        return "pending", None, None
    
    last_run = latest_result.get("ts")
    duration_sec = latest_result.get("duration_sec")
    
    # Prüfe ob Task stale ist (älter als 2x erwartetes Intervall)
    if last_run:
        try:
            last_run_dt = datetime.fromisoformat(last_run.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            
            # Einfache Stale-Logik: wenn älter als 30 Minuten (default)
            stale_threshold = timedelta(minutes=30)
            if now - last_run_dt > stale_threshold:
                return "stale", last_run, duration_sec
        except Exception:
            pass
    
    # Status basierend auf ok-Flag
    if latest_result.get("ok", False):
        return "success", last_run, duration_sec
    else:
        return "error", last_run, duration_sec


@router.get("/api/monitor/status", response_model=MonitorStatus)
async def get_monitor_status():
    """Gibt aktuellen Monitor-Status zurück"""
    try:
        # Autopilot-Status vom Manager
        autopilot_status = autopilot_manager.get_status()
        
        # Lade Tasks-Konfiguration
        tasks_config_path = Path("data/autopilot/tasks.yaml")
        tasks_config = []
        if tasks_config_path.exists():
            with open(tasks_config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                tasks_config = config.get('tasks', [])
        
        # Berechne Metriken
        total_tasks = len(tasks_config)
        active_tasks = len([t for t in tasks_config if t.get('enabled', False)])
        
        # Next runs (vereinfacht - in echter Implementierung würde man Cron parsen)
        next_runs = []
        for task in tasks_config:
            if task.get('enabled', False):
                # Vereinfachte Next-Run-Logik (in echt würde man Cron parsen)
                next_runs.append({
                    "task_id": task['id'],
                    "next": _get_utc_now()  # Placeholder
                })
        
        return MonitorStatus(
            autopilot_running=autopilot_status.get('running', False),
            total_tasks=total_tasks,
            active_tasks=active_tasks,
            next_runs=next_runs,
            last_updated=_get_utc_now()
        )
        
    except Exception as e:
        # Bei Fehlern leere, aber wohlgeformte Antwort
        return MonitorStatus(
            autopilot_running=False,
            total_tasks=0,
            active_tasks=0,
            next_runs=[],
            last_updated=_get_utc_now()
        )


@router.get("/api/monitor/tasks", response_model=List[TaskStatus])
async def get_monitor_tasks():
    """Gibt alle Tasks mit Status zurück"""
    try:
        # Lade Tasks-Konfiguration
        tasks_config_path = Path("data/autopilot/tasks.yaml")
        if not tasks_config_path.exists():
            return []
            
        with open(tasks_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            tasks_config = config.get('tasks', [])
        
        tasks = []
        for task_config in tasks_config:
            task_id = task_config['id']
            status, last_run, duration_sec = _determine_task_status(
                task_id, 
                task_config.get('schedule', '')
            )
            
            tasks.append(TaskStatus(
                id=task_id,
                title=task_config.get('description'),
                schedule=task_config.get('schedule', ''),
                enabled=task_config.get('enabled', False),
                provider=task_config.get('provider', 'auto'),
                type=task_config.get('task_type', 'analysis'),
                last_run=last_run,
                last_status=status,
                last_duration_sec=duration_sec
            ))
        
        return tasks
        
    except Exception as e:
        # Bei Fehlern leere Liste zurückgeben
        return []


@router.get("/api/monitor/logs", response_model=List[TaskLog])
async def get_monitor_logs(
    task_id: str = Query(..., description="Task-ID"),
    limit: int = Query(50, description="Maximale Anzahl Logs")
):
    """Gibt Task-Logs zurück"""
    try:
        # Lade Results für Task
        results = read_many(task_id, limit)
        
        logs = []
        for result in results:
            logs.append(TaskLog(
                ts=result.get("ts", ""),
                status=result.get("status", "error"),
                duration_sec=result.get("duration_sec"),
                provider=result.get("provider"),
                notes=result.get("notes"),
                error=result.get("error")
            ))
        
        return logs
        
    except Exception as e:
        # Bei Fehlern leere Liste zurückgeben
        return []


@router.get("/api/monitor/health-check")
async def get_health_check():
    """Health-Check 2.0: Mini-Pings für alle Provider"""
    try:
        return await health_check_2.check_all_providers()
    except Exception as e:
        return {
            "timestamp": time.time(),
            "error": str(e),
            "providers": {},
            "summary": {"total": 0, "ok": 0, "n_a": 0, "errors": 1}
        }


@router.get("/api/monitor/check-keys")
async def get_keys_status():
    """Prüft Status der API-Keys (ohne echte Calls)"""
    try:
        return health_check_2.get_keys_status()
    except Exception as e:
        return {
            "error": str(e),
            "openai": {"configured": False, "env_source": "unknown", "model": ""},
            "claude": {"configured": False, "env_source": "unknown", "model": ""},
            "perplexity": {"configured": False, "env_source": "unknown", "model": ""}
        }
