# backend/tests/autopilot/test_experiments.py
"""
Tests für Autopilot Experiments
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from backend.autopilot.experiments import (
    ExperimentManager, TrafficSplitManager, ExperimentScheduler,
    ExperimentConfig, ExperimentStatus
)

class TestExperimentManager:
    """Tests für ExperimentManager"""
    
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
    
    @pytest.fixture
    def manager(self, temp_db):
        from backend.autopilot.metrics import MetricsWriter
        # Mock der get_metrics_writer Funktion
        import backend.autopilot.experiments
        original_writer = backend.autopilot.experiments.get_metrics_writer
        backend.autopilot.experiments.get_metrics_writer = lambda: MetricsWriter(temp_db)
        
        yield ExperimentManager()
        
        # Restore
        backend.autopilot.experiments.get_metrics_writer = original_writer
    
    def test_create_experiment(self, manager):
        """Test Experiment-Erstellung"""
        config = ExperimentConfig(
            name="Test Experiment",
            type="ab",
            variants={"A": "variant_a", "B": "variant_b"},
            traffic_split={"A": 0.5, "B": 0.5}
        )
        
        experiment_id = manager.create_experiment(config)
        
        assert experiment_id is not None
        assert isinstance(experiment_id, str)
        assert len(experiment_id) > 0
    
    def test_create_experiment_invalid_split(self, manager):
        """Test Experiment-Erstellung mit ungültigem Traffic Split"""
        config = ExperimentConfig(
            name="Test Experiment",
            type="ab",
            variants={"A": "variant_a", "B": "variant_b"},
            traffic_split={"A": 0.3, "B": 0.4}  # Summe != 1.0
        )
        
        with pytest.raises(ValueError):
            manager.create_experiment(config)
    
    def test_start_experiment(self, manager):
        """Test Experiment-Start"""
        # Erstelle Experiment
        config = ExperimentConfig(
            name="Test Experiment",
            type="ab",
            variants={"A": "variant_a", "B": "variant_b"},
            traffic_split={"A": 0.5, "B": 0.5}
        )
        experiment_id = manager.create_experiment(config)
        
        # Starte Experiment
        success = manager.start_experiment(experiment_id)
        assert success is True
        
        # Prüfe Status
        status = manager.get_experiment_status(experiment_id)
        assert status.status == "running"
    
    def test_start_nonexistent_experiment(self, manager):
        """Test Start eines nicht existierenden Experiments"""
        success = manager.start_experiment("nonexistent_id")
        assert success is False
    
    def test_stop_experiment(self, manager):
        """Test Experiment-Stop"""
        # Erstelle und starte Experiment
        config = ExperimentConfig(
            name="Test Experiment",
            type="ab",
            variants={"A": "variant_a", "B": "variant_b"},
            traffic_split={"A": 0.5, "B": 0.5}
        )
        experiment_id = manager.create_experiment(config)
        manager.start_experiment(experiment_id)
        
        # Stoppe Experiment
        success = manager.stop_experiment(experiment_id)
        assert success is True
        
        # Prüfe Status
        status = manager.get_experiment_status(experiment_id)
        assert status.status == "stopped"
    
    def test_list_experiments(self, manager):
        """Test Experiment-Liste"""
        # Erstelle mehrere Experimente
        for i in range(3):
            config = ExperimentConfig(
                name=f"Test Experiment {i}",
                type="ab",
                variants={"A": "variant_a", "B": "variant_b"},
                traffic_split={"A": 0.5, "B": 0.5}
            )
            manager.create_experiment(config)
        
        # Liste alle Experimente
        experiments = manager.list_experiments()
        assert len(experiments) == 3
        
        # Liste nur laufende Experimente
        running_experiments = manager.list_experiments(status="running")
        assert len(running_experiments) == 0  # Keine gestartet
    
    def test_evaluate_experiment(self, manager):
        """Test Experiment-Auswertung"""
        # Erstelle und starte Experiment
        config = ExperimentConfig(
            name="Test Experiment",
            type="ab",
            variants={"A": "variant_a", "B": "variant_b"},
            traffic_split={"A": 0.5, "B": 0.5}
        )
        experiment_id = manager.create_experiment(config)
        manager.start_experiment(experiment_id)
        
        # Evaluiere Experiment (sollte None zurückgeben ohne Daten)
        result = manager.evaluate_experiment(experiment_id)
        assert result is None  # Keine Metriken vorhanden
    
    def test_check_guardrails(self, manager):
        """Test Guardrail-Prüfung"""
        # Erstelle und starte Experiment
        config = ExperimentConfig(
            name="Test Experiment",
            type="ab",
            variants={"A": "variant_a", "B": "variant_b"},
            traffic_split={"A": 0.5, "B": 0.5}
        )
        experiment_id = manager.create_experiment(config)
        manager.start_experiment(experiment_id)
        
        # Prüfe Guardrails
        guardrail_check = manager.check_guardrails(experiment_id)
        
        assert "status" in guardrail_check
        assert "violations" in guardrail_check
        assert guardrail_check["status"] == "ok"  # Keine Metriken = keine Verletzungen

class TestTrafficSplitManager:
    """Tests für TrafficSplitManager"""
    
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
    
    @pytest.fixture
    def manager(self, temp_db):
        from backend.autopilot.metrics import MetricsWriter
        # Mock der get_metrics_writer Funktion
        import backend.autopilot.experiments
        original_writer = backend.autopilot.experiments.get_metrics_writer
        backend.autopilot.experiments.get_metrics_writer = lambda: MetricsWriter(temp_db)
        
        yield TrafficSplitManager()
        
        # Restore
        backend.autopilot.experiments.get_metrics_writer = original_writer
    
    def test_get_variant_for_request(self, manager):
        """Test Varianten-Zuordnung für Anfragen"""
        # Erstelle Experiment
        from backend.autopilot.experiments import ExperimentManager
        exp_manager = ExperimentManager()
        
        config = ExperimentConfig(
            name="Test Experiment",
            type="ab",
            variants={"A": "variant_a", "B": "variant_b"},
            traffic_split={"A": 0.5, "B": 0.5}
        )
        experiment_id = exp_manager.create_experiment(config)
        exp_manager.start_experiment(experiment_id)
        
        # Teste Varianten-Zuordnung
        variant_a = manager.get_variant_for_request(experiment_id, "test_run_1")
        variant_b = manager.get_variant_for_request(experiment_id, "test_run_2")
        
        assert variant_a in ["A", "B"]
        assert variant_b in ["A", "B"]
    
    def test_get_variant_nonexistent_experiment(self, manager):
        """Test Varianten-Zuordnung für nicht existierendes Experiment"""
        variant = manager.get_variant_for_request("nonexistent_id", "test_run")
        assert variant is None
    
    def test_update_traffic_split(self, manager):
        """Test Traffic-Split-Aktualisierung"""
        # Erstelle und starte Experiment
        from backend.autopilot.experiments import ExperimentManager
        exp_manager = ExperimentManager()
        
        config = ExperimentConfig(
            name="Test Experiment",
            type="ab",
            variants={"A": "variant_a", "B": "variant_b"},
            traffic_split={"A": 0.5, "B": 0.5}
        )
        experiment_id = exp_manager.create_experiment(config)
        exp_manager.start_experiment(experiment_id)
        
        # Aktualisiere Traffic Split
        new_split = {"A": 0.7, "B": 0.3}
        success = manager.update_traffic_split(experiment_id, new_split)
        assert success is True
    
    def test_update_traffic_split_invalid(self, manager):
        """Test Traffic-Split-Aktualisierung mit ungültigem Split"""
        # Erstelle und starte Experiment
        from backend.autopilot.experiments import ExperimentManager
        exp_manager = ExperimentManager()
        
        config = ExperimentConfig(
            name="Test Experiment",
            type="ab",
            variants={"A": "variant_a", "B": "variant_b"},
            traffic_split={"A": 0.5, "B": 0.5}
        )
        experiment_id = exp_manager.create_experiment(config)
        exp_manager.start_experiment(experiment_id)
        
        # Ungültiger Split
        invalid_split = {"A": 0.3, "B": 0.4}  # Summe != 1.0
        success = manager.update_traffic_split(experiment_id, invalid_split)
        assert success is False

class TestExperimentScheduler:
    """Tests für ExperimentScheduler"""
    
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
    
    @pytest.fixture
    def scheduler(self, temp_db):
        from backend.autopilot.metrics import MetricsWriter
        # Mock der get_metrics_writer Funktion
        import backend.autopilot.experiments
        original_writer = backend.autopilot.experiments.get_metrics_writer
        backend.autopilot.experiments.get_metrics_writer = lambda: MetricsWriter(temp_db)
        
        yield ExperimentScheduler()
        
        # Restore
        backend.autopilot.experiments.get_metrics_writer = original_writer
    
    def test_check_running_experiments(self, scheduler):
        """Test Überprüfung laufender Experimente"""
        results = scheduler.check_running_experiments()
        
        assert isinstance(results, list)
        # Keine laufenden Experimente
        assert len(results) == 0
    
    def test_schedule_daily_evaluation(self, scheduler):
        """Test tägliche Auswertung"""
        report = scheduler.schedule_daily_evaluation()
        
        assert "timestamp" in report
        assert "total_experiments" in report
        assert "experiments" in report
        assert "summary" in report
        
        assert report["total_experiments"] == 0  # Keine Experimente
        assert report["summary"]["violations"] == 0
        assert report["summary"]["ready_for_evaluation"] == 0
        assert report["summary"]["auto_stopped"] == 0

class TestExperimentConfig:
    """Tests für ExperimentConfig Dataclass"""
    
    def test_experiment_config_creation(self):
        """Test ExperimentConfig Erstellung"""
        config = ExperimentConfig(
            name="Test Experiment",
            type="ab",
            variants={"A": "variant_a", "B": "variant_b"},
            traffic_split={"A": 0.5, "B": 0.5},
            duration_hours=48,
            min_samples=200
        )
        
        assert config.name == "Test Experiment"
        assert config.type == "ab"
        assert config.variants == {"A": "variant_a", "B": "variant_b"}
        assert config.traffic_split == {"A": 0.5, "B": 0.5}
        assert config.duration_hours == 48
        assert config.min_samples == 200
        assert config.success_criteria is not None
        assert config.guardrails is not None
    
    def test_experiment_config_defaults(self):
        """Test ExperimentConfig Standardwerte"""
        config = ExperimentConfig(
            name="Test Experiment",
            type="ab",
            variants={"A": "variant_a"},
            traffic_split={"A": 1.0}
        )
        
        assert config.duration_hours == 24
        assert config.min_samples == 100
        assert config.success_criteria is not None
        assert config.guardrails is not None

class TestExperimentStatus:
    """Tests für ExperimentStatus Dataclass"""
    
    def test_experiment_status_creation(self):
        """Test ExperimentStatus Erstellung"""
        status = ExperimentStatus(
            experiment_id="test_exp",
            status="running",
            start_time=datetime.utcnow(),
            end_time=None
        )
        
        assert status.experiment_id == "test_exp"
        assert status.status == "running"
        assert status.start_time is not None
        assert status.end_time is None
        assert status.current_traffic is None
        assert status.results is None
        assert status.error_message is None
