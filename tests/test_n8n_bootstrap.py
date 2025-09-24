"""
Tests für n8n Bootstrap-Funktionalität
Mock-basierte Tests ohne echte HTTP-Calls
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import json
from pathlib import Path

# Import des Bootstrap-Moduls
import sys
sys.path.append('.')
from integrations.n8n.bootstrap import N8NBootstrap


class TestN8NBootstrap:
    """Test-Klasse für n8n Bootstrap"""
    
    @pytest.fixture
    def mock_workflow_json(self):
        """Mock-Workflow JSON"""
        return {
            "name": "Rico V5 – Event Hub",
            "nodes": [
                {
                    "id": "Webhook_Entry",
                    "name": "Webhook: /webhook/rico-events",
                    "type": "n8n-nodes-base.webhook",
                    "parameters": {"path": "rico-events"}
                }
            ],
            "connections": {}
        }
    
    @pytest.fixture
    def mock_environment(self):
        """Mock-Environment für Tests"""
        with patch.dict('os.environ', {
            'N8N_ENABLED': 'true',
            'N8N_HOST': 'http://localhost:5678',
            'N8N_API_KEY': 'test-api-key',
            'N8N_TIMEOUT_SECONDS': '15'
        }):
            yield
    
    @pytest.mark.asyncio
    async def test_workflow_exists_update_activate(self, mock_workflow_json, mock_environment):
        """Test: Workflow existiert → Update & Activate"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock responses
            mock_client.get.return_value.status_code = 200
            mock_client.get.return_value.json.return_value = [
                {"id": "workflow-123", "name": "Rico V5 – Event Hub", "active": False}
            ]
            
            mock_client.patch.return_value.status_code = 200
            mock_client.patch.return_value.json.return_value = {
                "id": "workflow-123", "name": "Rico V5 – Event Hub", "active": False
            }
            
            mock_client.post.return_value.status_code = 200
            
            # Mock workflow JSON loading
            with patch('pathlib.Path.exists', return_value=True), \
                 patch('builtins.open', mock_open_with_json(mock_workflow_json)):
                
                async with N8NBootstrap() as bootstrap:
                    result = await bootstrap.bootstrap()
                    
                    assert result is True
                    
                    # Verify calls
                    mock_client.get.assert_called()  # Search workflow
                    mock_client.patch.assert_called()  # Update workflow
                    mock_client.post.assert_called()  # Activate workflow
    
    @pytest.mark.asyncio
    async def test_workflow_missing_create_activate(self, mock_workflow_json, mock_environment):
        """Test: Workflow fehlt → Create & Activate"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock responses - kein Workflow gefunden
            mock_client.get.return_value.status_code = 200
            mock_client.get.return_value.json.return_value = []
            
            mock_client.post.return_value.status_code = 201
            mock_client.post.return_value.json.return_value = {
                "id": "workflow-new", "name": "Rico V5 – Event Hub", "active": False
            }
            
            # Mock workflow JSON loading
            with patch('pathlib.Path.exists', return_value=True), \
                 patch('builtins.open', mock_open_with_json(mock_workflow_json)):
                
                async with N8NBootstrap() as bootstrap:
                    result = await bootstrap.bootstrap()
                    
                    assert result is True
                    
                    # Verify calls
                    mock_client.get.assert_called()  # Search workflow
                    mock_client.post.assert_called()  # Create & activate workflow
    
    @pytest.mark.asyncio
    async def test_401_authentication_error(self, mock_environment):
        """Test: 401 → Klarer Fehlertext"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock 401 response
            mock_client.get.return_value.status_code = 401
            
            async with N8NBootstrap() as bootstrap:
                result = await bootstrap.bootstrap()
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_n8n_disabled_no_op(self):
        """Test: N8N_ENABLED=false → no-op"""
        with patch.dict('os.environ', {'N8N_ENABLED': 'false'}):
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                
                async with N8NBootstrap() as bootstrap:
                    result = await bootstrap.bootstrap()
                    
                    # Should return early without making HTTP calls
                    mock_client.get.assert_not_called()
                    assert result is False
    
    @pytest.mark.asyncio
    async def test_connection_timeout(self, mock_environment):
        """Test: Connection timeout handling"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock timeout exception
            mock_client.get.side_effect = asyncio.TimeoutError()
            
            async with N8NBootstrap() as bootstrap:
                result = await bootstrap.bootstrap()
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_workflow_json_not_found(self, mock_environment):
        """Test: Workflow JSON Datei nicht gefunden"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock file not found
            with patch('pathlib.Path.exists', return_value=False):
                async with N8NBootstrap() as bootstrap:
                    result = await bootstrap.bootstrap()
                    
                    assert result is False


def mock_open_with_json(json_data):
    """Helper: Mock open() mit JSON-Daten"""
    from unittest.mock import mock_open
    return mock_open(read_data=json.dumps(json_data))


class TestN8NBootstrapIntegration:
    """Integration-Tests für Bootstrap (Mock-basiert)"""
    
    @pytest.mark.asyncio
    async def test_bootstrap_with_mock_n8n(self):
        """Test: Kompletter Bootstrap-Prozess mit Mock n8n"""
        with patch.dict('os.environ', {
            'N8N_ENABLED': 'true',
            'N8N_HOST': 'http://localhost:5678',
            'N8N_API_KEY': 'test-key'
        }):
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                
                # Mock successful workflow creation
                mock_client.get.return_value.status_code = 200
                mock_client.get.return_value.json.return_value = []
                
                mock_client.post.return_value.status_code = 201
                mock_client.post.return_value.json.return_value = {
                    "id": "workflow-123", "name": "Rico V5 – Event Hub", "active": True
                }
                
                # Mock workflow file
                workflow_data = {
                    "name": "Rico V5 – Event Hub",
                    "nodes": [{"id": "test", "type": "webhook"}],
                    "connections": {}
                }
                
                with patch('pathlib.Path.exists', return_value=True), \
                     patch('builtins.open', mock_open_with_json(workflow_data)):
                    
                    async with N8NBootstrap() as bootstrap:
                        result = await bootstrap.bootstrap()
                        
                        assert result is True
                        
                        # Verify all required calls were made
                        assert mock_client.get.call_count >= 1  # Search workflows
                        assert mock_client.post.call_count >= 2  # Create + activate


if __name__ == "__main__":
    # Einfacher Test-Runner für manuelle Tests
    import asyncio
    
    async def run_manual_test():
        """Manueller Test ohne Mocks (nur wenn n8n läuft)"""
        print("Running manual n8n bootstrap test...")
        
        # Set test environment
        import os
        os.environ.update({
            'N8N_ENABLED': 'true',
            'N8N_HOST': 'http://localhost:5678',
            'N8N_API_KEY': 'test-key'
        })
        
        async with N8NBootstrap() as bootstrap:
            result = await bootstrap.bootstrap()
            print(f"Bootstrap result: {result}")
    
    # Nur ausführen wenn direkt aufgerufen
    if __name__ == "__main__":
        print("n8n Bootstrap Tests")
        print("Run with pytest for full test suite:")
        print("pytest tests/test_n8n_bootstrap.py -v")
