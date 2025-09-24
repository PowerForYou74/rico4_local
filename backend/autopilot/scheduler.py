# backend/autopilot/scheduler.py
"""
Autopilot Scheduler - Job Scheduling und Orchestrierung
Verwaltet zyklische Jobs für Autopilot
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import threading
import logging

# ------------------------------------------------------------
# Enums
# ------------------------------------------------------------

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobType(Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"

# ------------------------------------------------------------
# Datenmodelle
# ------------------------------------------------------------

@dataclass
class JobResult:
    """Ergebnis eines Jobs"""
    job_id: str
    status: JobStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.end_time and self.start_time:
            self.duration_seconds = (self.end_time - self.start_time).total_seconds()

@dataclass
class ScheduledJob:
    """Geplanter Job"""
    id: str
    name: str
    job_type: JobType
    function: Callable
    interval_seconds: int
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    enabled: bool = True
    max_retries: int = 3
    timeout_seconds: int = 300
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.next_run is None:
            self.next_run = datetime.utcnow() + timedelta(seconds=self.interval_seconds)

# ------------------------------------------------------------
# Job Scheduler
# ------------------------------------------------------------

class JobScheduler:
    """Verwaltet geplante Jobs"""
    
    def __init__(self):
        self.jobs: Dict[str, ScheduledJob] = {}
        self.results: List[JobResult] = []
        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.logger = logging.getLogger(__name__)
        
        # Standard-Jobs registrieren
        self._register_default_jobs()
    
    def _register_default_jobs(self):
        """Registriert Standard-Autopilot-Jobs"""
        
        # Stündliche Metriken-Rollups
        self.add_job(
            id="hourly_metrics_rollup",
            name="Hourly Metrics Rollup",
            job_type=JobType.HOURLY,
            function=self._hourly_metrics_rollup,
            interval_seconds=3600  # 1 Stunde
        )
        
        # Tägliche Experiment-Auswertung
        self.add_job(
            id="daily_experiments_tick",
            name="Daily Experiments Tick",
            job_type=JobType.DAILY,
            function=self._daily_experiments_tick,
            interval_seconds=86400  # 24 Stunden
        )
        
        # Wöchentliche Prompt-Review
        self.add_job(
            id="weekly_prompt_review",
            name="Weekly Prompt Review",
            job_type=JobType.WEEKLY,
            function=self._weekly_prompt_review,
            interval_seconds=604800  # 7 Tage
        )
        
        # Tägliche Knowledge-Base Ingest
        self.add_job(
            id="daily_kb_ingest",
            name="Daily Knowledge Base Ingest",
            job_type=JobType.DAILY,
            function=self._daily_kb_ingest,
            interval_seconds=86400  # 24 Stunden
        )
    
    def add_job(self, 
                id: str,
                name: str,
                job_type: JobType,
                function: Callable,
                interval_seconds: int,
                enabled: bool = True,
                max_retries: int = 3,
                timeout_seconds: int = 300,
                metadata: Dict[str, Any] = None) -> bool:
        """Fügt neuen Job hinzu"""
        
        if id in self.jobs:
            self.logger.warning(f"Job {id} already exists, updating...")
        
        job = ScheduledJob(
            id=id,
            name=name,
            job_type=job_type,
            function=function,
            interval_seconds=interval_seconds,
            enabled=enabled,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
            metadata=metadata or {}
        )
        
        self.jobs[id] = job
        self.logger.info(f"Added job: {name} ({job_type.value})")
        return True
    
    def remove_job(self, job_id: str) -> bool:
        """Entfernt Job"""
        
        if job_id not in self.jobs:
            return False
        
        del self.jobs[job_id]
        self.logger.info(f"Removed job: {job_id}")
        return True
    
    def enable_job(self, job_id: str) -> bool:
        """Aktiviert Job"""
        
        if job_id not in self.jobs:
            return False
        
        self.jobs[job_id].enabled = True
        self.logger.info(f"Enabled job: {job_id}")
        return True
    
    def disable_job(self, job_id: str) -> bool:
        """Deaktiviert Job"""
        
        if job_id not in self.jobs:
            return False
        
        self.jobs[job_id].enabled = False
        self.logger.info(f"Disabled job: {job_id}")
        return True
    
    def start_scheduler(self):
        """Startet den Scheduler"""
        
        if self.running:
            self.logger.warning("Scheduler already running")
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        self.logger.info("Scheduler started")
    
    def stop_scheduler(self):
        """Stoppt den Scheduler"""
        
        if not self.running:
            return
        
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        self.logger.info("Scheduler stopped")
    
    def _scheduler_loop(self):
        """Hauptschleife des Schedulers"""
        
        while self.running:
            try:
                current_time = datetime.utcnow()
                
                # Prüfe alle Jobs
                for job in self.jobs.values():
                    if not job.enabled:
                        continue
                    
                    if job.next_run and current_time >= job.next_run:
                        # Job ist fällig
                        self._execute_job(job)
                
                # Warte 60 Sekunden bis zur nächsten Prüfung
                time.sleep(60)
                
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)
    
    def _execute_job(self, job: ScheduledJob):
        """Führt einen Job aus"""
        
        self.logger.info(f"Executing job: {job.name}")
        
        # Erstelle Job-Result
        result = JobResult(
            job_id=job.id,
            status=JobStatus.RUNNING,
            start_time=datetime.utcnow()
        )
        
        try:
            # Führe Job aus
            job_data = job.function()
            
            # Job erfolgreich
            result.status = JobStatus.COMPLETED
            result.end_time = datetime.utcnow()
            result.result_data = job_data
            
            # Aktualisiere Job-Zeiten
            job.last_run = result.start_time
            job.next_run = datetime.utcnow() + timedelta(seconds=job.interval_seconds)
            
            self.logger.info(f"Job {job.name} completed successfully")
            
        except Exception as e:
            # Job fehlgeschlagen
            result.status = JobStatus.FAILED
            result.end_time = datetime.utcnow()
            result.error_message = str(e)
            
            self.logger.error(f"Job {job.name} failed: {e}")
        
        # Speichere Result
        self.results.append(result)
        
        # Behalte nur die letzten 1000 Results
        if len(self.results) > 1000:
            self.results = self.results[-1000:]
    
    def run_job_now(self, job_id: str) -> Optional[JobResult]:
        """Führt einen Job sofort aus"""
        
        if job_id not in self.jobs:
            return None
        
        job = self.jobs[job_id]
        self._execute_job(job)
        
        # Gib das letzte Result zurück
        return self.results[-1] if self.results else None
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Gibt Status eines Jobs zurück"""
        
        if job_id not in self.jobs:
            return None
        
        job = self.jobs[job_id]
        
        # Finde letztes Result
        last_result = None
        for result in reversed(self.results):
            if result.job_id == job_id:
                last_result = result
                break
        
        return {
            "job_id": job_id,
            "name": job.name,
            "enabled": job.enabled,
            "last_run": job.last_run.isoformat() if job.last_run else None,
            "next_run": job.next_run.isoformat() if job.next_run else None,
            "last_status": last_result.status.value if last_result else None,
            "last_duration": last_result.duration_seconds if last_result else None,
            "last_error": last_result.error_message if last_result else None
        }
    
    def get_all_jobs_status(self) -> List[Dict[str, Any]]:
        """Gibt Status aller Jobs zurück"""
        
        return [self.get_job_status(job_id) for job_id in self.jobs.keys()]
    
    def get_recent_results(self, limit: int = 50) -> List[JobResult]:
        """Gibt letzte Job-Results zurück"""
        
        return sorted(self.results, key=lambda r: r.start_time, reverse=True)[:limit]

