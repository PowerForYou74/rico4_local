# backend/tests/autopilot/test_metrics.py
"""
Tests für Autopilot Metrics
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from backend.autopilot.metrics import MetricsWriter, AutopilotMetrics, AutopilotExperiments

class TestMetricsWriter:
    """Tests für MetricsWriter"""
    
    @pytest.fixture
    def temp_db(self):
        """Erstellt temporäre Datenbank für Tests"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        yield f"sqlite:///{db_path}"
        
        # Cleanup
        try:
            os.unlink(db_path)
        except:
            pass
    
    def test_metrics_writer_init(self, temp_db):
        """Test MetricsWriter Initialisierung"""
        writer = MetricsWriter(temp_db)
        assert writer.engine is not None
    
    def test_log_run(self, temp_db):
        """Test Run-Logging"""
        writer = MetricsWriter(temp_db)
        
        run_id = writer.log_run(
            task="test_task",
            provider="test_provider",
            latency_ms=1000.0,
            cost_est=0.01,
            quality_score=0.8,
            win=True
        )
        
        assert run_id is not None
        assert isinstance(run_id, str)
    
    def test_get_metrics_summary(self, temp_db):
        """Test Metriken-Zusammenfassung"""
        writer = MetricsWriter(temp_db)
        
        # Logge einige Test-Runs
        for i in range(5):
            writer.log_run(
                task="test_task",
                provider="test_provider",
                latency_ms=1000.0 + i * 100,
                cost_est=0.01,
                quality_score=0.8,
                win=True
            )
        
        summary = writer.get_metrics_summary(hours=24)
        
        assert summary["total_runs"] == 5
        assert summary["avg_latency_ms"] > 0
        assert summary["total_cost"] > 0
        assert summary["error_rate"] == 0
        assert summary["win_rate"] == 1.0
    
    def test_get_metrics_summary_with_filters(self, temp_db):
        """Test Metriken-Zusammenfassung mit Filtern"""
        writer = MetricsWriter(temp_db)
        
        # Logge verschiedene Tasks und Provider
        writer.log_run(task="task_a", provider="provider_1", latency_ms=1000, cost_est=0.01)
        writer.log_run(task="task_b", provider="provider_1", latency_ms=2000, cost_est=0.02)
        writer.log_run(task="task_a", provider="provider_2", latency_ms=1500, cost_est=0.015)
        
        # Filter nach Task
        summary_a = writer.get_metrics_summary(task="task_a")
        assert summary_a["total_runs"] == 2
        
        # Filter nach Provider
        summary_p1 = writer.get_metrics_summary(provider="provider_1")
        assert summary_p1["total_runs"] == 2
    
    def test_hook_functions(self, temp_db):
        """Test Hook-Funktionen"""
        writer = MetricsWriter(temp_db)
        
        # Test hook_ai_ask_start
        run_id = writer.hook_ai_ask_start("test_task", "test_provider")
        assert run_id is not None
        assert "test_task" in run_id
        assert "test_provider" in run_id
        
        # Test hook_ai_ask_end
        writer.hook_ai_ask_end(
            run_id=run_id,
            latency_ms=1000.0,
            cost_est=0.01,
            quality_score=0.8,
            win=True
        )
        
        # Prüfe ob Run geloggt wurde
        summary = writer.get_metrics_summary()
        assert summary["total_runs"] == 1

class TestAutopilotMetrics:
    """Tests für AutopilotMetrics Model"""
    
    def test_autopilot_metrics_creation(self):
        """Test AutopilotMetrics Erstellung"""
        metric = AutopilotMetrics(
            task="test_task",
            provider="test_provider",
            latency_ms=1000.0,
            cost_est=0.01,
            quality_score=0.8,
            win=True,
            run_id="test_run_123"
        )
        
        assert metric.task == "test_task"
        assert metric.provider == "test_provider"
        assert metric.latency_ms == 1000.0
        assert metric.cost_est == 0.01
        assert metric.quality_score == 0.8
        assert metric.win is True
        assert metric.run_id == "test_run_123"

class TestAutopilotExperiments:
    """Tests für AutopilotExperiments Model"""
    
    def test_autopilot_experiments_creation(self):
        """Test AutopilotExperiments Erstellung"""
        experiment = AutopilotExperiments(
            experiment_id="test_exp_123",
            name="Test Experiment",
            type="ab",
            variants={"A": "variant_a", "B": "variant_b"},
            traffic_split={"A": 0.5, "B": 0.5},
            start_ts=datetime.utcnow(),
            status="running"
        )
        
        assert experiment.experiment_id == "test_exp_123"
        assert experiment.name == "Test Experiment"
        assert experiment.type == "ab"
        assert experiment.variants == {"A": "variant_a", "B": "variant_b"}
        assert experiment.traffic_split == {"A": 0.5, "B": 0.5}
        assert experiment.status == "running"
