# backend/autopilot/metrics.py
"""
Autopilot Metrics - Telemetrie und KPI-Erfassung
Erfasst Runs, Errors, Latency, Win-Rate, Business-KPIs
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from sqlmodel import SQLModel, Field, create_engine, Session, select
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, Text, JSON
import os

# ------------------------------------------------------------
# Datenmodelle
# ------------------------------------------------------------

class AutopilotMetrics(SQLModel, table=True):
    """Metriken-Tabelle für Autopilot"""
    __tablename__ = "autopilot_metrics"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    task: str = Field(index=True)  # z.B. "ai_ask", "kb_search", "prompt_optimization"
    provider: str = Field(index=True)  # "openai", "claude", "perplexity", "auto_race"
    latency_ms: float
    cost_est: float = Field(default=0.0)  # Geschätzte Kosten in USD
    quality_score: Optional[float] = None  # 0.0-1.0, optional
    win: Optional[bool] = None  # True wenn dieser Run gewonnen hat
    error_type: Optional[str] = None  # "timeout", "rate_limit", "api_error", etc.
    run_id: str = Field(index=True)  # Eindeutige Run-ID
    experiment_id: Optional[str] = Field(default=None, index=True)  # A/B Test ID
    metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))  # Zusätzliche Daten

class AutopilotExperiments(SQLModel, table=True):
    """Experimente-Tabelle für A/B Tests"""
    __tablename__ = "autopilot_experiments"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    experiment_id: str = Field(unique=True, index=True)
    name: str
    type: str = Field(index=True)  # "ab", "prompt", "routing"
    variants: Dict[str, Any] = Field(sa_column=Column(JSON))
    traffic_split: Dict[str, float] = Field(sa_column=Column(JSON))
    start_ts: datetime
    stop_ts: Optional[datetime] = None
    status: str = Field(default="draft", index=True)  # "draft", "running", "stopped", "completed"
    guardrails: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    success_criteria: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ------------------------------------------------------------
# Metrics Writer
# ------------------------------------------------------------

class MetricsWriter:
    """Schreibt Metriken in die Datenbank"""
    
    def __init__(self, db_url: str = None):
        if db_url is None:
            # Verwende bestehende DB oder erstelle neue
            db_path = os.getenv("DATABASE_URL", "sqlite:///rico_ops_v2.db")
            self.engine = create_engine(db_path)
        else:
            self.engine = create_engine(db_url)
        
        # Tabellen erstellen
        SQLModel.metadata.create_all(self.engine)
    
    def log_run(self, 
                 task: str,
                 provider: str, 
                 latency_ms: float,
                 cost_est: float = 0.0,
                 quality_score: Optional[float] = None,
                 win: Optional[bool] = None,
                 error_type: Optional[str] = None,
                 run_id: Optional[str] = None,
                 experiment_id: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None) -> str:
        """Loggt einen Run"""
        
        if run_id is None:
            run_id = f"{task}_{provider}_{int(time.time() * 1000)}"
        
        metric = AutopilotMetrics(
            task=task,
            provider=provider,
            latency_ms=latency_ms,
            cost_est=cost_est,
            quality_score=quality_score,
            win=win,
            error_type=error_type,
            run_id=run_id,
            experiment_id=experiment_id,
            metadata=metadata or {}
        )
        
        with Session(self.engine) as session:
            session.add(metric)
            session.commit()
            session.refresh(metric)
        
        return run_id
    
    def get_metrics_summary(self, 
                           hours: int = 24,
                           task: Optional[str] = None,
                           provider: Optional[str] = None) -> Dict[str, Any]:
        """Gibt Metriken-Zusammenfassung zurück"""
        
        since = datetime.utcnow() - timedelta(hours=hours)
        
        with Session(self.engine) as session:
            query = select(AutopilotMetrics).where(AutopilotMetrics.timestamp >= since)
            
            if task:
                query = query.where(AutopilotMetrics.task == task)
            if provider:
                query = query.where(AutopilotMetrics.provider == provider)
            
            metrics = session.exec(query).all()
            
            if not metrics:
                return {
                    "total_runs": 0,
                    "avg_latency_ms": 0,
                    "total_cost": 0,
                    "error_rate": 0,
                    "win_rate": 0,
                    "avg_quality_score": 0
                }
            
            total_runs = len(metrics)
            successful_runs = [m for m in metrics if m.error_type is None]
            error_rate = (total_runs - len(successful_runs)) / total_runs if total_runs > 0 else 0
            
            avg_latency = sum(m.latency_ms for m in metrics) / total_runs
            total_cost = sum(m.cost_est for m in metrics)
            
            quality_scores = [m.quality_score for m in metrics if m.quality_score is not None]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            
            wins = [m for m in metrics if m.win is True]
            win_rate = len(wins) / total_runs if total_runs > 0 else 0
            
            return {
                "total_runs": total_runs,
                "avg_latency_ms": round(avg_latency, 2),
                "total_cost": round(total_cost, 4),
                "error_rate": round(error_rate, 3),
                "win_rate": round(win_rate, 3),
                "avg_quality_score": round(avg_quality, 3)
            }

# ------------------------------------------------------------
# Globale Instanz
# ------------------------------------------------------------

_metrics_writer: Optional[MetricsWriter] = None

def get_metrics_writer() -> MetricsWriter:
    """Singleton für MetricsWriter"""
    global _metrics_writer
    if _metrics_writer is None:
        _metrics_writer = MetricsWriter()
    return _metrics_writer

# ------------------------------------------------------------
# Hook-Funktionen für bestehende APIs
# ------------------------------------------------------------

def hook_ai_ask_start(task: str, provider: str, run_id: str = None) -> str:
    """Hook für Start eines AI-Asks"""
    if run_id is None:
        run_id = f"ai_ask_{provider}_{int(time.time() * 1000)}"
    return run_id

def hook_ai_ask_end(run_id: str, 
                   latency_ms: float,
                   cost_est: float = 0.0,
                   quality_score: Optional[float] = None,
                   win: bool = None,
                   error_type: Optional[str] = None,
                   experiment_id: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None):
    """Hook für Ende eines AI-Asks"""
    
    # Extrahiere Task und Provider aus run_id
    parts = run_id.split("_")
    if len(parts) >= 3:
        task = "_".join(parts[:-2])
        provider = parts[-2]
    else:
        task = "ai_ask"
        provider = "unknown"
    
    get_metrics_writer().log_run(
        task=task,
        provider=provider,
        latency_ms=latency_ms,
        cost_est=cost_est,
        quality_score=quality_score,
        win=win,
        error_type=error_type,
        run_id=run_id,
        experiment_id=experiment_id,
        metadata=metadata
    )