# ------------------------------------------------------------
# Standard Autopilot Jobs
# ------------------------------------------------------------

class AutopilotJobs:
    """Standard-Jobs für Autopilot"""
    
    @staticmethod
    def _hourly_metrics_rollup() -> Dict[str, Any]:
        """Stündliche Metriken-Rollups"""
        from .metrics import get_metrics_writer
        
        try:
            writer = get_metrics_writer()
            
            # Hole Metriken der letzten Stunde
            summary = writer.get_metrics_summary(hours=1)
            
            # Rollup-Logik (vereinfacht)
            rollup_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "period": "hourly",
                "metrics": summary,
                "status": "completed"
            }
            
            return rollup_data
            
        except Exception as e:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "period": "hourly",
                "status": "failed",
                "error": str(e)
            }
    
    @staticmethod
    def _daily_experiments_tick() -> Dict[str, Any]:
        """Tägliche Experiment-Auswertung"""
        from .experiments import get_experiment_scheduler
        
        try:
            scheduler = get_experiment_scheduler()
            
            # Führe tägliche Auswertung durch
            report = scheduler.schedule_daily_evaluation()
            
            return report
            
        except Exception as e:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "failed",
                "error": str(e)
            }
    
    @staticmethod
    def _weekly_prompt_review() -> Dict[str, Any]:
        """Wöchentliche Prompt-Review"""
        from .registry import get_prompt_registry
        from .optimizer import get_multi_optimizer
        
        try:
            prompt_registry = get_prompt_registry()
            optimizer = get_multi_optimizer()
            
            # Hole alle aktiven Prompts
            active_prompts = prompt_registry.list_prompts(status=PromptStatus.ACTIVE)
            
            review_results = {
                "timestamp": datetime.utcnow().isoformat(),
                "period": "weekly",
                "prompts_reviewed": len(active_prompts),
                "recommendations": []
            }
            
            # Review-Logik (vereinfacht)
            for prompt in active_prompts:
                # Hier würde man echte Optimierung durchführen
                review_results["recommendations"].append({
                    "prompt_id": prompt.id,
                    "name": prompt.name,
                    "action": "no_change_needed"
                })
            
            return review_results
            
        except Exception as e:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "period": "weekly",
                "status": "failed",
                "error": str(e)
            }
    
    @staticmethod
    def _daily_kb_ingest() -> Dict[str, Any]:
        """Tägliche Knowledge-Base Ingest"""
        from .knowledge import get_ingest_manager
        
        try:
            ingest_manager = get_ingest_manager()
            
            # Führe tägliche Ingest durch
            results = ingest_manager.run_daily_ingest()
            
            return results
            
        except Exception as e:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "failed",
                "error": str(e)
            }

