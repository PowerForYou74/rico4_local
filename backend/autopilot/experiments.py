# backend/autopilot/experiments.py
"""
Autopilot Experiments - A/B Test Management
Plant, führt aus und wertet Experimente aus
"""

import json
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from sqlmodel import Session, select
from .metrics import AutopilotExperiments, AutopilotMetrics, get_metrics_writer
from .evaluator import get_ab_analyzer, ExperimentResult

# ------------------------------------------------------------
# Datenmodelle
# ------------------------------------------------------------

@dataclass
class ExperimentConfig:
    """Konfiguration für ein Experiment"""
    name: str
    type: str  # "ab", "prompt", "routing"
    variants: Dict[str, Any]
    traffic_split: Dict[str, float]
    duration_hours: int = 24
    min_samples: int = 100
    success_criteria: Dict[str, Any] = None
    guardrails: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.success_criteria is None:
            self.success_criteria = {
                "win_rate_delta_min": 0.05,
                "p_value_max": 0.05,
                "min_confidence": 0.8
            }
        
        if self.guardrails is None:
            self.guardrails = {
                "max_error_rate": 0.1,
                "max_latency_ms": 15000,
                "max_cost_per_day": 10.0
            }

@dataclass
class ExperimentStatus:
    """Status eines Experiments"""
    experiment_id: str
    status: str  # "draft", "running", "stopped", "completed", "failed"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    current_traffic: Dict[str, float] = None
    results: Optional[ExperimentResult] = None
    error_message: Optional[str] = None

# ------------------------------------------------------------
# Experiment Manager
# ------------------------------------------------------------

