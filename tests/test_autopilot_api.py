"""
Tests für Autopilot API Router
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

# Import der FastAPI App
import sys
sys.path.append('/Users/ow-winkel/Projects/rico4_local/backend')
from app.main import app


class TestAutopilotAPI:
    """Test-Klasse für Autopilot API Endpunkte"""
    
    def setup_method(self):
        """Setup für jeden Test"""
        self.client = TestClient(app)
    
    def test_get_status_success(self):
        """Test erfolgreiche Status-Abfrage"""
        mock_status = {
            'running': True,
            'tasks_count': 2,
            'enabled_tasks': 1,
            'scheduled_jobs': 1,
            'tasks': [
                {
                    'id': 'test_task',
                    'description': 'Test Task',
                    'schedule': '0 20 * * *',
                    'enabled': True,
                    'task_type': 'analysis',
                    'provider': 'auto'
                }
            ]
        }
        
        with patch('app.routers.autopilot.autopilot_manager') as mock_manager:
            mock_manager.get_status.return_value = mock_status
            
            response = self.client.get("/api/v1/autopilot/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] == True
            assert data['data']['running'] == True
            assert data['data']['tasks_count'] == 2
    
    def test_get_status_error(self):
        """Test Status-Abfrage mit Fehler"""
        with patch('app.routers.autopilot.autopilot_manager') as mock_manager:
            mock_manager.get_status.side_effect = Exception("Test error")
            
            response = self.client.get("/api/v1/autopilot/status")
            
            assert response.status_code == 500
    
    def test_start_autopilot_success(self):
        """Test erfolgreicher Autopilot-Start"""
        with patch('app.routers.autopilot.autopilot_manager') as mock_manager:
            mock_manager.start.return_value = True
            
            response = self.client.post("/api/v1/autopilot/start")
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] == True
            assert "erfolgreich gestartet" in data['message']
    
    def test_start_autopilot_failure(self):
        """Test Autopilot-Start mit Fehler"""
        with patch('app.routers.autopilot.autopilot_manager') as mock_manager:
            mock_manager.start.return_value = False
            
            response = self.client.post("/api/v1/autopilot/start")
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] == False
            assert "konnte nicht gestartet" in data['message']
    
    def test_stop_autopilot_success(self):
        """Test erfolgreicher Autopilot-Stop"""
        with patch('app.routers.autopilot.autopilot_manager') as mock_manager:
            mock_manager.stop.return_value = True
            
            response = self.client.post("/api/v1/autopilot/stop")
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] == True
            assert "erfolgreich gestoppt" in data['message']
    
    def test_stop_autopilot_failure(self):
        """Test Autopilot-Stop mit Fehler"""
        with patch('app.routers.autopilot.autopilot_manager') as mock_manager:
            mock_manager.stop.return_value = False
            
            response = self.client.post("/api/v1/autopilot/stop")
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] == False
            assert "konnte nicht gestoppt" in data['message']
    
    @pytest.mark.asyncio
    async def test_run_task_manually_success(self):
        """Test erfolgreiche manuelle Task-Ausführung"""
        mock_result = {
            'success': True,
            'task_id': 'test_task',
            'result': {'test': 'data'}
        }
        
        with patch('app.routers.autopilot.autopilot_manager') as mock_manager:
            mock_manager.run_task_manually = AsyncMock(return_value=mock_result)
            
            response = self.client.post("/api/v1/autopilot/run-task?task_id=test_task")
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] == True
            assert data['data']['task_id'] == 'test_task'
    
    @pytest.mark.asyncio
    async def test_run_task_manually_error(self):
        """Test manuelle Task-Ausführung mit Fehler"""
        with patch('app.routers.autopilot.autopilot_manager') as mock_manager:
            mock_manager.run_task_manually = AsyncMock(
                side_effect=Exception("Test error")
            )
            
            response = self.client.post("/api/v1/autopilot/run-task?task_id=test_task")
            
            assert response.status_code == 500
    
    def test_get_results_success(self):
        """Test erfolgreiche Ergebnis-Abfrage"""
        mock_results = [
            {
                'task_id': 'task1',
                'success': True,
                'timestamp': '2024-01-01T10:00:00',
                'file': 'task1_20240101_100000.json'
            },
            {
                'task_id': 'task2',
                'success': False,
                'timestamp': '2024-01-01T09:00:00',
                'file': 'task2_20240101_090000.json'
            }
        ]
        
        with patch('app.routers.autopilot.autopilot_manager') as mock_manager:
            mock_manager.get_recent_results.return_value = mock_results
            
            response = self.client.get("/api/v1/autopilot/results?limit=10")
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] == True
            assert len(data['data']) == 2
            assert data['data'][0]['task_id'] == 'task1'
    
    def test_get_results_error(self):
        """Test Ergebnis-Abfrage mit Fehler"""
        with patch('app.routers.autopilot.autopilot_manager') as mock_manager:
            mock_manager.get_recent_results.side_effect = Exception("Test error")
            
            response = self.client.get("/api/v1/autopilot/results")
            
            assert response.status_code == 500
    
    def test_get_tasks_success(self):
        """Test erfolgreiche Task-Liste"""
        mock_tasks = [
            {
                'id': 'task1',
                'description': 'Test Task 1',
                'schedule': '0 20 * * *',
                'enabled': True,
                'task_type': 'analysis',
                'provider': 'auto'
            },
            {
                'id': 'task2',
                'description': 'Test Task 2',
                'schedule': '0 9 * * *',
                'enabled': False,
                'task_type': 'post',
                'provider': 'openai'
            }
        ]
        
        with patch('app.routers.autopilot.autopilot_manager') as mock_manager:
            mock_manager.get_status.return_value = {'tasks': mock_tasks}
            
            response = self.client.get("/api/v1/autopilot/tasks")
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] == True
            assert len(data['data']) == 2
            assert data['data'][0]['id'] == 'task1'
            assert data['data'][1]['enabled'] == False
    
    def test_get_tasks_error(self):
        """Test Task-Liste mit Fehler"""
        with patch('app.routers.autopilot.autopilot_manager') as mock_manager:
            mock_manager.get_status.side_effect = Exception("Test error")
            
            response = self.client.get("/api/v1/autopilot/tasks")
            
            assert response.status_code == 500


if __name__ == "__main__":
    pytest.main([__file__])
