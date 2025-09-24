"""
Tests für AutopilotManager
"""

import pytest
import asyncio
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Import des AutopilotManagers
import sys
sys.path.append('/Users/ow-winkel/Projects/rico4_local/backend')
from app.autopilot import AutopilotManager


class TestAutopilotManager:
    """Test-Klasse für AutopilotManager"""
    
    def setup_method(self):
        """Setup für jeden Test"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "config.yaml"
        self.results_dir = Path(self.temp_dir) / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Test-Konfiguration
        self.test_config = {
            'tasks': [
                {
                    'id': 'test_task',
                    'description': 'Test Task',
                    'schedule': '0 20 * * *',
                    'enabled': True,
                    'provider': 'auto',
                    'task_type': 'analysis',
                    'prompt': 'Test prompt'
                }
            ]
        }
        
        # Konfiguration schreiben
        with open(self.config_path, 'w') as f:
            yaml.dump(self.test_config, f)
        
        # AutopilotManager mit Test-Pfaden
        self.manager = AutopilotManager(str(self.config_path))
        self.manager.results_dir = self.results_dir
    
    def teardown_method(self):
        """Cleanup nach jedem Test"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_config_success(self):
        """Test erfolgreiches Laden der Konfiguration"""
        assert self.manager.load_config() == True
        assert len(self.manager.tasks_config) == 1
        assert self.manager.tasks_config[0]['id'] == 'test_task'
    
    def test_load_config_file_not_found(self):
        """Test bei fehlender Konfigurationsdatei"""
        manager = AutopilotManager("nonexistent.yaml")
        assert manager.load_config() == False
    
    def test_load_config_invalid_yaml(self):
        """Test bei ungültigem YAML"""
        with open(self.config_path, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        manager = AutopilotManager(str(self.config_path))
        assert manager.load_config() == False
    
    def test_start_success(self):
        """Test erfolgreicher Start"""
        with patch.object(self.manager.scheduler, 'start'):
            with patch.object(self.manager, '_schedule_task', return_value=True):
                result = self.manager.start()
                assert result == True
                assert self.manager.is_running == True
    
    def test_start_already_running(self):
        """Test Start wenn bereits laufend"""
        self.manager.is_running = True
        assert self.manager.start() == False
    
    def test_start_config_load_fails(self):
        """Test Start bei fehlgeschlagenem Config-Load"""
        with patch.object(self.manager, 'load_config', return_value=False):
            assert self.manager.start() == False
    
    def test_stop_success(self):
        """Test erfolgreicher Stop"""
        self.manager.is_running = True
        with patch.object(self.manager.scheduler, 'shutdown'):
            result = self.manager.stop()
            assert result == True
            assert self.manager.is_running == False
    
    def test_stop_not_running(self):
        """Test Stop wenn nicht laufend"""
        assert self.manager.stop() == False
    
    def test_schedule_task_success(self):
        """Test erfolgreiche Task-Planung"""
        task = self.test_config['tasks'][0]
        with patch.object(self.manager.scheduler, 'add_job'):
            result = self.manager._schedule_task(task)
            assert result == True
    
    def test_schedule_task_invalid_cron(self):
        """Test Task-Planung mit ungültiger Cron-Syntax"""
        task = self.test_config['tasks'][0].copy()
        task['schedule'] = 'invalid cron'
        
        result = self.manager._schedule_task(task)
        assert result == False
    
    @pytest.mark.asyncio
    async def test_execute_task_success(self):
        """Test erfolgreiche Task-Ausführung"""
        task = self.test_config['tasks'][0]
        
        # Mock für Orchestrator
        mock_result = {
            'success': True,
            'task_id': 'test_task',
            'result': {'test': 'data'}
        }
        
        with patch.object(self.manager.orchestrator, 'run_autopilot_task', 
                         new_callable=AsyncMock, return_value=mock_result):
            
            await self.manager._execute_task(task)
            
            # Prüfe ob Ergebnis gespeichert wurde
            result_files = list(self.results_dir.glob("*.json"))
            assert len(result_files) == 1
    
    @pytest.mark.asyncio
    async def test_execute_task_failure(self):
        """Test Task-Ausführung mit Fehler"""
        task = self.test_config['tasks'][0]
        
        with patch.object(self.manager.orchestrator, 'run_autopilot_task', 
                         new_callable=AsyncMock, side_effect=Exception("Test error")):
            
            await self.manager._execute_task(task)
            
            # Prüfe ob Fehler-Ergebnis gespeichert wurde
            result_files = list(self.results_dir.glob("*.json"))
            assert len(result_files) == 1
            
            # Prüfe Inhalt der Fehler-Datei
            with open(result_files[0], 'r') as f:
                import json
                result = json.load(f)
                assert result['success'] == False
                assert 'Test error' in result['error']
    
    @pytest.mark.asyncio
    async def test_run_task_manually_success(self):
        """Test manuelle Task-Ausführung erfolgreich"""
        self.manager.load_config()
        
        mock_result = {
            'success': True,
            'task_id': 'test_task',
            'result': {'test': 'data'}
        }
        
        with patch.object(self.manager.orchestrator, 'run_autopilot_task', 
                         new_callable=AsyncMock, return_value=mock_result):
            
            result = await self.manager.run_task_manually('test_task')
            assert result['success'] == True
            assert result['task_id'] == 'test_task'
    
    @pytest.mark.asyncio
    async def test_run_task_manually_not_found(self):
        """Test manuelle Task-Ausführung für nicht existierenden Task"""
        self.manager.load_config()
        
        result = await self.manager.run_task_manually('nonexistent_task')
        assert result['success'] == False
        assert 'nicht gefunden' in result['error']
    
    def test_get_status(self):
        """Test Status-Abfrage"""
        self.manager.load_config()
        self.manager.is_running = True
        
        status = self.manager.get_status()
        
        assert status['running'] == True
        assert status['tasks_count'] == 1
        assert status['enabled_tasks'] == 1
        assert len(status['tasks']) == 1
        assert status['tasks'][0]['id'] == 'test_task'
    
    def test_get_recent_results(self):
        """Test Abruf der letzten Ergebnisse"""
        # Erstelle Test-Ergebnisdateien
        test_results = [
            {'task_id': 'task1', 'success': True, 'timestamp': '2024-01-01T10:00:00'},
            {'task_id': 'task2', 'success': False, 'timestamp': '2024-01-01T09:00:00'}
        ]
        
        for i, result in enumerate(test_results):
            filepath = self.results_dir / f"task{i}_20240101_100000.json"
            with open(filepath, 'w') as f:
                import json
                json.dump(result, f)
        
        results = self.manager.get_recent_results(limit=5)
        assert len(results) == 2
        assert results[0]['task_id'] == 'task1'  # Neueste zuerst
        assert results[1]['task_id'] == 'task2'
    
    def test_save_result(self):
        """Test Speichern von Task-Ergebnissen"""
        test_result = {
            'success': True,
            'task_id': 'test_task',
            'result': {'test': 'data'}
        }
        
        self.manager._save_result('test_task', test_result)
        
        # Prüfe ob Datei erstellt wurde
        result_files = list(self.results_dir.glob("test_task_*.json"))
        assert len(result_files) == 1
        
        # Prüfe Inhalt
        with open(result_files[0], 'r') as f:
            import json
            saved_result = json.load(f)
            assert saved_result == test_result


if __name__ == "__main__":
    pytest.main([__file__])