class ExperimentManager:
    """Verwaltet A/B Tests und Experimente"""
    
    def __init__(self):
        self.writer = get_metrics_writer()
        self.ab_analyzer = get_ab_analyzer()
    
    def create_experiment(self, config: ExperimentConfig) -> str:
        """Erstellt ein neues Experiment"""
        
        experiment_id = f"exp_{uuid.uuid4().hex[:8]}"
        
        # Validiere Traffic Split
        total_split = sum(config.traffic_split.values())
        if abs(total_split - 1.0) > 0.01:
            raise ValueError(f"Traffic split must sum to 1.0, got {total_split}")
        
        # Erstelle Experiment in DB
        experiment = AutopilotExperiments(
            experiment_id=experiment_id,
            name=config.name,
            type=config.type,
            variants=config.variants,
            traffic_split=config.traffic_split,
            start_ts=datetime.utcnow(),
            status="draft",
            guardrails=config.guardrails,
            success_criteria=config.success_criteria
        )
        
        with Session(self.writer.engine) as session:
            session.add(experiment)
            session.commit()
            session.refresh(experiment)
        
        return experiment_id
    
    def start_experiment(self, experiment_id: str) -> bool:
        """Startet ein Experiment"""
        
        with Session(self.writer.engine) as session:
            query = select(AutopilotExperiments).where(
                AutopilotExperiments.experiment_id == experiment_id
            )
            experiment = session.exec(query).first()
            
            if not experiment:
                return False
            
            if experiment.status != "draft":
                return False
            
            experiment.status = "running"
            experiment.start_ts = datetime.utcnow()
            session.add(experiment)
            session.commit()
        
        return True
    
    def stop_experiment(self, experiment_id: str) -> bool:
        """Stoppt ein Experiment"""
        
        with Session(self.writer.engine) as session:
            query = select(AutopilotExperiments).where(
                AutopilotExperiments.experiment_id == experiment_id
            )
            experiment = session.exec(query).first()
            
            if not experiment:
                return False
            
            if experiment.status != "running":
                return False
            
            experiment.status = "stopped"
            experiment.stop_ts = datetime.utcnow()
            session.add(experiment)
            session.commit()
        
        return True
    
    def get_experiment_status(self, experiment_id: str) -> Optional[ExperimentStatus]:
        """Gibt Status eines Experiments zurück"""
        
        with Session(self.writer.engine) as session:
            query = select(AutopilotExperiments).where(
                AutopilotExperiments.experiment_id == experiment_id
            )
            experiment = session.exec(query).first()
            
            if not experiment:
                return None
            
            return ExperimentStatus(
                experiment_id=experiment_id,
                status=experiment.status,
                start_time=experiment.start_ts,
                end_time=experiment.stop_ts,
                current_traffic=experiment.traffic_split
            )
    
    def list_experiments(self, 
                        status: Optional[str] = None,
                        limit: int = 50) -> List[ExperimentStatus]:
        """Listet Experimente auf"""
        
        with Session(self.writer.engine) as session:
            query = select(AutopilotExperiments)
            
            if status:
                query = query.where(AutopilotExperiments.status == status)
            
            query = query.order_by(AutopilotExperiments.created_at.desc()).limit(limit)
            experiments = session.exec(query).all()
            
            return [
                ExperimentStatus(
                    experiment_id=exp.experiment_id,
                    status=exp.status,
                    start_time=exp.start_ts,
                    end_time=exp.stop_ts,
                    current_traffic=exp.traffic_split
                )
                for exp in experiments
            ]
    
    def evaluate_experiment(self, experiment_id: str) -> Optional[ExperimentResult]:
        """Wertet ein Experiment aus"""
        
        with Session(self.writer.engine) as session:
            query = select(AutopilotExperiments).where(
                AutopilotExperiments.experiment_id == experiment_id
            )
            experiment = session.exec(query).first()
            
            if not experiment or experiment.status != "running":
                return None
            
            # Hole Varianten
            variants = list(experiment.variants.keys())
            if len(variants) < 2:
                return None
            
            # Führe A/B Analyse durch
            result = self.ab_analyzer.analyze_experiment(
                experiment_id=experiment_id,
                variant_a=variants[0],
                variant_b=variants[1],
                min_samples=experiment.success_criteria.get("min_samples", 100),
                significance_level=experiment.success_criteria.get("p_value_max", 0.05)
            )
            
            return result
    
    def check_guardrails(self, experiment_id: str) -> Dict[str, Any]:
        """Prüft Guardrails für ein Experiment"""
        
        with Session(self.writer.engine) as session:
            query = select(AutopilotExperiments).where(
                AutopilotExperiments.experiment_id == experiment_id
            )
            experiment = session.exec(query).first()
            
            if not experiment:
                return {"status": "error", "message": "Experiment not found"}
            
            # Hole Metriken für dieses Experiment
            metrics_query = select(AutopilotMetrics).where(
                AutopilotMetrics.experiment_id == experiment_id,
                AutopilotMetrics.timestamp >= experiment.start_ts
            )
            metrics = session.exec(metrics_query).all()
            
            if not metrics:
                return {"status": "ok", "violations": []}
            
            violations = []
            guardrails = experiment.guardrails or {}
            
            # Prüfe Error Rate
            error_rate = sum(1 for m in metrics if m.error_type is not None) / len(metrics)
            max_error_rate = guardrails.get("max_error_rate", 0.1)
            if error_rate > max_error_rate:
                violations.append({
                    "type": "error_rate",
                    "current": error_rate,
                    "limit": max_error_rate,
                    "message": f"Error rate {error_rate:.3f} exceeds limit {max_error_rate}"
                })
            
            # Prüfe Latenz
            avg_latency = sum(m.latency_ms for m in metrics) / len(metrics)
            max_latency = guardrails.get("max_latency_ms", 15000)
            if avg_latency > max_latency:
                violations.append({
                    "type": "latency",
                    "current": avg_latency,
                    "limit": max_latency,
                    "message": f"Average latency {avg_latency:.0f}ms exceeds limit {max_latency}ms"
                })
            
            # Prüfe Kosten
            total_cost = sum(m.cost_est for m in metrics)
            max_cost = guardrails.get("max_cost_per_day", 10.0)
            if total_cost > max_cost:
                violations.append({
                    "type": "cost",
                    "current": total_cost,
                    "limit": max_cost,
                    "message": f"Total cost ${total_cost:.2f} exceeds limit ${max_cost}"
                })
            
            return {
                "status": "ok" if not violations else "violations",
                "violations": violations
            }
    
    def auto_stop_experiment(self, experiment_id: str) -> bool:
        """Stoppt Experiment automatisch bei Verletzungen"""
        
        guardrail_check = self.check_guardrails(experiment_id)
        
        if guardrail_check["status"] == "violations":
            # Stoppe Experiment
            success = self.stop_experiment(experiment_id)
            
            if success:
                # Logge Verletzung
                violations = guardrail_check["violations"]
                violation_types = [v["type"] for v in violations]
                
                # Hier könnte man eine Slack-Notification senden
                print(f"Experiment {experiment_id} stopped due to guardrail violations: {violation_types}")
            
            return success
        
        return False

# ------------------------------------------------------------
# Traffic Split Manager
# ------------------------------------------------------------

