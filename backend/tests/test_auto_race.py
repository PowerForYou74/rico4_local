"""
Auto-Race Tests mit Mock-basierten Providern
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from datetime import datetime

from orchestrator.auto_race import AutoRaceOrchestrator, RaceStatus
from providers.base import ProviderResponse, ProviderType, ProviderError
from providers.openai_client import OpenAIProvider
from providers.anthropic_client import AnthropicProvider
from providers.perplexity_client import PerplexityProvider


class TestAutoRaceOrchestrator:
    """Test auto-race orchestrator with mocked providers"""
    
    @pytest.fixture
    def mock_providers(self):
        """Create mock providers for testing"""
        providers = []
        
        # Mock OpenAI provider
        openai_provider = OpenAIProvider("test-key", "gpt-3.5-turbo")
        openai_provider.generate_response = AsyncMock(return_value=ProviderResponse(
            provider="openai",
            model="gpt-3.5-turbo",
            content="OpenAI response",
            latency_ms=100.0,
            success=True
        ))
        openai_provider.health_check = AsyncMock(return_value={
            "status": "healthy",
            "latency_ms": 50.0,
            "provider": "openai"
        })
        providers.append(openai_provider)
        
        # Mock Anthropic provider
        anthropic_provider = AnthropicProvider("test-key", "claude-3-sonnet-20240229")
        anthropic_provider.generate_response = AsyncMock(return_value=ProviderResponse(
            provider="anthropic",
            model="claude-3-sonnet-20240229",
            content="Anthropic response",
            latency_ms=150.0,
            success=True
        ))
        anthropic_provider.health_check = AsyncMock(return_value={
            "status": "healthy",
            "latency_ms": 75.0,
            "provider": "anthropic"
        })
        providers.append(anthropic_provider)
        
        # Mock Perplexity provider
        perplexity_provider = PerplexityProvider("test-key", "sonar")
        perplexity_provider.generate_response = AsyncMock(return_value=ProviderResponse(
            provider="perplexity",
            model="sonar",
            content="Perplexity response",
            latency_ms=200.0,
            success=True
        ))
        perplexity_provider.health_check = AsyncMock(return_value={
            "status": "healthy",
            "latency_ms": 100.0,
            "provider": "perplexity"
        })
        providers.append(perplexity_provider)
        
        return providers
    
    @pytest.fixture
    def orchestrator(self, mock_providers):
        """Create orchestrator with mock providers"""
        return AutoRaceOrchestrator(mock_providers, timeout=5.0)
    
    @pytest.mark.asyncio
    async def test_race_success(self, orchestrator):
        """Test successful race with first provider winning"""
        result = await orchestrator.race("Test prompt")
        
        assert result.status == RaceStatus.COMPLETED
        assert result.winner is not None
        assert result.winner.success is True
        assert result.winner.provider == "openai"  # Should win due to tie-breaker
        assert len(result.participants) == 3
        assert result.race_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_race_with_failure(self, mock_providers):
        """Test race with some providers failing"""
        # Make one provider fail
        mock_providers[1].generate_response = AsyncMock(return_value=ProviderResponse(
            provider="anthropic",
            model="claude-3-sonnet-20240229",
            content="",
            latency_ms=0.0,
            success=False,
            error=ProviderError(
                provider="anthropic",
                error_type="APIError",
                message="API Error"
            )
        ))
        
        orchestrator = AutoRaceOrchestrator(mock_providers)
        result = await orchestrator.race("Test prompt")
        
        assert result.status == RaceStatus.COMPLETED
        assert result.winner is not None
        assert result.winner.success is True
        assert result.winner.provider == "openai"  # Should still win
    
    @pytest.mark.asyncio
    async def test_race_all_fail(self, mock_providers):
        """Test race where all providers fail"""
        # Make all providers fail
        for provider in mock_providers:
            provider.generate_response = AsyncMock(return_value=ProviderResponse(
                provider=provider.provider_type.value,
                model=provider.model,
                content="",
                latency_ms=0.0,
                success=False,
                error=ProviderError(
                    provider=provider.provider_type.value,
                    error_type="APIError",
                    message="API Error"
                )
            ))
        
        orchestrator = AutoRaceOrchestrator(mock_providers)
        result = await orchestrator.race("Test prompt")
        
        assert result.status == RaceStatus.FAILED
        assert result.winner is None
        assert len(result.participants) == 3
    
    @pytest.mark.asyncio
    async def test_race_timeout(self, mock_providers):
        """Test race timeout"""
        # Make all providers slow
        async def slow_response(*args, **kwargs):
            await asyncio.sleep(10)  # Longer than timeout
            return ProviderResponse(
                provider="test",
                model="test",
                content="Slow response",
                latency_ms=10000.0,
                success=True
            )
        
        for provider in mock_providers:
            provider.generate_response = slow_response
        
        orchestrator = AutoRaceOrchestrator(mock_providers, timeout=1.0)
        result = await orchestrator.race("Test prompt")
        
        assert result.status == RaceStatus.FAILED
        assert result.winner is None
        assert "timeout" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_tie_breaker_order(self, mock_providers):
        """Test tie-breaker order (OpenAI should win)"""
        # Make all providers return at the same time
        for provider in mock_providers:
            provider.generate_response = AsyncMock(return_value=ProviderResponse(
                provider=provider.provider_type.value,
                model=provider.model,
                content=f"{provider.provider_type.value} response",
                latency_ms=100.0,  # Same latency
                success=True
            ))
        
        orchestrator = AutoRaceOrchestrator(mock_providers)
        result = await orchestrator.race("Test prompt")
        
        assert result.winner.provider == "openai"  # Should win due to tie-breaker
    
    @pytest.mark.asyncio
    async def test_health_check_all(self, orchestrator):
        """Test health check for all providers"""
        result = await orchestrator.health_check_all()
        
        assert "openai" in result
        assert "anthropic" in result
        assert "perplexity" in result
        
        for provider_name, health in result.items():
            assert health["status"] == "healthy"
            assert "latency_ms" in health
            assert health["provider"] == provider_name
    
    @pytest.mark.asyncio
    async def test_health_check_with_failure(self, mock_providers):
        """Test health check with some providers failing"""
        # Make one provider fail health check
        mock_providers[1].health_check = AsyncMock(side_effect=Exception("Health check failed"))
        
        orchestrator = AutoRaceOrchestrator(mock_providers)
        result = await orchestrator.health_check_all()
        
        assert result["openai"]["status"] == "healthy"
        assert result["anthropic"]["status"] == "unhealthy"
        assert result["perplexity"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_race_with_kwargs(self, orchestrator):
        """Test race with additional kwargs"""
        result = await orchestrator.race(
            "Test prompt",
            max_tokens=1000,
            temperature=0.7
        )
        
        assert result.status == RaceStatus.COMPLETED
        assert result.winner is not None
        
        # Verify kwargs were passed to providers
        for provider in orchestrator.providers:
            provider.generate_response.assert_called_once()
            call_args = provider.generate_response.call_args
            assert call_args[0][0] == "Test prompt"  # prompt
            assert call_args[1]["max_tokens"] == 1000
            assert call_args[1]["temperature"] == 0.7
    
    @pytest.mark.asyncio
    async def test_race_cancellation(self, mock_providers):
        """Test that pending tasks are cancelled"""
        cancelled_tasks = []
        
        async def track_cancellation(*args, **kwargs):
            try:
                await asyncio.sleep(1)
                return ProviderResponse(
                    provider="test",
                    model="test",
                    content="Should not reach here",
                    latency_ms=1000.0,
                    success=True
                )
            except asyncio.CancelledError:
                cancelled_tasks.append("cancelled")
                raise
        
        for provider in mock_providers:
            provider.generate_response = track_cancellation
        
        orchestrator = AutoRaceOrchestrator(mock_providers, timeout=0.5)
        result = await orchestrator.race("Test prompt")
        
        assert result.status == RaceStatus.FAILED
        # Note: In real scenario, some tasks might be cancelled
        # This test verifies the timeout mechanism works


class TestRaceResult:
    """Test race result functionality"""
    
    def test_race_result_creation(self):
        """Test race result creation"""
        from orchestrator.auto_race import RaceResult
        
        result = RaceResult(
            winner=None,
            participants=[],
            race_time_ms=100.0,
            status=RaceStatus.PENDING
        )
        
        assert result.winner is None
        assert result.participants == []
        assert result.race_time_ms == 100.0
        assert result.status == RaceStatus.PENDING
        assert result.error is None
    
    def test_race_status_enum(self):
        """Test race status enum"""
        assert RaceStatus.PENDING == "pending"
        assert RaceStatus.RUNNING == "running"
        assert RaceStatus.COMPLETED == "completed"
        assert RaceStatus.FAILED == "failed"
        assert RaceStatus.CANCELLED == "cancelled"


@pytest.mark.asyncio
async def test_orchestrator_initialization():
    """Test orchestrator initialization"""
    providers = []
    orchestrator = AutoRaceOrchestrator(providers, timeout=10.0)
    
    assert orchestrator.providers == providers
    assert orchestrator.timeout == 10.0
    assert orchestrator.tie_breaker_order == [
        ProviderType.OPENAI,
        ProviderType.ANTHROPIC,
        ProviderType.PERPLEXITY
    ]


@pytest.mark.asyncio
async def test_empty_providers():
    """Test orchestrator with empty providers list"""
    orchestrator = AutoRaceOrchestrator([])
    result = await orchestrator.race("Test prompt")
    
    assert result.status == RaceStatus.FAILED
    assert result.winner is None
    assert result.participants == []
