"""
Tests für Integrations Status API
Mock-basierte Tests für n8n Status-Endpoints
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import sys

# Add project root to path
sys.path.append('.')

from backend.api.v2.integrations import router, check_n8n_health
from backend.main import app


class TestIntegrationsStatus:
    """Test-Klasse für Integrations Status API"""
    
    @pytest.fixture
    def client(self):
        """FastAPI Test Client"""
        return TestClient(app)
    
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
    async def test_n8n_status_enabled_reachable(self, mock_environment):
        """Test: n8n enabled und erreichbar"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock successful response
            mock_client.get.return_value.status_code = 200
            
            result = await check_n8n_health()
            
            assert result['enabled'] is True
            assert result['reachable'] is True
            assert result['api_key_present'] is True
            assert result['host'] == 'http://localhost:5678'
            assert result['error_message'] is None
    
    @pytest.mark.asyncio
    async def test_n8n_status_enabled_not_reachable(self, mock_environment):
        """Test: n8n enabled aber nicht erreichbar"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock connection error
            mock_client.get.side_effect = Exception("Connection failed")
            
            result = await check_n8n_health()
            
            assert result['enabled'] is True
            assert result['reachable'] is False
            assert result['api_key_present'] is True
            assert result['error_message'] == "Connection failed"
    
    @pytest.mark.asyncio
    async def test_n8n_status_disabled(self):
        """Test: n8n disabled"""
        with patch.dict('os.environ', {'N8N_ENABLED': 'false'}):
            result = await check_n8n_health()
            
            assert result['enabled'] is False
            assert result['reachable'] is False
            assert result['api_key_present'] is False
            assert result['error_message'] == "n8n disabled"
    
    @pytest.mark.asyncio
    async def test_n8n_status_401_auth_failed(self, mock_environment):
        """Test: 401 Authentication failed"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock 401 response
            mock_client.get.return_value.status_code = 401
            
            result = await check_n8n_health()
            
            assert result['enabled'] is True
            assert result['reachable'] is True  # Erreichbar, aber auth fehlt
            assert result['api_key_present'] is True
            assert result['error_message'] == "API authentication failed"
    
    @pytest.mark.asyncio
    async def test_n8n_status_403_forbidden(self, mock_environment):
        """Test: 403 Forbidden"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock 403 response
            mock_client.get.return_value.status_code = 403
            
            result = await check_n8n_health()
            
            assert result['enabled'] is True
            assert result['reachable'] is True
            assert result['api_key_present'] is True
            assert result['error_message'] == "API access forbidden"
    
    @pytest.mark.asyncio
    async def test_n8n_status_timeout(self, mock_environment):
        """Test: Timeout handling"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock timeout
            import httpx
            mock_client.get.side_effect = httpx.TimeoutException("Request timeout")
            
            result = await check_n8n_health()
            
            assert result['enabled'] is True
            assert result['reachable'] is False
            assert result['api_key_present'] is True
            assert result['error_message'] == "Connection timeout"
    
    @pytest.mark.asyncio
    async def test_n8n_status_no_api_key(self):
        """Test: Kein API Key gesetzt"""
        with patch.dict('os.environ', {
            'N8N_ENABLED': 'true',
            'N8N_HOST': 'http://localhost:5678',
            'N8N_API_KEY': '',  # Leer
            'N8N_TIMEOUT_SECONDS': '15'
        }):
            result = await check_n8n_health()
            
            assert result['enabled'] is True
            assert result['api_key_present'] is False


