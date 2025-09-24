# backend/autopilot/evaluator.py
"""
Autopilot Evaluator - Scorer, Baselines, Signifikanztests
Bewertet Qualität, führt A/B Analysen durch
"""

import math
import statistics
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlmodel import Session, select
from .metrics import AutopilotMetrics, get_metrics_writer

# ------------------------------------------------------------
# Datenmodelle
# ------------------------------------------------------------

@dataclass
class QualityScore:
    """Qualitätsbewertung eines Runs"""
    score: float  # 0.0-1.0
    factors: Dict[str, float]  # Einzelne Bewertungsfaktoren
    confidence: float  # Vertrauen in die Bewertung

@dataclass
class ExperimentResult:
    """Ergebnis eines A/B Tests"""
    experiment_id: str
    variant_a: str
    variant_b: str
    n_a: int
    n_b: int
    win_rate_a: float
    win_rate_b: float
    p_value: float
    significant: bool
    effect_size: float
    recommendation: str  # "continue", "stop", "apply_a", "apply_b"

# ------------------------------------------------------------
# Quality Scorer
# ------------------------------------------------------------

class QualityScorer:
    """Bewertet die Qualität von AI-Antworten"""
    
    def __init__(self):
        self.weights = {
            "completion": 0.3,      # Vollständigkeit der Antwort
            "relevance": 0.25,      # Relevanz zur Frage
            "accuracy": 0.2,        # Richtigkeit der Informationen
            "clarity": 0.15,       # Klarheit der Antwort
            "safety": 0.1          # Sicherheit/Guardrails
        }
    
    def score_response(self, 
                      question: str,
                      response: str,
                      provider: str,
                      metadata: Optional[Dict[str, Any]] = None) -> QualityScore:
        """Bewertet eine AI-Antwort"""
        
        factors = {}
        
        # 1. Completion Score (Länge und Vollständigkeit)
        factors["completion"] = self._score_completion(response, question)
        
        # 2. Relevance Score (Relevanz zur Frage)
        factors["relevance"] = self._score_relevance(question, response)
        
        # 3. Accuracy Score (basierend auf Metadaten)
        factors["accuracy"] = self._score_accuracy(metadata or {})
        
        # 4. Clarity Score (Struktur und Verständlichkeit)
        factors["clarity"] = self._score_clarity(response)
        
        # 5. Safety Score (Guardrails)
        factors["safety"] = self._score_safety(response)
        
        # Gewichteter Gesamtscore
        total_score = sum(factors[key] * self.weights[key] for key in factors)
        
        # Confidence basierend auf Faktoren-Varianz
        confidence = 1.0 - statistics.stdev(factors.values()) if len(factors) > 1 else 1.0
        
        return QualityScore(
            score=total_score,
            factors=factors,
            confidence=confidence
        )
    
    def _score_completion(self, response: str, question: str) -> float:
        """Bewertet Vollständigkeit der Antwort"""
        if not response or len(response.strip()) < 10:
            return 0.0
        
        # Mindestlänge basierend auf Frage
        min_length = max(50, len(question) * 2)
        
        if len(response) < min_length:
            return 0.3
        
        # Vollständigkeit basierend auf Struktur
        has_structure = any(marker in response.lower() for marker in 
                          ['1.', '2.', '•', '-', '**', '##', '###'])
        
        if has_structure and len(response) > min_length * 1.5:
            return 1.0
        elif len(response) > min_length:
            return 0.8
        else:
            return 0.6
    
    def _score_relevance(self, question: str, response: str) -> float:
        """Bewertet Relevanz zur Frage"""
        if not question or not response:
            return 0.0
        
        # Einfache Keyword-Übereinstimmung
        question_words = set(question.lower().split())
        response_words = set(response.lower().split())
        
        if not question_words:
            return 0.5
        
        overlap = len(question_words.intersection(response_words))
        relevance = overlap / len(question_words)
        
        return min(1.0, relevance * 2)  # Skalierung
    
    def _score_accuracy(self, metadata: Dict[str, Any]) -> float:
        """Bewertet Richtigkeit basierend auf Metadaten"""
        # Basierend auf finish_reason und anderen Metadaten
        finish_reason = metadata.get('finish_reason', '')
        
        if finish_reason == 'stop':
            return 1.0
        elif finish_reason == 'length':
            return 0.8
        elif finish_reason == 'content_filter':
            return 0.3
        else:
            return 0.5
    
    def _score_clarity(self, response: str) -> float:
        """Bewertet Klarheit der Antwort"""
        if not response:
            return 0.0
        
        # Struktur-Indikatoren
        structure_indicators = ['**', '##', '###', '1.', '2.', '•', '-']
        has_structure = any(indicator in response for indicator in structure_indicators)
        
        # Satzlänge (zu lange Sätze = weniger klar)
        sentences = response.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        
        clarity_score = 0.5
        
        if has_structure:
            clarity_score += 0.3
        
        if 5 <= avg_sentence_length <= 20:
            clarity_score += 0.2
        elif avg_sentence_length > 30:
            clarity_score -= 0.2
        
        return max(0.0, min(1.0, clarity_score))
    
    def _score_safety(self, response: str) -> float:
        """Bewertet Sicherheit der Antwort"""
        if not response:
            return 1.0
        
        # Gefährliche Keywords
        dangerous_keywords = [
            'hack', 'exploit', 'malware', 'virus', 'illegal', 'harmful',
            'dangerous', 'unsafe', 'risky', 'threat'
        ]
        
        response_lower = response.lower()
        danger_count = sum(1 for keyword in dangerous_keywords if keyword in response_lower)
        
        if danger_count == 0:
            return 1.0
        elif danger_count <= 2:
            return 0.7
        else:
            return 0.3

