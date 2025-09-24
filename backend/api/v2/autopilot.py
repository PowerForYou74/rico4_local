# backend/api/v2/autopilot.py
"""
Autopilot REST API - /v2/autopilot/...
REST-Endpoints für Autopilot-Funktionalität
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel

# Import Autopilot Module
from ...autopilot.metrics import get_metrics_writer, hook_ai_ask_start, hook_ai_ask_end
from ...autopilot.evaluator import get_quality_scorer, get_ab_analyzer, get_baseline_manager
from ...autopilot.optimizer import get_prompt_optimizer, get_routing_optimizer, get_multi_optimizer
from ...autopilot.experiments import get_experiment_manager, get_traffic_manager, get_experiment_scheduler
from ...autopilot.knowledge import get_kb_manager, get_ingest_manager
from ...autopilot.registry import get_prompt_registry, get_policy_registry
from ...autopilot.scheduler import get_scheduler_manager

router = APIRouter(prefix="/v2/autopilot", tags=["autopilot"])

# ------------------------------------------------------------
# Pydantic Models
# ------------------------------------------------------------

class MetricsRequest(BaseModel):
    task: str
    provider: str
    latency_ms: float
    cost_est: float = 0.0
    quality_score: Optional[float] = None
    win: Optional[bool] = None
    error_type: Optional[str] = None
    run_id: Optional[str] = None
    experiment_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ExperimentConfig(BaseModel):
    name: str
    type: str  # "ab", "prompt", "routing"
    variants: Dict[str, Any]
    traffic_split: Dict[str, float]
    duration_hours: int = 24
    min_samples: int = 100
    success_criteria: Optional[Dict[str, Any]] = None
    guardrails: Optional[Dict[str, Any]] = None

class PromptVariant(BaseModel):
    id: str
    name: str
    content: str
    role: str = "system"
    tags: List[str] = []

class RoutingPolicy(BaseModel):
    id: str
    name: str
    weights: Dict[str, float]
    conditions: Dict[str, Any]

# ------------------------------------------------------------
# Status & Health
# ------------------------------------------------------------

@router.get("/status")
async def get_autopilot_status():
    """Gibt Autopilot-Status zurück"""
    
    try:
        # Hole Scheduler-Status
        scheduler_manager = get_scheduler_manager()
        scheduler_status = scheduler_manager.get_scheduler_status()
        
        # Hole Experiment-Status
        experiment_manager = get_experiment_manager()
        running_experiments = experiment_manager.list_experiments(status="running")
        
        # Hole Knowledge-Base Status
        kb_manager = get_kb_manager()
        kb_stats = kb_manager.get_knowledge_stats()
        
        # Hole letzte Ingest
        ingest_manager = get_ingest_manager()
        last_ingest = ingest_manager.get_knowledge_stats()
        
        return {
            "enabled": True,
            "timestamp": datetime.utcnow().isoformat(),
            "scheduler": {
                "running": scheduler_status["running"],
                "jobs_count": scheduler_status["jobs_count"],
                "enabled_jobs": scheduler_status["enabled_jobs"]
            },
            "experiments": {
                "running_count": len(running_experiments),
                "experiments": [
                    {
                        "experiment_id": exp.experiment_id,
                        "status": exp.status,
                        "start_time": exp.start_time.isoformat() if exp.start_time else None
                    }
                    for exp in running_experiments
                ]
            },
            "knowledge_base": {
                "total_sources": kb_stats.get("total_sources", 0),
                "total_chunks": kb_stats.get("total_chunks", 0),
                "total_summaries": kb_stats.get("total_summaries", 0)
            },
            "last_ingest": last_ingest.get("timestamp", "never")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting autopilot status: {str(e)}")

@router.get("/health")
async def get_autopilot_health():
    """Gibt detaillierte Health-Informationen zurück"""
    
    try:
        # Prüfe alle Komponenten
        components = {}
        
        # Metrics Writer
        try:
            writer = get_metrics_writer()
            components["metrics"] = {"status": "ok", "message": "Metrics writer available"}
        except Exception as e:
            components["metrics"] = {"status": "error", "message": str(e)}
        
        # Experiment Manager
        try:
            exp_manager = get_experiment_manager()
            components["experiments"] = {"status": "ok", "message": "Experiment manager available"}
        except Exception as e:
            components["experiments"] = {"status": "error", "message": str(e)}
        
        # Knowledge Base
        try:
            kb_manager = get_kb_manager()
            components["knowledge"] = {"status": "ok", "message": "Knowledge base available"}
        except Exception as e:
            components["knowledge"] = {"status": "error", "message": str(e)}
        
        # Registry
        try:
            prompt_registry = get_prompt_registry()
            policy_registry = get_policy_registry()
            components["registry"] = {"status": "ok", "message": "Registry available"}
        except Exception as e:
            components["registry"] = {"status": "error", "message": str(e)}
        
        # Scheduler
        try:
            scheduler_manager = get_scheduler_manager()
            components["scheduler"] = {"status": "ok", "message": "Scheduler available"}
        except Exception as e:
            components["scheduler"] = {"status": "error", "message": str(e)}
        
        # Gesamtstatus
        all_ok = all(comp["status"] == "ok" for comp in components.values())
        
        return {
            "overall_status": "healthy" if all_ok else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "components": components
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting autopilot health: {str(e)}")

# ------------------------------------------------------------
# Metrics
# ------------------------------------------------------------

@router.post("/metrics")
async def log_metrics(metrics: MetricsRequest):
    """Loggt Metriken"""
    
    try:
        writer = get_metrics_writer()
        
        run_id = writer.log_run(
            task=metrics.task,
            provider=metrics.provider,
            latency_ms=metrics.latency_ms,
            cost_est=metrics.cost_est,
            quality_score=metrics.quality_score,
            win=metrics.win,
            error_type=metrics.error_type,
            run_id=metrics.run_id,
            experiment_id=metrics.experiment_id,
            metadata=metrics.metadata
        )
        
        return {"status": "success", "run_id": run_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error logging metrics: {str(e)}")

@router.post("/metrics/rollup")
async def rollup_metrics():
    """Führt Metriken-Rollup durch"""
    
    try:
        writer = get_metrics_writer()
        
        # Hole verschiedene Zeiträume
        rollups = {
            "hourly": writer.get_metrics_summary(hours=1),
            "daily": writer.get_metrics_summary(hours=24),
            "weekly": writer.get_metrics_summary(hours=168)
        }
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "rollups": rollups
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rolling up metrics: {str(e)}")

@router.get("/metrics/summary")
async def get_metrics_summary(
    hours: int = Query(24, description="Hours to look back"),
    task: Optional[str] = Query(None, description="Filter by task"),
    provider: Optional[str] = Query(None, description="Filter by provider")
):
    """Gibt Metriken-Zusammenfassung zurück"""
    
    try:
        writer = get_metrics_writer()
        
        summary = writer.get_metrics_summary(
            hours=hours,
            task=task,
            provider=provider
        )
        
        return {
            "status": "success",
            "summary": summary,
            "filters": {
                "hours": hours,
                "task": task,
                "provider": provider
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting metrics summary: {str(e)}")

# ------------------------------------------------------------
# Experiments
# ------------------------------------------------------------

@router.post("/experiments")
async def create_experiment(config: ExperimentConfig):
    """Erstellt neues Experiment"""
    
    try:
        from ...autopilot.experiments import ExperimentConfig as ExpConfig
        
        exp_config = ExpConfig(
            name=config.name,
            type=config.type,
            variants=config.variants,
            traffic_split=config.traffic_split,
            duration_hours=config.duration_hours,
            min_samples=config.min_samples,
            success_criteria=config.success_criteria,
            guardrails=config.guardrails
        )
        
        experiment_manager = get_experiment_manager()
        experiment_id = experiment_manager.create_experiment(exp_config)
        
        return {
            "status": "success",
            "experiment_id": experiment_id,
            "message": f"Experiment '{config.name}' created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating experiment: {str(e)}")

@router.post("/experiments/{experiment_id}/start")
async def start_experiment(experiment_id: str):
    """Startet Experiment"""
    
    try:
        experiment_manager = get_experiment_manager()
        success = experiment_manager.start_experiment(experiment_id)
        
        if success:
            return {"status": "success", "message": f"Experiment {experiment_id} started"}
        else:
            raise HTTPException(status_code=400, detail="Failed to start experiment")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting experiment: {str(e)}")

@router.post("/experiments/{experiment_id}/stop")
async def stop_experiment(experiment_id: str):
    """Stoppt Experiment"""
    
    try:
        experiment_manager = get_experiment_manager()
        success = experiment_manager.stop_experiment(experiment_id)
        
        if success:
            return {"status": "success", "message": f"Experiment {experiment_id} stopped"}
        else:
            raise HTTPException(status_code=400, detail="Failed to stop experiment")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping experiment: {str(e)}")

@router.get("/experiments")
async def list_experiments(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Maximum number of experiments")
):
    """Listet Experimente auf"""
    
    try:
        experiment_manager = get_experiment_manager()
        experiments = experiment_manager.list_experiments(status=status, limit=limit)
        
        return {
            "status": "success",
            "experiments": [
                {
                    "experiment_id": exp.experiment_id,
                    "status": exp.status,
                    "start_time": exp.start_time.isoformat() if exp.start_time else None,
                    "end_time": exp.end_time.isoformat() if exp.end_time else None,
                    "current_traffic": exp.current_traffic
                }
                for exp in experiments
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing experiments: {str(e)}")

@router.get("/experiments/{experiment_id}/status")
async def get_experiment_status(experiment_id: str):
    """Gibt Status eines Experiments zurück"""
    
    try:
        experiment_manager = get_experiment_manager()
        status = experiment_manager.get_experiment_status(experiment_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        return {
            "status": "success",
            "experiment": {
                "experiment_id": status.experiment_id,
                "status": status.status,
                "start_time": status.start_time.isoformat() if status.start_time else None,
                "end_time": status.end_time.isoformat() if status.end_time else None,
                "current_traffic": status.current_traffic
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting experiment status: {str(e)}")

@router.post("/experiments/{experiment_id}/evaluate")
async def evaluate_experiment(experiment_id: str):
    """Wertet Experiment aus"""
    
    try:
        experiment_manager = get_experiment_manager()
        result = experiment_manager.evaluate_experiment(experiment_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Experiment not found or not running")
        
        return {
            "status": "success",
            "evaluation": {
                "experiment_id": result.experiment_id,
                "variant_a": result.variant_a,
                "variant_b": result.variant_b,
                "n_a": result.n_a,
                "n_b": result.n_b,
                "win_rate_a": result.win_rate_a,
                "win_rate_b": result.win_rate_b,
                "p_value": result.p_value,
                "significant": result.significant,
                "effect_size": result.effect_size,
                "recommendation": result.recommendation
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error evaluating experiment: {str(e)}")

# ------------------------------------------------------------
# Evaluation & Optimization
# ------------------------------------------------------------

@router.post("/evaluate")
async def evaluate_system():
    """Führt System-Evaluation durch"""
    
    try:
        scheduler = get_experiment_scheduler()
        report = scheduler.schedule_daily_evaluation()
        
        return {
            "status": "success",
            "evaluation": report
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error evaluating system: {str(e)}")

@router.post("/optimize")
async def optimize_system(
    base_prompt: str = Body(..., description="Base prompt to optimize"),
    objectives: Optional[Dict[str, float]] = Body(None, description="Optimization objectives")
):
    """Optimiert System"""
    
    try:
        optimizer = get_multi_optimizer()
        prompt_variants, routing_policy = optimizer.optimize_system(base_prompt, objectives)
        
        return {
            "status": "success",
            "optimization": {
                "prompt_variants": [
                    {
                        "id": variant.id,
                        "name": variant.name,
                        "content": variant.content,
                        "role": variant.role,
                        "tags": variant.tags
                    }
                    for variant in prompt_variants
                ],
                "routing_policy": {
                    "id": routing_policy.id,
                    "name": routing_policy.name,
                    "weights": routing_policy.weights,
                    "conditions": routing_policy.conditions
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing system: {str(e)}")

# ------------------------------------------------------------
# Registry Management
# ------------------------------------------------------------

@router.post("/propose")
async def propose_changes(
    prompt_variants: Optional[List[PromptVariant]] = Body(None),
    routing_policies: Optional[List[RoutingPolicy]] = Body(None)
):
    """Schlägt Änderungen vor"""
    
    try:
        results = {"prompts": [], "policies": []}
        
        # Registriere Prompt-Varianten
        if prompt_variants:
            prompt_registry = get_prompt_registry()
            for variant in prompt_variants:
                prompt_id = prompt_registry.register_prompt(
                    name=variant.name,
                    content=variant.content,
                    role=variant.role,
                    tags=variant.tags
                )
                results["prompts"].append({"id": prompt_id, "name": variant.name})
        
        # Registriere Routing-Policies
        if routing_policies:
            policy_registry = get_policy_registry()
            for policy in routing_policies:
                policy_id = policy_registry.register_policy(
                    name=policy.name,
                    policy_type="routing",  # Vereinfacht
                    config={
                        "weights": policy.weights,
                        "conditions": policy.conditions
                    }
                )
                results["policies"].append({"id": policy_id, "name": policy.name})
        
        return {
            "status": "success",
            "proposed": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error proposing changes: {str(e)}")

@router.post("/apply")
async def apply_changes(
    prompt_ids: Optional[List[str]] = Body(None),
    policy_ids: Optional[List[str]] = Body(None)
):
    """Wendet Änderungen an"""
    
    try:
        results = {"prompts": [], "policies": []}
        
        # Befördere Prompts
        if prompt_ids:
            prompt_registry = get_prompt_registry()
            for prompt_id in prompt_ids:
                # Hole aktuelle Version
                prompt = prompt_registry.registry.prompts.get(prompt_id)
                if prompt:
                    success = prompt_registry.promote_candidate(prompt_id, prompt.current_version)
                    results["prompts"].append({"id": prompt_id, "success": success})
        
        # Befördere Policies
        if policy_ids:
            policy_registry = get_policy_registry()
            for policy_id in policy_ids:
                # Hole aktuelle Version
                policy = policy_registry.registry.policies.get(policy_id)
                if policy:
                    success = policy_registry.promote_policy(policy_id, policy.current_version)
                    results["policies"].append({"id": policy_id, "success": success})
        
        return {
            "status": "success",
            "applied": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error applying changes: {str(e)}")

@router.post("/rollback")
async def rollback_changes(
    prompt_ids: Optional[List[str]] = Body(None),
    policy_ids: Optional[List[str]] = Body(None)
):
    """Rollback von Änderungen"""
    
    try:
        results = {"prompts": [], "policies": []}
        
        # Rollback Prompts
        if prompt_ids:
            prompt_registry = get_prompt_registry()
            for prompt_id in prompt_ids:
                # Finde vorherige Version
                prompt = prompt_registry.registry.prompts.get(prompt_id)
                if prompt and len(prompt.versions) > 1:
                    # Vereinfachte Logik - nimm vorherige Version
                    versions = list(prompt.versions.keys())
                    if len(versions) > 1:
                        target_version = prompt.versions[versions[-2]].version
                        success = prompt_registry.rollback_prompt(prompt_id, target_version)
                        results["prompts"].append({"id": prompt_id, "success": success})
        
        return {
            "status": "success",
            "rolled_back": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rolling back changes: {str(e)}")

# ------------------------------------------------------------
# Knowledge Base
# ------------------------------------------------------------

@router.post("/kb/ingest")
async def ingest_knowledge(
    docs_path: str = Body("docs", description="Path to docs directory"),
    results_path: str = Body("data/results", description="Path to results directory")
):
    """Führt Knowledge-Base Ingest durch"""
    
    try:
        ingest_manager = get_ingest_manager()
        results = ingest_manager.run_daily_ingest(docs_path, results_path)
        
        return {
            "status": "success",
            "ingest_results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting knowledge: {str(e)}")

@router.get("/kb/stats")
async def get_kb_stats():
    """Gibt Knowledge-Base Statistiken zurück"""
    
    try:
        kb_manager = get_kb_manager()
        stats = kb_manager.get_knowledge_stats()
        
        return {
            "status": "success",
            "stats": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting KB stats: {str(e)}")

# ------------------------------------------------------------
# Scheduler
# ------------------------------------------------------------

@router.get("/scheduler/status")
async def get_scheduler_status():
    """Gibt Scheduler-Status zurück"""
    
    try:
        scheduler_manager = get_scheduler_manager()
        status = scheduler_manager.get_scheduler_status()
        
        return {
            "status": "success",
            "scheduler": status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting scheduler status: {str(e)}")

@router.post("/scheduler/jobs/{job_id}/run")
async def run_job_manually(job_id: str):
    """Führt Job manuell aus"""
    
    try:
        scheduler_manager = get_scheduler_manager()
        result = scheduler_manager.run_job_manually(job_id)
        
        if result:
            return {
                "status": "success",
                "job_result": result
            }
        else:
            raise HTTPException(status_code=404, detail="Job not found")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running job: {str(e)}")
