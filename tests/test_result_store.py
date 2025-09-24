"""
Tests für Result Store Helper
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone

from backend.app.services.result_store import write_result, read_latest, read_many


@pytest.fixture
def temp_results_dir():
    """Temporäres Verzeichnis für Test-Results"""
    temp_dir = tempfile.mkdtemp()
    original_cwd = Path.cwd()
    
    # Wechsle in temp-Verzeichnis
    os.chdir(temp_dir)
    
    yield temp_dir
    
    # Cleanup
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)


def test_write_result_success(temp_results_dir):
    """Test erfolgreiches Schreiben eines Results"""
    task_id = "test_task"
    payload = {
        "success": True,
        "duration_sec": 1.5,
        "provider": "openai",
        "task_type": "analysis",
        "notes": "Test erfolgreich",
        "error": None
    }
    
    filepath = write_result(task_id, payload)
    
    # Prüfe dass Pfad zurückgegeben wird
    assert filepath != ""
    assert Path(filepath).exists()
    
    # Prüfe Datei-Inhalt
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert data["ok"] == True
    assert data["status"] == "success"
    assert data["duration_sec"] == 1.5
    assert data["provider"] == "openai"
    assert data["prompt_type"] == "analysis"
    assert data["notes"] == "Test erfolgreich"
    assert data["error"] is None
    assert "ts" in data
    assert data["ts"].endswith("Z")


def test_write_result_error(temp_results_dir):
    """Test Schreiben eines Error-Results"""
    task_id = "error_task"
    payload = {
        "success": False,
        "duration_sec": 0.5,
        "provider": "claude",
        "error": "Test-Fehler"
    }
    
    filepath = write_result(task_id, payload)
    
    assert filepath != ""
    assert Path(filepath).exists()
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert data["ok"] == False
    assert data["status"] == "error"
    assert data["error"] == "Test-Fehler"


def test_read_latest(temp_results_dir):
    """Test Lesen des neuesten Results"""
    task_id = "latest_test"
    
    # Schreibe mehrere Results
    write_result(task_id, {"success": True, "notes": "Erstes"})
    write_result(task_id, {"success": True, "notes": "Zweites"})
    write_result(task_id, {"success": False, "notes": "Drittes"})
    
    # Lese latest
    latest = read_latest(task_id)
    
    assert latest is not None
    assert latest["notes"] == "Drittes"  # Sollte das neueste sein


def test_read_many(temp_results_dir):
    """Test Lesen mehrerer Results"""
    task_id = "many_test"
    
    # Schreibe mehrere Results
    for i in range(5):
        write_result(task_id, {"success": True, "notes": f"Result {i}"})
    
    # Lese alle
    many = read_many(task_id, limit=10)
    assert len(many) == 5
    
    # Prüfe Sortierung (neueste zuerst)
    assert many[0]["notes"] == "Result 4"
    assert many[4]["notes"] == "Result 0"
    
    # Test mit Limit
    limited = read_many(task_id, limit=3)
    assert len(limited) == 3
    assert limited[0]["notes"] == "Result 4"


def test_read_nonexistent_task(temp_results_dir):
    """Test Lesen von nicht existierendem Task"""
    latest = read_latest("nonexistent")
    assert latest is None
    
    many = read_many("nonexistent", limit=5)
    assert many == []


def test_error_handling(temp_results_dir):
    """Test Fehlerbehandlung"""
    # Test mit ungültigen Daten
    filepath = write_result("", {})  # Leere task_id
    assert filepath == ""
    
    # Test mit None-Werten
    filepath = write_result("test", {
        "success": None,
        "duration_sec": None,
        "provider": None
    })
    
    # Sollte trotzdem funktionieren
    assert filepath != ""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert data["ok"] == False  # None wird zu False
    assert data["duration_sec"] is None
    assert data["provider"] is None


def test_directory_creation(temp_results_dir):
    """Test automatische Ordner-Erstellung"""
    task_id = "new_task"
    payload = {"success": True}
    
    # Schreibe Result (sollte Ordner erstellen)
    filepath = write_result(task_id, payload)
    
    # Prüfe dass Ordner erstellt wurde
    task_dir = Path("data/results") / task_id
    assert task_dir.exists()
    assert task_dir.is_dir()
    
    # Prüfe dass Datei im Ordner liegt
    assert Path(filepath).parent == task_dir
