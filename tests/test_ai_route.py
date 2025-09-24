"""
Tests für AI-Routing und Multi-Provider Integration
Mock-basierte Tests für /v2/ai/ask Endpoint
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import sys

# Add project root to path
sys.path.append('.')

from backend.api.v2.ai import router, determine_provider, get_available_providers
from backend.main import app


class TestAIRouting:
    """Test-Klasse für AI-Routing-Logik"""
    
    @pytest.fixture
    def mock_providers(self):
        """Mock-Provider für Tests"""
        providers = []
        
        # Mock OpenAI Provider
        openai_mock = MagicMock()
        openai_mock.provider_type.value = "openai"
        providers.append(openai_mock)
        
        # Mock Anthropic Provider
        anthropic_mock = MagicMock()
        anthropic_mock.provider_type.value = "anthropic"
        providers.append(anthropic_mock)
        
        # Mock Perplexity Provider
        perplexity_mock = MagicMock()
        perplexity_mock.provider_type.value = "perplexity"
        providers.append(perplexity_mock)
        
        return providers
    
    def test_routing_research_task(self, mock_providers):
        """Test: research task → Perplexity"""
        from pydantic import BaseModel
        
        class MockRequest(BaseModel):
            task: str = "research"
            prompt: str = "Test prompt"
            preferred: str = "auto"
            online: bool = False
        
        request = MockRequest()
        
        provider, reason = determine_provider(request, mock_providers)
        
        assert provider.provider_type.value == "perplexity"
        assert reason == "research_online_mode"
    
    def test_routing_online_mode(self, mock_providers):
        """Test: online=true → Perplexity"""
        from pydantic import BaseModel
        
        class MockRequest(BaseModel):
            task: str = "analysis"
            prompt: str = "Test prompt"
            preferred: str = "auto"
            online: bool = True
        
        request = MockRequest()
        
        provider, reason = determine_provider(request, mock_providers)
        
        assert provider.provider_type.value == "perplexity"
        assert reason == "research_online_mode"
    
    def test_routing_write_task(self, mock_providers):
        """Test: write task → Anthropic"""
        from pydantic import BaseModel
        
        class MockRequest(BaseModel):
            task: str = "write"
            prompt: str = "Test prompt"
            preferred: str = "auto"
            online: bool = False
        
        request = MockRequest()
        
        provider, reason = determine_provider(request, mock_providers)
        
        assert provider.provider_type.value == "anthropic"
        assert reason == "write_review_task"
    
    def test_routing_review_task(self, mock_providers):
        """Test: review task → Anthropic"""
        from pydantic import BaseModel
        
        class MockRequest(BaseModel):
            task: str = "review"
            prompt: str = "Test prompt"
            preferred: str = "auto"
            online: bool = False
        
        request = MockRequest()
        
        provider, reason = determine_provider(request, mock_providers)
        
        assert provider.provider_type.value == "anthropic"
        assert reason == "write_review_task"
    
    def test_routing_analysis_task(self, mock_providers):
        """Test: analysis task → OpenAI"""
        from pydantic import BaseModel
        
        class MockRequest(BaseModel):
            task: str = "analysis"
            prompt: str = "Test prompt"
            preferred: str = "auto"
            online: bool = False
        
        request = MockRequest()
        
        provider, reason = determine_provider(request, mock_providers)
        
        assert provider.provider_type.value == "openai"
        assert reason == "analysis_default"
    
    def test_routing_forced_provider(self, mock_providers):
        """Test: preferred=anthropic → erzwungener Provider"""
        from pydantic import BaseModel
        
        class MockRequest(BaseModel):
            task: str = "analysis"
            prompt: str = "Test prompt"
            preferred: str = "anthropic"
            online: bool = False
        
        request = MockRequest()
        
        provider, reason = determine_provider(request, mock_providers)
        
        assert provider.provider_type.value == "anthropic"
        assert reason == "forced_anthropic"
    
    def test_routing_auto_race_fallback(self):
        """Test: Auto-race Fallback wenn keine spezifischen Provider verfügbar"""
        from pydantic import BaseModel
        
        class MockRequest(BaseModel):
            task: str = "unknown_task"
            prompt: str = "Test prompt"
            preferred: str = "auto"
            online: bool = False
        
        request = MockRequest()
        
        # Nur Anthropic verfügbar
        providers = [MagicMock()]
        providers[0].provider_type.value = "anthropic"
        
        provider, reason = determine_provider(request, providers)
        
        assert provider.provider_type.value == "anthropic"
        assert reason == "first_available"


class TestAIEndpoint:
    """Test-Klasse für /v2/ai/ask Endpoint"""
    
    @pytest.fixture
    def client(self):
        """FastAPI Test Client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_environment(self):
        """Mock-Environment für Tests"""
        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'test-openai-key',
            'ANTHROPIC_API_KEY': 'test-anthropic-key',
            'PERPLEXITY_API_KEY': 'test-perplexity-key'
        }):
            yield
    
    def test_ask_ai_research_task(self, client, mock_environment):
        """Test: POST /v2/ai/ask mit research task"""
        with patch('backend.api.v2.ai.get_available_providers') as mock_get_providers:
            # Mock providers
            mock_providers = []
            
            perplexity_mock = AsyncMock()
            perplexity_mock.provider_type.value = "perplexity"
            perplexity_mock.generate_response.return_value = MagicMock(
                content="Research result",
                provider="perplexity",
                provider_model="sonar",
                tokens_in=10,
                tokens_out=50,
                duration_s=1.5,
                finish_reason="stop",
                success=True
            )
            mock_providers.append(perplexity_mock)
            
            mock_get_providers.return_value = mock_providers
            
            response = client.post("/v2/ai/ask", json={
                "task": "research",
                "prompt": "Top 3 D2C Cashflow Ideen",
                "preferred": "auto",
                "online": False
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["provider"] == "perplexity"
            assert data["task"] == "research"
            assert data["content"] == "Research result"
            assert data["routing_reason"] == "research_online_mode"
    
    def test_ask_ai_write_task(self, client, mock_environment):
        """Test: POST /v2/ai/ask mit write task"""
        with patch('backend.api.v2.ai.get_available_providers') as mock_get_providers:
            # Mock providers
            mock_providers = []
            
            anthropic_mock = AsyncMock()
            anthropic_mock.provider_type.value = "anthropic"
            anthropic_mock.generate_response.return_value = MagicMock(
                content="Creative writing result",
                provider="anthropic",
                provider_model="claude-3-7-sonnet-20250219",
                tokens_in=20,
                tokens_out=100,
                duration_s=2.0,
                finish_reason="stop",
                success=True
            )
            mock_providers.append(anthropic_mock)
            
            mock_get_providers.return_value = mock_providers
            
            response = client.post("/v2/ai/ask", json={
                "task": "write",
                "prompt": "Schreibe eine strukturierte Executive Summary",
                "preferred": "auto",
                "online": False
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["provider"] == "anthropic"
            assert data["task"] == "write"
            assert data["content"] == "Creative writing result"
            assert data["routing_reason"] == "write_review_task"
    
    def test_ask_ai_analysis_task(self, client, mock_environment):
        """Test: POST /v2/ai/ask mit analysis task"""
        with patch('backend.api.v2.ai.get_available_providers') as mock_get_providers:
            # Mock providers
            mock_providers = []
            
            openai_mock = AsyncMock()
            openai_mock.provider_type.value = "openai"
            openai_mock.generate_response.return_value = MagicMock(
                content="Analysis result",
                provider="openai",
                provider_model="gpt-4o",
                tokens_in=15,
                tokens_out=75,
                duration_s=1.2,
                finish_reason="stop",
                success=True
            )
            mock_providers.append(openai_mock)
            
            mock_get_providers.return_value = mock_providers
            
            response = client.post("/v2/ai/ask", json={
                "task": "analysis",
                "prompt": "Analysiere die Marktdaten",
                "preferred": "auto",
                "online": False
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["provider"] == "openai"
            assert data["task"] == "analysis"
            assert data["content"] == "Analysis result"
            assert data["routing_reason"] == "analysis_default"
    
    def test_ask_ai_forced_provider(self, client, mock_environment):
        """Test: POST /v2/ai/ask mit erzwungenem Provider"""
        with patch('backend.api.v2.ai.get_available_providers') as mock_get_providers:
            # Mock providers
            mock_providers = []
            
            openai_mock = AsyncMock()
            openai_mock.provider_type.value = "openai"
            openai_mock.generate_response.return_value = MagicMock(
                content="Forced provider result",
                provider="openai",
                provider_model="gpt-4o",
                tokens_in=10,
                tokens_out=40,
                duration_s=0.8,
                finish_reason="stop",
                success=True
            )
            mock_providers.append(openai_mock)
            
            mock_get_providers.return_value = mock_providers
            
            response = client.post("/v2/ai/ask", json={
                "task": "research",
                "prompt": "Test prompt",
                "preferred": "openai",
                "online": False
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["provider"] == "openai"
            assert data["routing_reason"] == "forced_openai"
    
    def test_ask_ai_auto_race_fallback(self, client, mock_environment):
        """Test: POST /v2/ai/ask mit Auto-Race Fallback"""
        with patch('backend.api.v2.ai.get_available_providers') as mock_get_providers, \
             patch('backend.api.v2.ai.AutoRaceOrchestrator') as mock_orchestrator:
            
            # Mock providers für Auto-Race
            mock_providers = []
            
            openai_mock = AsyncMock()
            openai_mock.provider_type.value = "openai"
            mock_providers.append(openai_mock)
            
            anthropic_mock = AsyncMock()
            anthropic_mock.provider_type.value = "anthropic"
            mock_providers.append(anthropic_mock)
            
            mock_get_providers.return_value = mock_providers
            
            # Mock Auto-Race Result
            mock_race_result = MagicMock()
            mock_race_result.winner = MagicMock(
                content="Auto-race result",
                provider="openai",
                provider_model="gpt-4o",
                tokens_in=12,
                tokens_out=60,
                duration_s=1.1,
                finish_reason="stop",
                success=True
            )
            mock_race_result.status = "completed"
            
            mock_orchestrator.return_value.race.return_value = mock_race_result
            
            response = client.post("/v2/ai/ask", json={
                "task": "unknown_task",
                "prompt": "Test prompt",
                "preferred": "auto",
                "online": False
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["provider"] == "openai"
            assert data["content"] == "Auto-race result"
            assert "auto_race_fallback" in data["routing_reason"]
    
    def test_ask_ai_no_providers(self, client):
        """Test: POST /v2/ai/ask ohne verfügbare Provider"""
        with patch.dict('os.environ', {}):  # Keine API Keys
            response = client.post("/v2/ai/ask", json={
                "task": "analysis",
                "prompt": "Test prompt",
                "preferred": "auto",
                "online": False
            })
            
            assert response.status_code == 503
            assert "No AI providers configured" in response.json()["detail"]
    
    def test_ask_ai_provider_failure(self, client, mock_environment):
        """Test: POST /v2/ai/ask mit Provider-Fehler"""
        with patch('backend.api.v2.ai.get_available_providers') as mock_get_providers:
            # Mock provider mit Fehler
            mock_providers = []
            
            openai_mock = AsyncMock()
            openai_mock.provider_type.value = "openai"
            openai_mock.generate_response.return_value = MagicMock(
                success=False,
                error=MagicMock(message="API Error")
            )
            mock_providers.append(openai_mock)
            
            mock_get_providers.return_value = mock_providers
            
            response = client.post("/v2/ai/ask", json={
                "task": "analysis",
                "prompt": "Test prompt",
                "preferred": "openai",
                "online": False
            })
            
            assert response.status_code == 500
            assert "failed" in response.json()["detail"]


class TestAIHealth:
    """Test-Klasse für AI Health Endpoints"""
    
    @pytest.fixture
    def client(self):
        """FastAPI Test Client"""
        return TestClient(app)
    
    def test_get_ai_health(self, client):
        """Test: GET /v2/ai/health"""
        with patch('backend.api.v2.ai.get_available_providers') as mock_get_providers:
            # Mock providers
            mock_providers = []
            
            openai_mock = AsyncMock()
            openai_mock.health_check.return_value = {
                "status": "healthy",
                "latency_ms": 150.0,
                "provider": "openai",
                "model": "gpt-4o"
            }
            mock_providers.append(openai_mock)
            
            mock_get_providers.return_value = mock_providers
            
            response = client.get("/v2/ai/health")
            
            assert response.status_code == 200
            data = response.json()
            assert "providers" in data
            assert "routing_rules" in data
            assert "auto_race_enabled" in data
            assert data["auto_race_enabled"] is False  # Nur ein Provider
    
    def test_get_routing_rules(self, client):
        """Test: GET /v2/ai/routing-rules"""
        response = client.get("/v2/ai/routing-rules")
        
        assert response.status_code == 200
        data = response.json()
        assert "routing_logic" in data
        assert "provider_models" in data
        assert "response_schema" in data


if __name__ == "__main__":
    # Einfacher Test-Runner für manuelle Tests
    print("AI Routing Tests")
    print("Run with pytest for full test suite:")
    print("pytest tests/test_ai_route.py -v")