# ------------------------------------------------------------
# A/B Test Analyzer
# ------------------------------------------------------------

class ABTestAnalyzer:
    """Führt A/B Test Analysen durch"""
    
    def analyze_experiment(self, 
                          experiment_id: str,
                          variant_a: str,
                          variant_b: str,
                          min_samples: int = 100,
                          significance_level: float = 0.05) -> ExperimentResult:
        """Analysiert ein A/B Experiment"""
        
        # Hole Metriken für beide Varianten
        metrics_a = self._get_variant_metrics(experiment_id, variant_a)
        metrics_b = self._get_variant_metrics(experiment_id, variant_b)
        
        n_a = len(metrics_a)
        n_b = len(metrics_b)
        
        if n_a < min_samples or n_b < min_samples:
            return ExperimentResult(
                experiment_id=experiment_id,
                variant_a=variant_a,
                variant_b=variant_b,
                n_a=n_a,
                n_b=n_b,
                win_rate_a=0,
                win_rate_b=0,
                p_value=1.0,
                significant=False,
                effect_size=0,
                recommendation="continue"  # Nicht genug Daten
            )
        
        # Win-Rate berechnen
        wins_a = sum(1 for m in metrics_a if m.win is True)
        wins_b = sum(1 for m in metrics_b if m.win is True)
        
        win_rate_a = wins_a / n_a if n_a > 0 else 0
        win_rate_b = wins_b / n_b if n_b > 0 else 0
        
        # Wilson Score für Konfidenzintervalle
        p_value, effect_size = self._wilson_score_test(
            wins_a, n_a, wins_b, n_b
        )
        
        significant = p_value < significance_level
        
        # Empfehlung
        if significant:
            if win_rate_a > win_rate_b:
                recommendation = "apply_a"
            else:
                recommendation = "apply_b"
        else:
            recommendation = "continue"
        
        return ExperimentResult(
            experiment_id=experiment_id,
            variant_a=variant_a,
            variant_b=variant_b,
            n_a=n_a,
            n_b=n_b,
            win_rate_a=win_rate_a,
            win_rate_b=win_rate_b,
            p_value=p_value,
            significant=significant,
            effect_size=effect_size,
            recommendation=recommendation
        )
    
    def _get_variant_metrics(self, experiment_id: str, variant: str) -> List[AutopilotMetrics]:
        """Holt Metriken für eine Variante"""
        writer = get_metrics_writer()
        
        with Session(writer.engine) as session:
            query = select(AutopilotMetrics).where(
                AutopilotMetrics.experiment_id == experiment_id,
                AutopilotMetrics.metadata.contains({"variant": variant})
            )
            return session.exec(query).all()
    
    def _wilson_score_test(self, wins_a: int, n_a: int, wins_b: int, n_b: int) -> Tuple[float, float]:
        """Wilson Score Test für Binomialverteilung"""
        
        if n_a == 0 or n_b == 0:
            return 1.0, 0.0
        
        p_a = wins_a / n_a
        p_b = wins_b / n_b
        
        # Wilson Score Konfidenzintervalle
        z = 1.96  # 95% Konfidenz
        
        # Standardfehler
        se_a = math.sqrt((p_a * (1 - p_a)) / n_a)
        se_b = math.sqrt((p_b * (1 - p_b)) / n_b)
        
        # Differenz und Standardfehler der Differenz
        diff = p_a - p_b
        se_diff = math.sqrt(se_a**2 + se_b**2)
        
        if se_diff == 0:
            return 1.0, 0.0
        
        # Z-Score
        z_score = abs(diff) / se_diff
        
        # P-Wert (vereinfacht)
        p_value = 2 * (1 - self._normal_cdf(z_score))
        
        # Effect Size (Cohen's h)
        effect_size = 2 * (math.asin(math.sqrt(p_a)) - math.asin(math.sqrt(p_b)))
        
        return p_value, effect_size
    
    def _normal_cdf(self, x: float) -> float:
        """Kumulative Verteilungsfunktion der Normalverteilung (vereinfacht)"""
        # Approximation der Normalverteilung
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

