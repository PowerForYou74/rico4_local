"""
Tests für Export-Utility
"""

import json
import tempfile
from pathlib import Path
import pytest
from datetime import datetime, timezone

from backend.app.utils.exporter import (
    ensure_dir, is_tabular, sanitize_filename, timestamp,
    write_json, write_csv, export_result, cleanup_old_exports
)


class TestExporter:
    """Test-Klasse für Export-Utility"""
    
    def test_ensure_dir(self):
        """Test Verzeichnis-Erstellung"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / "test_export"
            ensure_dir(test_dir)
            assert test_dir.exists()
            assert test_dir.is_dir()
    
    def test_is_tabular(self):
        """Test tabellarische Daten-Erkennung"""
        # Tabellarische Daten
        tabular_data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        assert is_tabular(tabular_data) is True
        
        # Nicht-tabellarische Daten
        non_tabular_data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob"}  # Fehlender Key
        ]
        assert is_tabular(non_tabular_data) is False
        
        # Leere Liste
        assert is_tabular([]) is False
        
        # Einzelnes Element
        assert is_tabular([{"name": "Alice"}]) is True
        
        # Nicht-Liste
        assert is_tabular({"name": "Alice"}) is False
    
    def test_sanitize_filename(self):
        """Test Dateiname-Sanitization"""
        assert sanitize_filename("test_file.json") == "test_file.json"
        assert sanitize_filename("test file.json") == "test_file.json"
        assert sanitize_filename("test/file.json") == "test_file.json"
        assert sanitize_filename("test@file.json") == "test_file.json"
        assert sanitize_filename("test___file.json") == "test_file.json"
        assert sanitize_filename("") == "export"
        assert sanitize_filename("   ") == "export"
    
    def test_timestamp(self):
        """Test Zeitstempel-Format"""
        ts = timestamp()
        assert len(ts) == 15  # YYYYMMDD-HHMMSS
        assert ts.count('-') == 1
        assert ts.count(':') == 0  # Keine Doppelpunkte
    
    def test_write_json(self):
        """Test JSON-Export"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            test_data = {"test": "data", "number": 42}
            
            result_path = write_json(base_dir, "test_task", test_data)
            
            assert result_path.exists()
            assert result_path.suffix == ".json"
            assert "test_task" in result_path.name
            
            # Inhalt prüfen
            with open(result_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            assert loaded_data == test_data
    
    def test_write_csv(self):
        """Test CSV-Export"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            test_data = [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25}
            ]
            
            result_path = write_csv(base_dir, "test_task", test_data)
            
            assert result_path.exists()
            assert result_path.suffix == ".csv"
            assert "test_task" in result_path.name
            
            # CSV-Inhalt prüfen (Spalten werden alphabetisch sortiert)
            with open(result_path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert "age,name" in content  # Alphabetisch sortiert
            assert "30,Alice" in content
            assert "25,Bob" in content
    
    def test_export_result_json_only(self):
        """Test Export nur JSON"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            test_data = {"test": "data"}
            
            result = export_result(base_dir, "test_task", test_data, want_csv=False)
            
            assert result["task_id"] == "test_task"
            assert result["json"] is not None
            assert result["csv"] is None
            assert result["size_json"] > 0
            assert result["size_csv"] is None
            assert "created_at" in result
            
            # JSON-Datei prüfen
            json_path = base_dir / result["json"]
            assert json_path.exists()
    
    def test_export_result_with_csv(self):
        """Test Export mit JSON und CSV"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            test_data = [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25}
            ]
            
            result = export_result(base_dir, "test_task", test_data, want_csv=True)
            
            assert result["task_id"] == "test_task"
            assert result["json"] is not None
            assert result["csv"] is not None
            assert result["size_json"] > 0
            assert result["size_csv"] > 0
            
            # Beide Dateien prüfen
            json_path = base_dir / result["json"]
            csv_path = base_dir / result["csv"]
            assert json_path.exists()
            assert csv_path.exists()
    
    def test_export_result_no_csv_for_non_tabular(self):
        """Test dass CSV nicht erstellt wird für nicht-tabellarische Daten"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            test_data = {"test": "data"}  # Nicht-tabellarisch
            
            result = export_result(base_dir, "test_task", test_data, want_csv=True)
            
            assert result["task_id"] == "test_task"
            assert result["json"] is not None
            assert result["csv"] is None  # Sollte None sein
            assert result["size_json"] > 0
            assert result["size_csv"] is None
    
    def test_cleanup_old_exports(self):
        """Test Cleanup alter Export-Dateien"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            
            # Alte Datei erstellen (vor 2 Tagen)
            old_file = base_dir / "old_export.json"
            with open(old_file, 'w') as f:
                json.dump({"old": "data"}, f)
            
            # Zeitstempel auf vor 2 Tagen setzen
            old_time = datetime.now(timezone.utc).timestamp() - (2 * 24 * 3600)
            old_file.touch()
            # Zeitstempel über os.utime setzen
            import os
            os.utime(old_file, (old_time, old_time))
            
            # Neue Datei erstellen
            new_file = base_dir / "new_export.json"
            with open(new_file, 'w') as f:
                json.dump({"new": "data"}, f)
            
            # Cleanup mit 1 Tag Aufbewahrung
            result = cleanup_old_exports(base_dir, keep_days=1)
            
            assert result["deleted_files"] == 1
            assert result["freed_bytes"] > 0
            assert not old_file.exists()
            assert new_file.exists()  # Neue Datei sollte bleiben
