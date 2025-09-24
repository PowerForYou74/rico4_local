"""
Tests für Monitor API
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.result_store import write_result, read_latest, read_many


@pytest.fixture
def client():
    """Test-Client für FastAPI"""
    return TestClient(app)


@pytest.fixture
def temp_results_dir():
    """Temporäres Verzeichnis für Test-Results"""
    temp_dir = tempfile.mkdtemp()
    original_dir = "data/results"
    
    # Erstelle Test-Struktur
    test_dir = Path(temp_dir) / "data" / "results"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    yield str(test_dir)
    
    # Cleanup
    shutil.rmtree(temp_dir)


def test_monitor_status_endpoint(client):
    """Test /api/monitor/status Endpoint"""
    response = client.get("/api/monitor/status")
    
    assert response.status_code == 200
    data = response.json()
    
    # Prüfe Pflichtfelder
    assert "autopilot_running" in data
    assert "total_tasks" in data
    assert "active_tasks" in data
    assert "next_runs" in data
    assert "last_updated" in data
    
    # Prüfe Datentypen
    assert isinstance(data["autopilot_running"], bool)
    assert isinstance(data["total_tasks"], int)
    assert isinstance(data["active_tasks"], int)
    assert isinstance(data["next_runs"], list)
    assert isinstance(data["last_updated"], str)
    
    # Prüfe ISO8601Z Format
    assert data["last_updated"].endswith("Z")


def test_monitor_tasks_endpoint(client):
    """Test /api/monitor/tasks Endpoint"""
    response = client.get("/api/monitor/tasks")
    
    assert response.status_code == 200
    data = response.json()
    
    # Sollte Liste sein
    assert isinstance(data, list)
    
    # Wenn Tasks vorhanden, prüfe Schema
    if data:
        task = data[0]
        assert "id" in task
        assert "title" in task
        assert "schedule" in task
        assert "enabled" in task
        assert "provider" in task
        assert "type" in task
        assert "last_run" in task
        assert "last_status" in task
        assert "last_duration_sec" in task
        
        # Prüfe Status-Werte
        assert task["last_status"] in ["success", "error", "pending", "stale"]


def test_monitor_logs_endpoint(client):
    """Test /api/monitor/logs Endpoint"""
    # Test mit existierendem Task
    response = client.get("/api/monitor/logs?task_id=test_task&limit=5")
    
    assert response.status_code == 200
    data = response.json()
    
    # Sollte Liste sein
    assert isinstance(data, list)
    
    # Wenn Logs vorhanden, prüfe Schema
    if data:
        log = data[0]
        assert "ts" in log
        assert "status" in log
        assert "duration_sec" in log
        assert "provider" in log
        assert "notes" in log
        assert "error" in log
        
        # Prüfe Status-Werte
        assert log["status"] in ["success", "error"]


def test_monitor_logs_missing_task(client):
    """Test /api/monitor/logs mit nicht existierendem Task"""
    response = client.get("/api/monitor/logs?task_id=nonexistent_task&limit=5")
    
    assert response.status_code == 200
    data = response.json()
    
    # Sollte leere Liste zurückgeben
    assert isinstance(data, list)
    assert len(data) == 0


def test_result_store_write_read(temp_results_dir):
    """Test Result Store write/read Funktionen"""
    import os
    os.chdir(Path(temp_results_dir).parent.parent)
    
    # Test-Daten
    task_id = "test_task"
    payload = {
        "success": True,
        "duration_sec": 1.5,
        "provider": "openai",
        "task_type": "analysis",
        "notes": "Test erfolgreich",
        "error": None
    }
    
    # Schreibe Result
    filepath = write_result(task_id, payload)
    assert filepath != ""
    assert Path(filepath).exists()
    
    # Lese latest
    latest = read_latest(task_id)
    assert latest is not None
    assert latest["ok"] == True
    assert latest["status"] == "success"
    assert latest["duration_sec"] == 1.5
    assert latest["provider"] == "openai"
    
    # Schreibe weitere Results
    write_result(task_id, {
        "success": False,
        "duration_sec": 2.0,
        "provider": "claude",
        "error": "Test-Fehler"
    })
    
    # Lese viele
    many = read_many(task_id, limit=10)
    assert len(many) == 2
    
    # Neuestes sollte das letzte sein
    assert many[0]["status"] == "error"
    assert many[1]["status"] == "success"


def test_result_store_error_handling(temp_results_dir):
    """Test Result Store Fehlerbehandlung"""
    import os
    os.chdir(Path(temp_results_dir).parent.parent)
    
    # Test mit ungültigen Daten
    filepath = write_result("", {})  # Leere task_id
    assert filepath == ""  # Sollte leeren String zurückgeben
    
    # Test read mit nicht existierendem Task
    latest = read_latest("nonexistent")
    assert latest is None
    
    many = read_many("nonexistent", limit=5)
    assert many == []
