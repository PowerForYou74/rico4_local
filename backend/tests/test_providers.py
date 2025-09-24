"""
Mock-basierte Provider-Tests
Alle Tests mocken HTTP-Calls, keine externen Requests
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import Response
import json

from providers.openai_client import OpenAIProvider
from providers.anthropic_client import AnthropicProvider
from providers.perplexity_client import PerplexityProvider
from providers.base import ProviderType, ProviderResponse, ProviderError


class TestOpenAIProvider:
    """Test OpenAI provider with mocked HTTP calls"""
    
    @pytest.fixture
    def provider(self):
        return OpenAIProvider("test-api-key", "gpt-3.5-turbo")
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, provider):
        """Test successful response generation"""
        mock_response_data = {
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {"total_tokens": 100},
            "model": "gpt-3.5-turbo"
        }
        
        mock_response = Response(
            status_code=200,
            content=json.dumps(mock_response_data),
            headers={"content-type": "application/json"}
        )
        
        with patch.object(provider.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            result = await provider.generate_response("Test prompt")
            
            assert result.success is True
            assert result.provider == "openai"
            assert result.model == "gpt-3.5-turbo"
            assert result.content == "Test response"
            assert result.usage == {"total_tokens": 100}
            assert result.latency_ms > 0
    
    @pytest.mark.asyncio
    async def test_generate_response_failure(self, provider):
        """Test failed response generation"""
        with patch.object(provider.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = Exception("API Error")
            
            result = await provider.generate_response("Test prompt")
            
            assert result.success is False
            assert result.provider == "openai"
            assert result.error is not None
            assert result.error.error_type == "Exception"
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, provider):
        """Test successful health check"""
        mock_response_data = {
            "data": [{"id": "gpt-3.5-turbo"}, {"id": "gpt-4"}]
        }
        
        mock_response = Response(
            status_code=200,
            content=json.dumps(mock_response_data),
            headers={"content-type": "application/json"}
        )
        
        with patch.object(provider.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            result = await provider.health_check()
            
            assert result["status"] == "healthy"
            assert result["provider"] == "openai"
            assert result["latency_ms"] > 0
            assert result["available_models"] == 2
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, provider):
        """Test failed health check"""
        with patch.object(provider.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("Connection Error")
            
            result = await provider.health_check()
            
            assert result["status"] == "unhealthy"
            assert result["provider"] == "openai"
            assert "error" in result


class TestAnthropicProvider:
    """Test Anthropic provider with mocked HTTP calls"""
    
    @pytest.fixture
    def provider(self):
        return AnthropicProvider("test-api-key", "claude-3-sonnet-20240229")
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, provider):
        """Test successful response generation"""
        mock_response_data = {
            "content": [{"text": "Test response"}],
            "usage": {"input_tokens": 50, "output_tokens": 50},
            "model": "claude-3-sonnet-20240229"
        }
        
        mock_response = Response(
            status_code=200,
            content=json.dumps(mock_response_data),
            headers={"content-type": "application/json"}
        )
        
        with patch.object(provider.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            result = await provider.generate_response("Test prompt")
            
            assert result.success is True
            assert result.provider == "anthropic"
            assert result.model == "claude-3-sonnet-20240229"
            assert result.content == "Test response"
            assert result.usage == {"input_tokens": 50, "output_tokens": 50}
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, provider):
        """Test successful health check"""
        mock_response_data = {
            "content": [{"text": "Hello"}],
            "model": "claude-3-sonnet-20240229"
        }
        
        mock_response = Response(
            status_code=200,
            content=json.dumps(mock_response_data),
            headers={"content-type": "application/json"}
        )
        
        with patch.object(provider.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            result = await provider.health_check()
            
            assert result["status"] == "healthy"
            assert result["provider"] == "anthropic"
            assert result["latency_ms"] > 0


class TestPerplexityProvider:
    """Test Perplexity provider with mocked HTTP calls"""
    
    @pytest.fixture
    def provider(self):
        return PerplexityProvider("test-api-key", "sonar")
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, provider):
        """Test successful response generation"""
        mock_response_data = {
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {"total_tokens": 100},
            "model": "sonar"
        }
        
        mock_response = Response(
            status_code=200,
            content=json.dumps(mock_response_data),
            headers={"content-type": "application/json"}
        )
        
        with patch.object(provider.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            result = await provider.generate_response("Test prompt")
            
            assert result.success is True
            assert result.provider == "perplexity"
            assert result.model == "sonar"
            assert result.content == "Test response"
    
    @pytest.mark.asyncio
    async def test_default_model_is_sonar(self, provider):
        """Test that default model is 'sonar'"""
        assert provider.model == "sonar"
        assert provider.get_default_model() == "sonar"
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, provider):
        """Test successful health check"""
        mock_response_data = {
            "choices": [{"message": {"content": "Hello"}}],
            "model": "sonar"
        }
        
        mock_response = Response(
            status_code=200,
            content=json.dumps(mock_response_data),
            headers={"content-type": "application/json"}
        )
        
        with patch.object(provider.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            result = await provider.health_check()
            
            assert result["status"] == "healthy"
            assert result["provider"] == "perplexity"
            assert result["model"] == "sonar"
            assert result["latency_ms"] > 0


class TestProviderErrorMapping:
    """Test provider error mapping"""
    
    def test_error_mapping(self):
        """Test error mapping functionality"""
        from providers.base import ProviderErrorMapper
        
        # Test OpenAI error mapping
        openai_error = Exception("Rate limit exceeded")
        mapped_error = ProviderErrorMapper.map_error("openai", openai_error)
        assert mapped_error == "unknown_error"  # Exception is not in mapping
        
        # Test error message generation
        message = ProviderErrorMapper.get_error_message("openai", openai_error)
        assert "unexpected error" in message.lower()
    
    def test_provider_types(self):
        """Test provider type enums"""
        assert ProviderType.OPENAI == "openai"
        assert ProviderType.ANTHROPIC == "anthropic"
        assert ProviderType.PERPLEXITY == "perplexity"
    
    def test_provider_response_creation(self):
        """Test provider response creation"""
        response = ProviderResponse(
            provider="test",
            model="test-model",
            content="test content",
            latency_ms=100.0
        )
        
        assert response.provider == "test"
        assert response.model == "test-model"
        assert response.content == "test content"
        assert response.latency_ms == 100.0
        assert response.success is True
        assert response.error is None


@pytest.mark.asyncio
async def test_provider_cleanup():
    """Test provider cleanup"""
    provider = OpenAIProvider("test-key")
    
    with patch.object(provider.client, 'aclose', new_callable=AsyncMock) as mock_close:
        await provider.close()
        mock_close.assert_called_once()


@pytest.mark.asyncio
async def test_provider_timeout():
    """Test provider timeout handling"""
    provider = OpenAIProvider("test-key")
    
    with patch.object(provider.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = asyncio.TimeoutError("Request timeout")
        
        result = await provider.generate_response("Test prompt")
        
        assert result.success is False
        assert result.error is not None
        assert "TimeoutError" in result.error.error_type