class TrafficSplitManager:
    """Verwaltet Traffic-Splitting für Experimente"""
    
    def __init__(self):
        self.writer = get_metrics_writer()
    
    def get_variant_for_request(self, 
                               experiment_id: str,
                               run_id: str) -> Optional[str]:
        """Bestimmt Variante für eine Anfrage basierend auf Traffic Split"""
        
        with Session(self.writer.engine) as session:
            query = select(AutopilotExperiments).where(
                AutopilotExperiments.experiment_id == experiment_id,
                AutopilotExperiments.status == "running"
            )
            experiment = session.exec(query).first()
            
            if not experiment:
                return None
            
            # Deterministisches Splitting basierend auf run_id
            import hashlib
            hash_value = int(hashlib.md5(run_id.encode()).hexdigest()[:8], 16)
            bucket = hash_value % 10000  # 0-9999
            
            # Bestimme Variante basierend auf Traffic Split
            cumulative = 0
            for variant, percentage in experiment.traffic_split.items():
                cumulative += percentage * 10000
                if bucket < cumulative:
                    return variant
            
            # Fallback zur ersten Variante
            return list(experiment.traffic_split.keys())[0]
    
    def update_traffic_split(self, 
                           experiment_id: str,
                           new_split: Dict[str, float]) -> bool:
        """Aktualisiert Traffic Split für ein laufendes Experiment"""
        
        # Validiere Split
        total = sum(new_split.values())
        if abs(total - 1.0) > 0.01:
            return False
        
        with Session(self.writer.engine) as session:
            query = select(AutopilotExperiments).where(
                AutopilotExperiments.experiment_id == experiment_id,
                AutopilotExperiments.status == "running"
            )
            experiment = session.exec(query).first()
            
            if not experiment:
                return False
            
            experiment.traffic_split = new_split
            session.add(experiment)
            session.commit()
        
        return True

# ------------------------------------------------------------
# Experiment Scheduler
# ------------------------------------------------------------

class ExperimentScheduler:
    """Plant und überwacht Experimente"""
    
    def __init__(self):
        self.manager = ExperimentManager()
        self.traffic_manager = TrafficSplitManager()
    
    def check_running_experiments(self) -> List[Dict[str, Any]]:
        """Überprüft alle laufenden Experimente"""
        
        running_experiments = self.manager.list_experiments(status="running")
        results = []
        
        for exp_status in running_experiments:
            # Prüfe Guardrails
            guardrail_check = self.manager.check_guardrails(exp_status.experiment_id)
            
            # Evaluiere Experiment
            evaluation = self.manager.evaluate_experiment(exp_status.experiment_id)
            
            result = {
                "experiment_id": exp_status.experiment_id,
                "status": exp_status.status,
                "guardrails": guardrail_check,
                "evaluation": evaluation
            }
            
            # Auto-Stop bei Verletzungen
            if guardrail_check["status"] == "violations":
                self.manager.auto_stop_experiment(exp_status.experiment_id)
                result["auto_stopped"] = True
            
            results.append(result)
        
        return results
    
    def schedule_daily_evaluation(self) -> Dict[str, Any]:
        """Tägliche Auswertung aller Experimente"""
        
        # Hole alle laufenden Experimente
        running_experiments = self.manager.list_experiments(status="running")
        
        # Prüfe jedes Experiment
        results = self.check_running_experiments()
        
        # Generiere Report
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_experiments": len(running_experiments),
            "experiments": results,
            "summary": {
                "violations": sum(1 for r in results if r["guardrails"]["status"] == "violations"),
                "ready_for_evaluation": sum(1 for r in results if r["evaluation"] is not None),
                "auto_stopped": sum(1 for r in results if r.get("auto_stopped", False))
            }
        }
        
        return report

# ------------------------------------------------------------
# Globale Instanzen
# ------------------------------------------------------------

_experiment_manager: Optional[ExperimentManager] = None
_traffic_manager: Optional[TrafficSplitManager] = None
_scheduler: Optional[ExperimentScheduler] = None

def get_experiment_manager() -> ExperimentManager:
    global _experiment_manager
    if _experiment_manager is None:
        _experiment_manager = ExperimentManager()
    return _experiment_manager

def get_traffic_manager() -> TrafficSplitManager:
    global _traffic_manager
    if _traffic_manager is None:
        _traffic_manager = TrafficSplitManager()
    return _traffic_manager

def get_experiment_scheduler() -> ExperimentScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = ExperimentScheduler()
    return _scheduler