# ------------------------------------------------------------
# Scheduler Manager
# ------------------------------------------------------------

class SchedulerManager:
    """Verwaltet den Autopilot-Scheduler"""
    
    def __init__(self):
        self.scheduler = JobScheduler()
        self.logger = logging.getLogger(__name__)
    
    def start_autopilot_scheduler(self):
        """Startet den Autopilot-Scheduler"""
        
        self.logger.info("Starting Autopilot Scheduler...")
        
        # Starte Scheduler
        self.scheduler.start_scheduler()
        
        self.logger.info("Autopilot Scheduler started successfully")
    
    def stop_autopilot_scheduler(self):
        """Stoppt den Autopilot-Scheduler"""
        
        self.logger.info("Stopping Autopilot Scheduler...")
        
        # Stoppe Scheduler
        self.scheduler.stop_scheduler()
        
        self.logger.info("Autopilot Scheduler stopped")
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Gibt Scheduler-Status zurück"""
        
        return {
            "running": self.scheduler.running,
            "jobs_count": len(self.scheduler.jobs),
            "enabled_jobs": len([j for j in self.scheduler.jobs.values() if j.enabled]),
            "jobs": self.scheduler.get_all_jobs_status(),
            "recent_results": [
                {
                    "job_id": r.job_id,
                    "status": r.status.value,
                    "start_time": r.start_time.isoformat(),
                    "duration": r.duration_seconds,
                    "error": r.error_message
                }
                for r in self.scheduler.get_recent_results(limit=10)
            ]
        }
    
    def run_job_manually(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Führt Job manuell aus"""
        
        result = self.scheduler.run_job_now(job_id)
        
        if result:
            return {
                "job_id": result.job_id,
                "status": result.status.value,
                "start_time": result.start_time.isoformat(),
                "end_time": result.end_time.isoformat() if result.end_time else None,
                "duration": result.duration_seconds,
                "result_data": result.result_data,
                "error": result.error_message
            }
        
        return None

# ------------------------------------------------------------
# Globale Instanzen
# ------------------------------------------------------------

_scheduler_manager: Optional[SchedulerManager] = None

def get_scheduler_manager() -> SchedulerManager:
    global _scheduler_manager
    if _scheduler_manager is None:
        _scheduler_manager = SchedulerManager()
    return _scheduler_manager

def start_autopilot_scheduler():
    """Startet den Autopilot-Scheduler (für main.py)"""
    manager = get_scheduler_manager()
    manager.start_autopilot_scheduler()

def stop_autopilot_scheduler():
    """Stoppt den Autopilot-Scheduler (für main.py)"""
    manager = get_scheduler_manager()
    manager.stop_autopilot_scheduler()
