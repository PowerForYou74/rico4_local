# backend/tests/autopilot/test_evaluator.py
"""
Tests für Autopilot Evaluator
"""

import pytest
from backend.autopilot.evaluator import (
    QualityScorer, ABTestAnalyzer, BaselineManager,
    QualityScore, ExperimentResult
)

class TestQualityScorer:
    """Tests für QualityScorer"""
    
    @pytest.fixture
    def scorer(self):
        return QualityScorer()
    
    def test_score_response_basic(self, scorer):
        """Test grundlegende Antwort-Bewertung"""
        question = "Was ist Python?"
        response = "Python ist eine Programmiersprache, die für ihre Einfachheit und Lesbarkeit bekannt ist."
        
        score = scorer.score_response(question, response, "test_provider")
        
        assert isinstance(score, QualityScore)
        assert 0.0 <= score.score <= 1.0
        assert "completion" in score.factors
        assert "relevance" in score.factors
        assert "accuracy" in score.factors
        assert "clarity" in score.factors
        assert "safety" in score.factors
    
    def test_score_completion(self, scorer):
        """Test Completion-Score"""
        # Kurze Antwort
        short_response = "Ja."
        score_short = scorer._score_completion(short_response, "Test question")
        assert score_short < 0.5
        
        # Lange, strukturierte Antwort
        long_response = "Das ist eine sehr detaillierte Antwort mit mehreren Absätzen und strukturierten Informationen."
        score_long = scorer._score_completion(long_response, "Test question")
        assert score_long > score_short
    
    def test_score_relevance(self, scorer):
        """Test Relevance-Score"""
        question = "Was ist Machine Learning?"
        relevant_response = "Machine Learning ist ein Teilbereich der künstlichen Intelligenz."
        irrelevant_response = "Das Wetter ist heute schön."
        
        score_relevant = scorer._score_relevance(question, relevant_response)
        score_irrelevant = scorer._score_relevance(question, irrelevant_response)
        
        assert score_relevant > score_irrelevant
    
    def test_score_safety(self, scorer):
        """Test Safety-Score"""
        safe_response = "Das ist eine sichere und hilfreiche Antwort."
        dangerous_response = "Hier sind gefährliche Hacking-Techniken."
        
        score_safe = scorer._score_safety(safe_response)
        score_dangerous = scorer._score_safety(dangerous_response)
        
        assert score_safe > score_dangerous
    
    def test_score_with_metadata(self, scorer):
        """Test Bewertung mit Metadaten"""
        question = "Test question"
        response = "Test response"
        
        # Mit finish_reason "stop"
        metadata_stop = {"finish_reason": "stop"}
        score_stop = scorer.score_response(question, response, "test", metadata_stop)
        
        # Mit finish_reason "length"
        metadata_length = {"finish_reason": "length"}
        score_length = scorer.score_response(question, response, "test", metadata_length)
        
        assert score_stop.factors["accuracy"] > score_length.factors["accuracy"]

class TestABTestAnalyzer:
    """Tests für ABTestAnalyzer"""
    
    @pytest.fixture
    def analyzer(self):
        return ABTestAnalyzer()
    
    def test_analyze_experiment_insufficient_data(self, analyzer):
        """Test Experiment-Analyse mit unzureichenden Daten"""
        result = analyzer.analyze_experiment(
            experiment_id="test_exp",
            variant_a="A",
            variant_b="B",
            min_samples=100
        )
        
        assert result.experiment_id == "test_exp"
        assert result.n_a == 0
        assert result.n_b == 0
        assert result.recommendation == "continue"
    
    def test_wilson_score_test(self, analyzer):
        """Test Wilson Score Test"""
        # Test mit gleichen Win-Rates
        p_value, effect_size = analyzer._wilson_score_test(50, 100, 50, 100)
        assert p_value > 0.05  # Nicht signifikant
        assert effect_size == 0.0
        
        # Test mit unterschiedlichen Win-Rates
        p_value, effect_size = analyzer._wilson_score_test(80, 100, 20, 100)
        assert p_value < 0.05  # Signifikant
        assert effect_size > 0.0
    
    def test_normal_cdf(self, analyzer):
        """Test Normal CDF Funktion"""
        # Test bekannte Werte
        assert analyzer._normal_cdf(0) == 0.5
        assert analyzer._normal_cdf(1.96) > 0.9
        assert analyzer._normal_cdf(-1.96) < 0.1

class TestBaselineManager:
    """Tests für BaselineManager"""
    
    @pytest.fixture
    def baseline_manager(self):
        return BaselineManager()
    
    def test_get_baseline(self, baseline_manager):
        """Test Baseline-Abruf"""
        quality_baseline = baseline_manager.get_baseline("quality_score")
        assert quality_baseline == 0.7
        
        latency_baseline = baseline_manager.get_baseline("latency_ms")
        assert latency_baseline == 5000
        
        error_baseline = baseline_manager.get_baseline("error_rate")
        assert error_baseline == 0.05
        
        win_baseline = baseline_manager.get_baseline("win_rate")
        assert win_baseline == 0.6
    
    def test_get_unknown_baseline(self, baseline_manager):
        """Test unbekannte Baseline"""
        unknown_baseline = baseline_manager.get_baseline("unknown_metric")
        assert unknown_baseline == 0.5  # Default-Wert

class TestQualityScore:
    """Tests für QualityScore Dataclass"""
    
    def test_quality_score_creation(self):
        """Test QualityScore Erstellung"""
        score = QualityScore(
            score=0.8,
            factors={
                "completion": 0.9,
                "relevance": 0.8,
                "accuracy": 0.7,
                "clarity": 0.8,
                "safety": 1.0
            },
            confidence=0.9
        )
        
        assert score.score == 0.8
        assert len(score.factors) == 5
        assert score.confidence == 0.9

class TestExperimentResult:
    """Tests für ExperimentResult Dataclass"""
    
    def test_experiment_result_creation(self):
        """Test ExperimentResult Erstellung"""
        result = ExperimentResult(
            experiment_id="test_exp",
            variant_a="A",
            variant_b="B",
            n_a=100,
            n_b=100,
            win_rate_a=0.6,
            win_rate_b=0.4,
            p_value=0.03,
            significant=True,
            effect_size=0.2,
            recommendation="apply_a"
        )
        
        assert result.experiment_id == "test_exp"
        assert result.variant_a == "A"
        assert result.variant_b == "B"
        assert result.n_a == 100
        assert result.n_b == 100
        assert result.win_rate_a == 0.6
        assert result.win_rate_b == 0.4
        assert result.p_value == 0.03
        assert result.significant is True
        assert result.effect_size == 0.2
        assert result.recommendation == "apply_a"