# ------------------------------------------------------------
# Baseline Manager
# ------------------------------------------------------------

class BaselineManager:
    """Verwaltet Baselines für Vergleiche"""
    
    def __init__(self):
        self.baselines = {
            "quality_score": 0.7,
            "latency_ms": 5000,
            "error_rate": 0.05,
            "win_rate": 0.6
        }
    
    def get_baseline(self, metric: str) -> float:
        """Gibt Baseline für eine Metrik zurück"""
        return self.baselines.get(metric, 0.5)
    
    def update_baseline(self, metric: str, value: float, window_hours: int = 168):
        """Aktualisiert Baseline basierend auf historischen Daten"""
        writer = get_metrics_writer()
        
        since = datetime.utcnow() - timedelta(hours=window_hours)
        
        with Session(writer.engine) as session:
            if metric == "quality_score":
                query = select(AutopilotMetrics.quality_score).where(
                    AutopilotMetrics.timestamp >= since,
                    AutopilotMetrics.quality_score.is_not(None)
                )
                scores = session.exec(query).all()
                if scores:
                    self.baselines[metric] = statistics.mean(scores)
            
            elif metric == "latency_ms":
                query = select(AutopilotMetrics.latency_ms).where(
                    AutopilotMetrics.timestamp >= since
                )
                latencies = session.exec(query).all()
                if latencies:
                    self.baselines[metric] = statistics.mean(latencies)
            
            elif metric == "error_rate":
                query = select(AutopilotMetrics).where(
                    AutopilotMetrics.timestamp >= since
                )
                metrics = session.exec(query).all()
                if metrics:
                    errors = sum(1 for m in metrics if m.error_type is not None)
                    self.baselines[metric] = errors / len(metrics)
            
            elif metric == "win_rate":
                query = select(AutopilotMetrics.win).where(
                    AutopilotMetrics.timestamp >= since,
                    AutopilotMetrics.win.is_not(None)
                )
                wins = session.exec(query).all()
                if wins:
                    self.baselines[metric] = sum(wins) / len(wins)

# ------------------------------------------------------------
# Globale Instanzen
# ------------------------------------------------------------

_quality_scorer: Optional[QualityScorer] = None
_ab_analyzer: Optional[ABTestAnalyzer] = None
_baseline_manager: Optional[BaselineManager] = None

def get_quality_scorer() -> QualityScorer:
    global _quality_scorer
    if _quality_scorer is None:
        _quality_scorer = QualityScorer()
    return _quality_scorer

def get_ab_analyzer() -> ABTestAnalyzer:
    global _ab_analyzer
    if _ab_analyzer is None:
        _ab_analyzer = ABTestAnalyzer()
    return _ab_analyzer

def get_baseline_manager() -> BaselineManager:
    global _baseline_manager
    if _baseline_manager is None:
        _baseline_manager = BaselineManager()
    return _baseline_manager
