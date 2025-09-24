"""
Tests für Export-API-Endpunkte
"""

import json
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from backend.app.main import app
from backend.app.autopilot import autopilot_manager


class TestExportsAPI:
    """Test-Klasse für Export-API"""
    
    @pytest.fixture
    def client(self):
        """FastAPI Test Client"""
        return TestClient(app)
    
    @pytest.fixture
    def temp_export_dir(self):
        """Temporäres Export-Verzeichnis"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    def test_list_exports_empty(self, client, temp_export_dir):
        """Test leere Export-Liste"""
        with patch.object(autopilot_manager, 'export_config', {'dir': str(temp_export_dir)}):
            response = client.get("/api/v1/autopilot/exports/list")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"] == []
            assert data["count"] == 0
    
    def test_list_exports_with_files(self, client, temp_export_dir):
        """Test Export-Liste mit Dateien"""
        # Test-Dateien erstellen
        json_file = temp_export_dir / "test_task__20240101-120000.json"
        csv_file = temp_export_dir / "test_task__20240101-120000.csv"
        
        with open(json_file, 'w') as f:
            json.dump({"test": "data"}, f)
        
        with open(csv_file, 'w') as f:
            f.write("name,age\nAlice,30\n")
        
        with patch.object(autopilot_manager, 'export_config', {'dir': str(temp_export_dir)}):
            response = client.get("/api/v1/autopilot/exports/list")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["count"] == 2
            
            files = data["data"]
            assert len(files) == 2
            
            # Prüfe Datei-Informationen
            for file_info in files:
                assert "task_id" in file_info
                assert "filename" in file_info
                assert "size" in file_info
                assert "created_at" in file_info
                assert "url" in file_info
                assert file_info["task_id"] == "test_task"
    
    def test_list_exports_with_task_filter(self, client, temp_export_dir):
        """Test Export-Liste mit Task-Filter"""
        # Verschiedene Task-Dateien erstellen
        task1_file = temp_export_dir / "task1__20240101-120000.json"
        task2_file = temp_export_dir / "task2__20240101-120000.json"
        
        with open(task1_file, 'w') as f:
            json.dump({"task": "1"}, f)
        
        with open(task2_file, 'w') as f:
            json.dump({"task": "2"}, f)
        
        with patch.object(autopilot_manager, 'export_config', {'dir': str(temp_export_dir)}):
            # Filter nach task1
            response = client.get("/api/v1/autopilot/exports/list?task_id=task1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 1
            assert data["data"][0]["task_id"] == "task1"
    
    def test_list_exports_with_limit(self, client, temp_export_dir):
        """Test Export-Liste mit Limit"""
        # Mehrere Dateien erstellen
        for i in range(5):
            file_path = temp_export_dir / f"task__20240101-12000{i}.json"
            with open(file_path, 'w') as f:
                json.dump({"task": i}, f)
        
        with patch.object(autopilot_manager, 'export_config', {'dir': str(temp_export_dir)}):
            response = client.get("/api/v1/autopilot/exports/list?limit=3")
            
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 3
            assert len(data["data"]) == 3
    
    def test_download_export_success(self, client, temp_export_dir):
        """Test erfolgreicher Export-Download"""
        # Test-Datei erstellen
        test_file = temp_export_dir / "test_task__20240101-120000.json"
        test_data = {"test": "data", "number": 42}
        
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        with patch.object(autopilot_manager, 'export_config', {'dir': str(temp_export_dir)}):
            response = client.get(f"/api/v1/autopilot/exports/download?file={test_file.name}")
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"
            assert response.headers["content-disposition"].startswith("attachment")
            
            # Inhalt prüfen
            downloaded_data = response.json()
            assert downloaded_data == test_data
    
    def test_download_export_csv(self, client, temp_export_dir):
        """Test CSV-Download"""
        # CSV-Datei erstellen
        csv_file = temp_export_dir / "test_task__20240101-120000.csv"
        with open(csv_file, 'w') as f:
            f.write("name,age\nAlice,30\nBob,25\n")
        
        with patch.object(autopilot_manager, 'export_config', {'dir': str(temp_export_dir)}):
            response = client.get(f"/api/v1/autopilot/exports/download?file={csv_file.name}")
            
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/csv")
            assert "Alice,30" in response.text
            assert "Bob,25" in response.text
    
    def test_download_export_not_found(self, client, temp_export_dir):
        """Test Download nicht existierender Datei"""
        with patch.object(autopilot_manager, 'export_config', {'dir': str(temp_export_dir)}):
            response = client.get("/api/v1/autopilot/exports/download?file=nonexistent.json")
            
            assert response.status_code == 404
            data = response.json()
            assert "nicht gefunden" in data["detail"]
    
    def test_download_export_path_traversal(self, client, temp_export_dir):
        """Test Pfad-Traversal-Schutz"""
        with patch.object(autopilot_manager, 'export_config', {'dir': str(temp_export_dir)}):
            # Versuche auf Datei außerhalb des Export-Verzeichnisses zuzugreifen
            response = client.get("/api/v1/autopilot/exports/download?file=../../../etc/passwd")
            
            assert response.status_code in [403, 404]  # Kann 403 oder 404 sein
            data = response.json()
            assert "Zugriff verweigert" in data["detail"] or "nicht gefunden" in data["detail"]
    
    def test_download_export_invalid_file_type(self, client, temp_export_dir):
        """Test Download ungültiger Dateitypen"""
        # Nicht-Export-Datei erstellen
        txt_file = temp_export_dir / "test.txt"
        with open(txt_file, 'w') as f:
            f.write("test content")
        
        with patch.object(autopilot_manager, 'export_config', {'dir': str(temp_export_dir)}):
            response = client.get(f"/api/v1/autopilot/exports/download?file={txt_file.name}")
            
            # Sollte funktionieren, da die Datei existiert
            assert response.status_code == 200