class TestIntegrationsAPI:
    """Test-Klasse für Integrations API Endpoints"""
    
    @pytest.fixture
    def client(self):
        """FastAPI Test Client"""
        return TestClient(app)
    
    def test_get_n8n_status_endpoint(self, client):
        """Test: GET /v2/integrations/n8n/status"""
        with patch('backend.api.v2.integrations.check_n8n_health') as mock_check:
            mock_check.return_value = {
                'enabled': True,
                'host': 'http://localhost:5678',
                'reachable': True,
                'api_key_present': True,
                'last_check': '2024-01-01T12:00:00',
                'error_message': None
            }
            
            response = client.get("/v2/integrations/n8n/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data['enabled'] is True
            assert data['reachable'] is True
            assert data['api_key_present'] is True
    
    def test_get_n8n_health_endpoint(self, client):
        """Test: GET /v2/integrations/n8n/health"""
        with patch('backend.api.v2.integrations.check_n8n_health') as mock_check:
            mock_check.return_value = {
                'enabled': True,
                'host': 'http://localhost:5678',
                'reachable': True,
                'api_key_present': True,
                'last_check': '2024-01-01T12:00:00',
                'error_message': None
            }
            
            response = client.get("/v2/integrations/n8n/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'healthy'
            assert 'message' in data
    
    def test_get_n8n_health_disabled(self, client):
        """Test: GET /v2/integrations/n8n/health (disabled)"""
        with patch('backend.api.v2.integrations.check_n8n_health') as mock_check:
            mock_check.return_value = {
                'enabled': False,
                'host': 'http://localhost:5678',
                'reachable': False,
                'api_key_present': False,
                'last_check': '2024-01-01T12:00:00',
                'error_message': 'n8n disabled'
            }
            
            response = client.get("/v2/integrations/n8n/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'disabled'
            assert 'n8n integration disabled' in data['message']
    
    def test_get_n8n_health_error(self, client):
        """Test: GET /v2/integrations/n8n/health (error)"""
        with patch('backend.api.v2.integrations.check_n8n_health') as mock_check:
            mock_check.return_value = {
                'enabled': True,
                'host': 'http://localhost:5678',
                'reachable': False,
                'api_key_present': True,
                'last_check': '2024-01-01T12:00:00',
                'error_message': 'Connection failed'
            }
            
            response = client.get("/v2/integrations/n8n/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'error'
            assert 'Connection failed' in data['message']
    
    def test_get_n8n_health_warning(self, client):
        """Test: GET /v2/integrations/n8n/health (warning)"""
        with patch('backend.api.v2.integrations.check_n8n_health') as mock_check:
            mock_check.return_value = {
                'enabled': True,
                'host': 'http://localhost:5678',
                'reachable': True,
                'api_key_present': False,
                'last_check': '2024-01-01T12:00:00',
                'error_message': None
            }
            
            response = client.get("/v2/integrations/n8n/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'warning'
            assert 'no API key configured' in data['message']


class TestIntegrationsMatrix:
    """Test-Matrix für verschiedene ENV-Kombinationen"""
    
    @pytest.mark.asyncio
    async def test_env_matrix_enabled_with_key(self):
        """Test: N8N_ENABLED=true + N8N_API_KEY gesetzt"""
        with patch.dict('os.environ', {
            'N8N_ENABLED': 'true',
            'N8N_HOST': 'http://localhost:5678',
            'N8N_API_KEY': 'test-key',
            'N8N_TIMEOUT_SECONDS': '15'
        }):
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                mock_client.get.return_value.status_code = 200
                
                result = await check_n8n_health()
                
                assert result['enabled'] is True
                assert result['api_key_present'] is True
    
    @pytest.mark.asyncio
    async def test_env_matrix_enabled_without_key(self):
        """Test: N8N_ENABLED=true + N8N_API_KEY nicht gesetzt"""
        with patch.dict('os.environ', {
            'N8N_ENABLED': 'true',
            'N8N_HOST': 'http://localhost:5678',
            'N8N_API_KEY': '',  # Leer
            'N8N_TIMEOUT_SECONDS': '15'
        }):
            result = await check_n8n_health()
            
            assert result['enabled'] is True
            assert result['api_key_present'] is False
    
    @pytest.mark.asyncio
    async def test_env_matrix_disabled(self):
        """Test: N8N_ENABLED=false"""
        with patch.dict('os.environ', {
            'N8N_ENABLED': 'false',
            'N8N_HOST': 'http://localhost:5678',
            'N8N_API_KEY': 'test-key',
            'N8N_TIMEOUT_SECONDS': '15'
        }):
            result = await check_n8n_health()
            
            assert result['enabled'] is False
            assert result['reachable'] is False
            assert result['api_key_present'] is False


if __name__ == "__main__":
    # Einfacher Test-Runner für manuelle Tests
    import asyncio
    
    async def run_manual_test():
        """Manueller Test ohne Mocks (nur wenn Backend läuft)"""
        print("Running manual integrations status test...")
        
        import httpx
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/v2/integrations/n8n/status")
                print(f"Status response: {response.status_code}")
                if response.status_code == 200:
                    print(f"Data: {response.json()}")
                else:
                    print(f"Error: {response.text}")
        except Exception as e:
            print(f"Connection error: {e}")
    
    print("Integrations Status Tests")
    print("Run with pytest for full test suite:")
    print("pytest tests/test_integrations_status.py -v")
