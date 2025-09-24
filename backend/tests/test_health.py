"""
Health-Check Tests
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import json

from main import app
from config.settings import settings


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_quick_health(self, client):
        """Test quick health check"""
        response = client.get("/health/quick")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "env_source" in data
        assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_health_check_no_providers(self, client):
        """Test health check with no providers configured"""
        with patch.object(settings, 'openai_api_key', None), \
             patch.object(settings, 'anthropic_api_key', None), \
             patch.object(settings, 'perplexity_api_key', None):
            
            response = client.get("/health/")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "no_providers"
            assert data["model"] == "none"
            assert data["env_source"] == settings.env_source
            assert data["providers"] == []
    
    @pytest.mark.asyncio
    async def test_health_check_with_providers(self, client):
        """Test health check with providers configured"""
        with patch.object(settings, 'openai_api_key', 'test-key'), \
             patch.object(settings, 'anthropic_api_key', 'test-key'), \
             patch.object(settings, 'perplexity_api_key', 'test-key'):
            
            # Mock provider health checks
            with patch('api.health.OpenAIProvider') as mock_openai, \
                 patch('api.health.AnthropicProvider') as mock_anthropic, \
                 patch('api.health.PerplexityProvider') as mock_perplexity:
                
                # Setup mock instances
                mock_openai_instance = AsyncMock()
                mock_openai_instance.health_check.return_value = {
                    "status": "healthy",
                    "latency_ms": 50.0,
                    "provider": "openai"
                }
                mock_openai_instance.model = "gpt-3.5-turbo"
                mock_openai_instance.close = AsyncMock()
                mock_openai.return_value = mock_openai_instance
                
                mock_anthropic_instance = AsyncMock()
                mock_anthropic_instance.health_check.return_value = {
                    "status": "healthy",
                    "latency_ms": 75.0,
                    "provider": "anthropic"
                }
                mock_anthropic_instance.model = "claude-3-sonnet-20240229"
                mock_anthropic_instance.close = AsyncMock()
                mock_anthropic.return_value = mock_anthropic_instance
                
                mock_perplexity_instance = AsyncMock()
                mock_perplexity_instance.health_check.return_value = {
                    "status": "healthy",
                    "latency_ms": 100.0,
                    "provider": "perplexity"
                }
                mock_perplexity_instance.model = "sonar"
                mock_perplexity_instance.close = AsyncMock()
                mock_perplexity.return_value = mock_perplexity_instance
                
                response = client.get("/health/")
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "healthy"
                assert data["model"] == "gpt-3.5-turbo"  # First healthy provider
                assert len(data["providers"]) == 3
                
                # Check provider details
                providers = {p["provider"]: p for p in data["providers"]}
                assert "openai" in providers
                assert "anthropic" in providers
                assert "perplexity" in providers
                
                for provider_data in data["providers"]:
                    assert provider_data["status"] == "healthy"
                    assert provider_data["latency_ms"] > 0
    
    @pytest.mark.asyncio
    async def test_health_check_provider_failure(self, client):
        """Test health check with provider failures"""
        with patch.object(settings, 'openai_api_key', 'test-key'), \
             patch.object(settings, 'anthropic_api_key', 'test-key'):
            
            with patch('api.health.OpenAIProvider') as mock_openai, \
                 patch('api.health.AnthropicProvider') as mock_anthropic:
                
                # Setup mock instances with failures
                mock_openai_instance = AsyncMock()
                mock_openai_instance.health_check.side_effect = Exception("API Error")
                mock_openai_instance.model = "gpt-3.5-turbo"
                mock_openai_instance.close = AsyncMock()
                mock_openai.return_value = mock_openai_instance
                
                mock_anthropic_instance = AsyncMock()
                mock_anthropic_instance.health_check.return_value = {
                    "status": "healthy",
                    "latency_ms": 75.0,
                    "provider": "anthropic"
                }
                mock_anthropic_instance.model = "claude-3-sonnet-20240229"
                mock_anthropic_instance.close = AsyncMock()
                mock_anthropic.return_value = mock_anthropic_instance
                
                response = client.get("/health/")
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "healthy"  # At least one provider is healthy
                assert data["model"] == "claude-3-sonnet-20240229"
                
                # Check that failed provider is marked as unhealthy
                providers = {p["provider"]: p for p in data["providers"]}
                assert providers["openai"]["status"] == "unhealthy"
                assert providers["anthropic"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_providers_health_endpoint(self, client):
        """Test providers health endpoint"""
        with patch.object(settings, 'openai_api_key', 'test-key'):
            
            with patch('api.health.OpenAIProvider') as mock_openai:
                mock_openai_instance = AsyncMock()
                mock_openai_instance.health_check.return_value = {
                    "status": "healthy",
                    "latency_ms": 50.0,
                    "provider": "openai"
                }
                mock_openai_instance.close = AsyncMock()
                mock_openai.return_value = mock_openai_instance
                
                response = client.get("/health/providers")
                
                assert response.status_code == 200
                data = response.json()
                assert "openai" in data
                assert data["openai"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_providers_health_no_providers(self, client):
        """Test providers health with no providers configured"""
        with patch.object(settings, 'openai_api_key', None), \
             patch.object(settings, 'anthropic_api_key', None), \
             patch.object(settings, 'perplexity_api_key', None):
            
            response = client.get("/health/providers")
            
            assert response.status_code == 200
            data = response.json()
            assert "error" in data
            assert "No providers configured" in data["error"]


class TestHealthModels:
    """Test health check data models"""
    
    def test_health_status_model(self):
        """Test health status model"""
        from api.health import HealthStatus
        
        status = HealthStatus(
            provider="test",
            model="test-model",
            status="healthy",
            latency_ms=100.0
        )
        
        assert status.provider == "test"
        assert status.model == "test-model"
        assert status.status == "healthy"
        assert status.latency_ms == 100.0
        assert status.error is None
    
    def test_system_health_model(self):
        """Test system health model"""
        from api.health import SystemHealth, HealthStatus
        
        provider_status = HealthStatus(
            provider="test",
            model="test-model",
            status="healthy",
            latency_ms=100.0
        )
        
        system_health = SystemHealth(
            status="healthy",
            latency_ms=150.0,
            model="test-model",
            env_source="test",
            providers=[provider_status]
        )
        
        assert system_health.status == "healthy"
        assert system_health.latency_ms == 150.0
        assert system_health.model == "test-model"
        assert system_health.env_source == "test"
        assert len(system_health.providers) == 1
        assert system_health.providers[0].provider == "test"


@pytest.mark.asyncio
async def test_health_check_integration():
    """Test health check integration"""
    from api.health import health_check
    
    with patch.object(settings, 'openai_api_key', None), \
         patch.object(settings, 'anthropic_api_key', None), \
         patch.object(settings, 'perplexity_api_key', None):
        
        result = await health_check()
        
        assert result.status == "no_providers"
        assert result.model == "none"
        assert result.env_source == settings.env_source
        assert result.providers == []


def test_health_check_response_format():
    """Test health check response format"""
    from api.health import SystemHealth, HealthStatus
    
    # Create sample response
    provider_status = HealthStatus(
        provider="openai",
        model="gpt-3.5-turbo",
        status="healthy",
        latency_ms=50.0
    )
    
    system_health = SystemHealth(
        status="healthy",
        latency_ms=100.0,
        model="gpt-3.5-turbo",
        env_source="local",
        providers=[provider_status]
    )
    
    # Convert to dict
    data = system_health.dict()
    
    assert "status" in data
    assert "latency_ms" in data
    assert "model" in data
    assert "env_source" in data
    assert "providers" in data
    assert "timestamp" in data
    
    assert data["status"] == "healthy"
    assert data["latency_ms"] == 100.0
    assert data["model"] == "gpt-3.5-turbo"
    assert data["env_source"] == "local"
    assert len(data["providers"]) == 1
    assert data["providers"][0]["provider"] == "openai"
