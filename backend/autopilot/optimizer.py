# backend/autopilot/optimizer.py
"""
Autopilot Optimizer - Prompt-/Routing-Optimierer
Multi-Objective: Qualität x Kosten x Latenz
"""

import json
import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlmodel import Session, select
from .metrics import AutopilotMetrics, get_metrics_writer
from .evaluator import get_quality_scorer, get_baseline_manager

# ------------------------------------------------------------
# Datenmodelle
# ------------------------------------------------------------

@dataclass
class PromptVariant:
    """Prompt-Variante für Optimierung"""
    id: str
    name: str
    content: str
    role: str = "system"
    tags: List[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()

@dataclass
class RoutingPolicy:
    """Routing-Policy für Provider-Auswahl"""
    id: str
    name: str
    weights: Dict[str, float]  # Provider -> Gewichtung
    conditions: Dict[str, Any]  # Bedingungen für Routing
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

@dataclass
class OptimizationResult:
    """Ergebnis einer Optimierung"""
    type: str  # "prompt", "routing"
    variant_id: str
    improvement: float  # Verbesserung gegenüber Baseline
    metrics: Dict[str, float]
    confidence: float

# ------------------------------------------------------------
# Prompt Optimizer
# ------------------------------------------------------------

class PromptOptimizer:
    """Optimiert Prompts basierend auf Metriken"""
    
    def __init__(self):
        self.optimization_strategies = [
            "clarity_improvement",
            "constraint_addition", 
            "few_shot_reordering",
            "role_refinement",
            "context_expansion"
        ]
    
    def generate_variants(self, 
                        base_prompt: str,
                        role: str = "system",
                        num_variants: int = 3) -> List[PromptVariant]:
        """Generiert Prompt-Varianten für Optimierung"""
        
        variants = []
        
        for i in range(num_variants):
            strategy = random.choice(self.optimization_strategies)
            variant_content = self._apply_strategy(base_prompt, strategy)
            
            variant = PromptVariant(
                id=f"variant_{int(datetime.utcnow().timestamp())}_{i}",
                name=f"Optimized {strategy} v{i+1}",
                content=variant_content,
                role=role,
                tags=[strategy, "optimized"]
            )
            variants.append(variant)
        
        return variants
    
    def _apply_strategy(self, base_prompt: str, strategy: str) -> str:
        """Wendet Optimierungsstrategie an"""
        
        if strategy == "clarity_improvement":
            return self._improve_clarity(base_prompt)
        elif strategy == "constraint_addition":
            return self._add_constraints(base_prompt)
        elif strategy == "few_shot_reordering":
            return self._reorder_few_shot(base_prompt)
        elif strategy == "role_refinement":
            return self._refine_role(base_prompt)
        elif strategy == "context_expansion":
            return self._expand_context(base_prompt)
        else:
            return base_prompt
    
    def _improve_clarity(self, prompt: str) -> str:
        """Verbessert Klarheit des Prompts"""
        improvements = [
            "\n\n**Wichtige Hinweise:**",
            "\n- Sei präzise und strukturiert in deinen Antworten",
            "\n- Verwende klare, verständliche Sprache",
            "\n- Strukturiere komplexe Informationen übersichtlich"
        ]
        return prompt + "".join(improvements)
    
    def _add_constraints(self, prompt: str) -> str:
        """Fügt Constraints hinzu"""
        constraints = [
            "\n\n**Constraints:**",
            "\n- Maximale Antwortlänge: 2000 Zeichen",
            "\n- Verwende nur verifizierte Informationen",
            "\n- Bei Unsicherheit: 'Ich bin mir nicht sicher' angeben"
        ]
        return prompt + "".join(constraints)
    
    def _reorder_few_shot(self, prompt: str) -> str:
        """Reordnet Few-Shot Beispiele"""
        # Vereinfachte Implementierung - in Realität würde man Few-Shot Beispiele parsen
        if "Beispiel:" in prompt or "Example:" in prompt:
            return prompt.replace("Beispiel:", "**Beispiel:**").replace("Example:", "**Example:**")
        return prompt
    
    def _refine_role(self, prompt: str) -> str:
        """Verfeinert die Rolle"""
        role_refinements = [
            "Du bist ein Experte mit jahrelanger Erfahrung.",
            "Deine Expertise umfasst sowohl Theorie als auch Praxis.",
            "Du denkst analytisch und strukturiert."
        ]
        return random.choice(role_refinements) + "\n\n" + prompt
    
    def _expand_context(self, prompt: str) -> str:
        """Erweitert den Kontext"""
        context_additions = [
            "\n\n**Kontext:** Berücksichtige aktuelle Best Practices und bewährte Methoden.",
            "\n\n**Ziel:** Biete praktische, umsetzbare Lösungen an."
        ]
        return prompt + "".join(context_additions)
    
    def evaluate_variant(self, 
                        variant: PromptVariant,
                        test_questions: List[str],
                        window_hours: int = 24) -> OptimizationResult:
        """Bewertet eine Prompt-Variante"""
        
        # Hole Metriken für diese Variante
        writer = get_metrics_writer()
        since = datetime.utcnow() - timedelta(hours=window_hours)
        
        with Session(writer.engine) as session:
            query = select(AutopilotMetrics).where(
                AutopilotMetrics.timestamp >= since,
                AutopilotMetrics.metadata.contains({"prompt_variant": variant.id})
            )
            metrics = session.exec(query).all()
        
        if not metrics:
            return OptimizationResult(
                type="prompt",
                variant_id=variant.id,
                improvement=0.0,
                metrics={},
                confidence=0.0
            )
        
        # Berechne Metriken
        avg_quality = sum(m.quality_score for m in metrics if m.quality_score) / len(metrics)
        avg_latency = sum(m.latency_ms for m in metrics) / len(metrics)
        error_rate = sum(1 for m in metrics if m.error_type) / len(metrics)
        win_rate = sum(1 for m in metrics if m.win) / len(metrics)
        
        # Vergleiche mit Baseline
        baseline_manager = get_baseline_manager()
        baseline_quality = baseline_manager.get_baseline("quality_score")
        baseline_latency = baseline_manager.get_baseline("latency_ms")
        baseline_error = baseline_manager.get_baseline("error_rate")
        baseline_win = baseline_manager.get_baseline("win_rate")
        
        # Verbesserung berechnen
        quality_improvement = (avg_quality - baseline_quality) / baseline_quality if baseline_quality > 0 else 0
        latency_improvement = (baseline_latency - avg_latency) / baseline_latency if baseline_latency > 0 else 0
        error_improvement = (baseline_error - error_rate) / baseline_error if baseline_error > 0 else 0
        win_improvement = (win_rate - baseline_win) / baseline_win if baseline_win > 0 else 0
        
        # Gewichteter Gesamtscore
        total_improvement = (
            quality_improvement * 0.4 +
            latency_improvement * 0.2 +
            error_improvement * 0.2 +
            win_improvement * 0.2
        )
        
        return OptimizationResult(
            type="prompt",
            variant_id=variant.id,
            improvement=total_improvement,
            metrics={
                "quality_score": avg_quality,
                "latency_ms": avg_latency,
                "error_rate": error_rate,
                "win_rate": win_rate
            },
            confidence=min(1.0, len(metrics) / 50)  # Confidence basierend auf Sample-Größe
        )

# ------------------------------------------------------------
# Routing Optimizer
# ------------------------------------------------------------

class RoutingOptimizer:
    """Optimiert Provider-Routing basierend auf Metriken"""
    
    def __init__(self):
        self.providers = ["openai", "claude", "perplexity"]
        self.default_weights = {p: 1.0 for p in self.providers}
    
    def analyze_provider_performance(self, 
                                   window_hours: int = 168) -> Dict[str, Dict[str, float]]:
        """Analysiert Provider-Performance"""
        
        writer = get_metrics_writer()
        since = datetime.utcnow() - timedelta(hours=window_hours)
        
        performance = {}
        
        for provider in self.providers:
            with Session(writer.engine) as session:
                query = select(AutopilotMetrics).where(
                    AutopilotMetrics.provider == provider,
                    AutopilotMetrics.timestamp >= since
                )
                metrics = session.exec(query).all()
            
            if not metrics:
                performance[provider] = {
                    "quality_score": 0.5,
                    "latency_ms": 5000,
                    "error_rate": 0.1,
                    "win_rate": 0.5,
                    "cost_est": 0.01
                }
                continue
            
            # Berechne Metriken
            quality_scores = [m.quality_score for m in metrics if m.quality_score is not None]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.5
            
            avg_latency = sum(m.latency_ms for m in metrics) / len(metrics)
            error_rate = sum(1 for m in metrics if m.error_type is not None) / len(metrics)
            win_rate = sum(1 for m in metrics if m.win is True) / len(metrics)
            avg_cost = sum(m.cost_est for m in metrics) / len(metrics)
            
            performance[provider] = {
                "quality_score": avg_quality,
                "latency_ms": avg_latency,
                "error_rate": error_rate,
                "win_rate": win_rate,
                "cost_est": avg_cost
            }
        
        return performance
    
    def optimize_routing_weights(self, 
                                performance: Dict[str, Dict[str, float]],
                                objectives: Dict[str, float] = None) -> Dict[str, float]:
        """Optimiert Routing-Gewichtungen basierend auf Performance"""
        
        if objectives is None:
            objectives = {
                "quality": 0.4,
                "latency": 0.2,
                "cost": 0.2,
                "reliability": 0.2
            }
        
        weights = {}
        
        for provider in self.providers:
            perf = performance.get(provider, {})
            
            # Normalisierte Scores (höher = besser)
            quality_score = perf.get("quality_score", 0.5)
            latency_score = 1.0 - min(1.0, perf.get("latency_ms", 5000) / 10000)  # Niedrigere Latenz = besser
            cost_score = 1.0 - min(1.0, perf.get("cost_est", 0.01) * 100)  # Niedrigere Kosten = besser
            reliability_score = 1.0 - perf.get("error_rate", 0.1)  # Niedrigere Fehlerrate = besser
            
            # Gewichteter Score
            total_score = (
                quality_score * objectives["quality"] +
                latency_score * objectives["latency"] +
                cost_score * objectives["cost"] +
                reliability_score * objectives["reliability"]
            )
            
            weights[provider] = max(0.1, total_score)  # Mindestgewichtung
        
        # Normalisiere Gewichtungen
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        
        return weights
    
    def create_routing_policy(self, 
                             weights: Dict[str, float],
                             conditions: Dict[str, Any] = None) -> RoutingPolicy:
        """Erstellt neue Routing-Policy"""
        
        if conditions is None:
            conditions = {
                "max_latency_ms": 10000,
                "max_cost_per_request": 0.05,
                "min_quality_threshold": 0.6
            }
        
        policy = RoutingPolicy(
            id=f"routing_policy_{int(datetime.utcnow().timestamp())}",
            name=f"Optimized Routing {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            weights=weights,
            conditions=conditions
        )
        
        return policy

# ------------------------------------------------------------
# Multi-Objective Optimizer
# ------------------------------------------------------------

class MultiObjectiveOptimizer:
    """Kombiniert Prompt- und Routing-Optimierung"""
    
    def __init__(self):
        self.prompt_optimizer = PromptOptimizer()
        self.routing_optimizer = RoutingOptimizer()
    
    def optimize_system(self, 
                       base_prompt: str,
                       objectives: Dict[str, float] = None) -> Tuple[List[PromptVariant], RoutingPolicy]:
        """Optimiert das gesamte System"""
        
        if objectives is None:
            objectives = {
                "quality": 0.4,
                "latency": 0.2,
                "cost": 0.2,
                "reliability": 0.2
            }
        
        # 1. Generiere Prompt-Varianten
        prompt_variants = self.prompt_optimizer.generate_variants(base_prompt)
        
        # 2. Analysiere Provider-Performance
        performance = self.routing_optimizer.analyze_provider_performance()
        
        # 3. Optimiere Routing
        routing_weights = self.routing_optimizer.optimize_routing_weights(performance, objectives)
        routing_policy = self.routing_optimizer.create_routing_policy(routing_weights)
        
        return prompt_variants, routing_policy
    
    def evaluate_optimization(self, 
                             prompt_variants: List[PromptVariant],
                             routing_policy: RoutingPolicy,
                             test_duration_hours: int = 24) -> Dict[str, Any]:
        """Bewertet Optimierungsergebnisse"""
        
        results = {
            "prompt_variants": [],
            "routing_policy": {
                "id": routing_policy.id,
                "weights": routing_policy.weights,
                "conditions": routing_policy.conditions
            },
            "overall_improvement": 0.0,
            "recommendations": []
        }
        
        # Bewerte Prompt-Varianten
        for variant in prompt_variants:
            result = self.prompt_optimizer.evaluate_variant(variant)
            results["prompt_variants"].append({
                "id": variant.id,
                "name": variant.name,
                "improvement": result.improvement,
                "metrics": result.metrics,
                "confidence": result.confidence
            })
        
        # Berechne Gesamtverbesserung
        if results["prompt_variants"]:
            avg_improvement = sum(v["improvement"] for v in results["prompt_variants"]) / len(results["prompt_variants"])
            results["overall_improvement"] = avg_improvement
        
        # Generiere Empfehlungen
        if results["overall_improvement"] > 0.1:
            results["recommendations"].append("Deploy optimized prompts")
        
        if any(v["improvement"] > 0.2 for v in results["prompt_variants"]):
            best_variant = max(results["prompt_variants"], key=lambda v: v["improvement"])
            results["recommendations"].append(f"Deploy best variant: {best_variant['name']}")
        
        return results

# ------------------------------------------------------------
# Globale Instanzen
# ------------------------------------------------------------

_prompt_optimizer: Optional[PromptOptimizer] = None
_routing_optimizer: Optional[RoutingOptimizer] = None
_multi_optimizer: Optional[MultiObjectiveOptimizer] = None

def get_prompt_optimizer() -> PromptOptimizer:
    global _prompt_optimizer
    if _prompt_optimizer is None:
        _prompt_optimizer = PromptOptimizer()
    return _prompt_optimizer

def get_routing_optimizer() -> RoutingOptimizer:
    global _routing_optimizer
    if _routing_optimizer is None:
        _routing_optimizer = RoutingOptimizer()
    return _routing_optimizer

def get_multi_optimizer() -> MultiObjectiveOptimizer:
    global _multi_optimizer
    if _multi_optimizer is None:
        _multi_optimizer = MultiObjectiveOptimizer()
    return _multi_optimizer
