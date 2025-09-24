"""
Integrationstests für Autopilot-Funktionalität
"""

import pytest
import asyncio
import tempfile
import yaml
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

# Import der Module
import sys
sys.path.append('/Users/ow-winkel/Projects/rico4_local/backend')
from app.main import app
from app.autopilot import AutopilotManager


class TestAutopilotIntegration:
    """Integrationstests für das gesamte Autopilot-System"""
    
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
                    'id': 'integration_test_task',
                    'description': 'Integration Test Task',
                    'schedule': '0 20 * * *',
                    'enabled': True,
                    'provider': 'auto',
                    'task_type': 'analysis',
                    'prompt': 'Integration test prompt'
                },
                {
                    'id': 'disabled_task',
                    'description': 'Disabled Task',
                    'schedule': '0 9 * * *',
                    'enabled': False,
                    'provider': 'openai',
                    'task_type': 'post',
                    'prompt': 'Disabled task prompt'
                }
            ],
            'exports': {
                'enabled': True,
                'dir': str(Path(self.temp_dir) / 'exports'),
                'formats': ['json', 'csv'],
                'keep_days': 7
            }
        }
        
        # Konfiguration schreiben
        with open(self.config_path, 'w') as f:
            yaml.dump(self.test_config, f)
        
        self.client = TestClient(app)
    
    def teardown_method(self):
        """Cleanup nach jedem Test"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_full_autopilot_workflow(self):
        """Test des kompletten Autopilot-Workflows"""
        
        # 1. AutopilotManager mit Test-Konfiguration erstellen
        manager = AutopilotManager(str(self.config_path))
        manager.results_dir = self.results_dir
        
        # 2. Konfiguration laden
        assert manager.load_config() == True
        assert len(manager.tasks_config) == 2
        
        # 3. Mock für Orchestrator
        mock_result = {
            'success': True,
            'task_id': 'integration_test_task',
            'task_type': 'analysis',
            'provider': 'openai',
            'timestamp': '2024-01-01T20:00:00',
            'result': {
                'kurz_zusammenfassung': 'Integration test erfolgreich',
                'kernbefunde': ['Test erfolgreich'],
                'action_plan': ['Nächste Schritte'],
                'risiken': [],
                'cashflow_radar': {'idee': 'Test-Idee'},
                'team_rolle': {'openai': True, 'claude': False},
                'aufgabenverteilung': ['Task 1', 'Task 2']
            }
        }
        
        with patch.object(manager.orchestrator, 'run_autopilot_task', 
                         new_callable=AsyncMock, return_value=mock_result):
            
            # 4. Autopilot starten
            with patch.object(manager.scheduler, 'start'):
                with patch.object(manager, '_schedule_task', return_value=True):
                    assert manager.start() == True
                    assert manager.is_running == True
            
            # 5. Status prüfen
            status = manager.get_status()
            assert status['running'] == True
            assert status['tasks_count'] == 2
            assert status['enabled_tasks'] == 1
            assert len(status['tasks']) == 2
            
            # 6. Task manuell ausführen
            result = await manager.run_task_manually('integration_test_task')
            assert result['success'] == True
            assert result['task_id'] == 'integration_test_task'
            
            # 7. Ergebnis prüfen
            result_files = list(self.results_dir.glob("*.json"))
            assert len(result_files) == 1
            
            with open(result_files[0], 'r') as f:
                saved_result = json.load(f)
                assert saved_result['success'] == True
                assert saved_result['task_id'] == 'integration_test_task'
            
            # 8. Autopilot stoppen
            with patch.object(manager.scheduler, 'shutdown'):
                assert manager.stop() == True
                assert manager.is_running == False
    
    def test_api_endpoints_integration(self):
        """Test der API-Endpunkte mit Mock-Daten"""
        
        # Mock für AutopilotManager
        mock_manager = Mock()
        mock_manager.get_status.return_value = {
            'running': True,
            'tasks_count': 2,
            'enabled_tasks': 1,
            'scheduled_jobs': 1,
            'tasks': [
                {
                    'id': 'api_test_task',
                    'description': 'API Test Task',
                    'schedule': '0 20 * * *',
                    'enabled': True,
                    'task_type': 'analysis',
                    'provider': 'auto'
                }
            ]
        }
        
        mock_manager.get_recent_results.return_value = [
            {
                'task_id': 'api_test_task',
                'success': True,
                'timestamp': '2024-01-01T20:00:00',
                'file': 'api_test_task_20240101_200000.json'
            }
        ]
        
        with patch('app.routers.autopilot.autopilot_manager', mock_manager):
            
            # Test Status-Endpunkt
            response = self.client.get("/api/v1/autopilot/status")
            assert response.status_code == 200
            data = response.json()
            assert data['success'] == True
            assert data['data']['running'] == True
            
            # Test Tasks-Endpunkt
            response = self.client.get("/api/v1/autopilot/tasks")
            assert response.status_code == 200
            data = response.json()
            assert data['success'] == True
            assert len(data['data']) == 1
            assert data['data'][0]['id'] == 'api_test_task'
            
            # Test Results-Endpunkt
            response = self.client.get("/api/v1/autopilot/results")
            assert response.status_code == 200
            data = response.json()
            assert data['success'] == True
            assert len(data['data']) == 1
            assert data['data'][0]['task_id'] == 'api_test_task'
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """Test der Fehlerbehandlung im gesamten System"""
        
        manager = AutopilotManager(str(self.config_path))
        manager.results_dir = self.results_dir
        manager.load_config()
        
        # Test 1: Orchestrator-Fehler
        with patch.object(manager.orchestrator, 'run_autopilot_task', 
                         new_callable=AsyncMock, side_effect=Exception("Orchestrator error")):
            
            result = await manager.run_task_manually('integration_test_task')
            assert result['success'] == False
            assert 'Orchestrator error' in result['error']
            
            # Prüfe ob Fehler-Ergebnis gespeichert wurde
            result_files = list(self.results_dir.glob("*.json"))
            assert len(result_files) == 1
            
            with open(result_files[0], 'r') as f:
                saved_result = json.load(f)
                assert saved_result['success'] == False
                assert 'Orchestrator error' in saved_result['error']
        
        # Cleanup für nächsten Test
        for f in self.results_dir.glob("*.json"):
            f.unlink()
        
        # Test 2: Ungültiger Task-ID
        result = await manager.run_task_manually('nonexistent_task')
        assert result['success'] == False
        assert 'nicht gefunden' in result['error']
        
        # Test 3: API-Fehler
        with patch('app.routers.autopilot.autopilot_manager') as mock_manager:
            mock_manager.get_status.side_effect = Exception("API error")
            
            response = self.client.get("/api/v1/autopilot/status")
            assert response.status_code == 500
    
    def test_config_validation(self):
        """Test der Konfigurationsvalidierung"""
        
        # Test 1: Gültige Konfiguration
        manager = AutopilotManager(str(self.config_path))
        assert manager.load_config() == True
        
        # Test 2: Ungültige Cron-Syntax
        invalid_config = self.test_config.copy()
        invalid_config['tasks'][0]['schedule'] = 'invalid cron syntax'
        
        with open(self.config_path, 'w') as f:
            yaml.dump(invalid_config, f)
        
        manager = AutopilotManager(str(self.config_path))
        assert manager.load_config() == True
        
        # Task-Planung sollte fehlschlagen
        task = manager.tasks_config[0]
        result = manager._schedule_task(task)
        assert result == False
        
        # Test 3: Fehlende Pflichtfelder
        incomplete_config = {
            'tasks': [
                {
                    'id': 'incomplete_task',
                    # Fehlende Pflichtfelder
                    'schedule': '0 20 * * *'
                }
            ]
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(incomplete_config, f)
        
        manager = AutopilotManager(str(self.config_path))
        assert manager.load_config() == True
        
        # Task-Planung sollte mit Default-Werten funktionieren
        task = manager.tasks_config[0]
        with patch.object(manager.scheduler, 'add_job'):
            result = manager._schedule_task(task)
            assert result == True
    
    @pytest.mark.asyncio
    async def test_concurrent_task_execution(self):
        """Test der gleichzeitigen Task-Ausführung"""
        
        manager = AutopilotManager(str(self.config_path))
        manager.results_dir = self.results_dir
        manager.load_config()
        
        # Mock für Orchestrator mit Verzögerung
        async def delayed_task(task):
            await asyncio.sleep(0.1)  # Simuliere Verarbeitungszeit
            return {
                'success': True,
                'task_id': task['id'],
                'result': {'test': 'data'}
            }
        
        with patch.object(manager.orchestrator, 'run_autopilot_task', 
                         side_effect=delayed_task):
            
            # Starte mehrere Tasks gleichzeitig
            tasks = [
                asyncio.create_task(manager.run_task_manually('integration_test_task')),
                asyncio.create_task(manager.run_task_manually('integration_test_task')),
                asyncio.create_task(manager.run_task_manually('integration_test_task'))
            ]
            
            # Warte auf alle Tasks
            results = await asyncio.gather(*tasks)
            
            # Prüfe Ergebnisse
            for result in results:
                assert result['success'] == True
                assert result['task_id'] == 'integration_test_task'
            
            # Prüfe ob alle Ergebnisse gespeichert wurden
            result_files = list(self.results_dir.glob("*.json"))
            assert len(result_files) == 3
    
    @pytest.mark.asyncio
    async def test_export_functionality_integration(self):
        """Test der Export-Funktionalität im Autopilot-System"""
        
        manager = AutopilotManager(str(self.config_path))
        manager.results_dir = self.results_dir
        manager.load_config()
        
        # Prüfe Export-Konfiguration
        assert manager.export_config['enabled'] == True
        assert 'json' in manager.export_config['formats']
        assert 'csv' in manager.export_config['formats']
        
        # Mock für Orchestrator mit tabellarischen Daten
        mock_result = {
            'success': True,
            'task_id': 'integration_test_task',
            'task_type': 'analysis',
            'provider': 'openai',
            'timestamp': '2024-01-01T20:00:00',
            'result': [
                {'name': 'Alice', 'age': 30, 'city': 'Berlin'},
                {'name': 'Bob', 'age': 25, 'city': 'München'},
                {'name': 'Charlie', 'age': 35, 'city': 'Hamburg'}
            ]
        }
        
        with patch.object(manager.orchestrator, 'run_autopilot_task', 
                         new_callable=AsyncMock, return_value=mock_result):
            
            # Task ausführen
            result = await manager.run_task_manually('integration_test_task')
            assert result['success'] == True
            
            # Prüfe Export-Metadaten
            assert 'export_files' in result
            export_meta = result['export_files']
            assert export_meta['task_id'] == 'integration_test_task'
            assert export_meta['json'] is not None
            assert export_meta['csv'] is not None  # Sollte CSV erstellt werden
            assert export_meta['size_json'] > 0
            assert export_meta['size_csv'] > 0
            
            # Prüfe Export-Dateien
            export_dir = Path(manager.export_config['dir'])
            assert export_dir.exists()
            
            json_file = export_dir / export_meta['json']
            csv_file = export_dir / export_meta['csv']
            
            assert json_file.exists()
            assert csv_file.exists()
            
            # JSON-Inhalt prüfen
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                assert len(json_data) == 3
                assert json_data[0]['name'] == 'Alice'
            
            # CSV-Inhalt prüfen
            with open(csv_file, 'r', encoding='utf-8') as f:
                csv_content = f.read()
                assert 'name,age,city' in csv_content
                assert 'Alice,30,Berlin' in csv_content
                assert 'Bob,25,München' in csv_content
    
    @pytest.mark.asyncio
    async def test_export_api_integration(self):
        """Test der Export-API-Endpunkte"""
        
        # Export-Verzeichnis und Test-Dateien erstellen
        export_dir = Path(self.temp_dir) / 'exports'
        export_dir.mkdir(exist_ok=True)
        
        # Test-Dateien erstellen
        json_file = export_dir / 'test_task__20240101-120000.json'
        csv_file = export_dir / 'test_task__20240101-120000.csv'
        
        with open(json_file, 'w') as f:
            json.dump({'test': 'data'}, f)
        
        with open(csv_file, 'w') as f:
            f.write('name,age\nAlice,30\n')
        
        # Mock für AutopilotManager
        mock_manager = Mock()
        mock_manager.export_config = {'dir': str(export_dir)}
        
        with patch('app.routers.autopilot.autopilot_manager', mock_manager):
            
            # Test Export-Liste
            response = self.client.get("/api/v1/autopilot/exports/list")
            assert response.status_code == 200
            data = response.json()
            assert data['success'] == True
            assert data['count'] == 2
            
            files = data['data']
            assert len(files) == 2
            
            # Prüfe Datei-Informationen
            for file_info in files:
                assert 'task_id' in file_info
                assert 'filename' in file_info
                assert 'size' in file_info
                assert 'url' in file_info
                assert file_info['task_id'] == 'test_task'
            
            # Test Export-Download
            response = self.client.get(f"/api/v1/autopilot/exports/download?file={json_file.name}")
            assert response.status_code == 200
            assert response.headers['content-type'] == 'application/json'
            
            # Test CSV-Download
            response = self.client.get(f"/api/v1/autopilot/exports/download?file={csv_file.name}")
            assert response.status_code == 200
            assert response.headers['content-type'] == 'text/csv'
            assert 'Alice,30' in response.text
            
            # Test Filter nach Task-ID
            response = self.client.get("/api/v1/autopilot/exports/list?task_id=test_task")
            assert response.status_code == 200
            data = response.json()
            assert data['count'] == 2
            
            # Test Filter nach nicht existierender Task-ID
            response = self.client.get("/api/v1/autopilot/exports/list?task_id=nonexistent")
            assert response.status_code == 200
            data = response.json()
            assert data['count'] == 0


if __name__ == "__main__":
    pytest.main([__file__])
