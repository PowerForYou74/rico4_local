"""
Auto-Race Logic with async asyncio.wait(FIRST_COMPLETED) and deterministic tie-breaker
"""
import asyncio
import time
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from ..providers.base import BaseProvider, ProviderResponse, ProviderType, ProviderError


class RaceStatus(str, Enum):
    """Auto-race status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class RaceResult:
    """Result of an auto-race"""
    winner: Optional[ProviderResponse] = None
    participants: List[ProviderResponse] = []
    race_time_ms: float = 0.0
    status: RaceStatus = RaceStatus.PENDING
    error: Optional[str] = None


class AutoRaceOrchestrator:
    """Orchestrates auto-race between multiple providers"""
    
    def __init__(self, providers: List[BaseProvider], timeout: float = 30.0):
        self.providers = providers
        self.timeout = timeout
        self.tie_breaker_order = [
            ProviderType.OPENAI,
            ProviderType.ANTHROPIC, 
            ProviderType.PERPLEXITY
        ]
    
    async def race(
        self, 
        prompt: str, 
        **kwargs
    ) -> RaceResult:
        """Run auto-race between providers"""
        start_time = time.time()
        
        # Create tasks for all providers
        tasks = []
        for provider in self.providers:
            task = asyncio.create_task(
                self._run_provider(provider, prompt, **kwargs)
            )
            tasks.append(task)
        
        try:
            # Wait for first completion
            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED,
                timeout=self.timeout
            )
            
            # Cancel remaining tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Collect results
            results = []
            for task in done:
                try:
                    result = await task
                    results.append(result)
                except Exception as e:
                    # Create error response for failed task
                    error_response = ProviderResponse(
                        content="",
                        provider="unknown",
                        provider_model="unknown",
                        duration_s=0.0,
                        latency_ms=0.0,
                        success=False,
                        error=ProviderError(
                            provider="unknown",
                            error_type=type(e).__name__,
                            message=str(e)
                        )
                    )
                    results.append(error_response)
            
            # Determine winner using tie-breaker
            winner = self._determine_winner(results)
            
            race_time_ms = (time.time() - start_time) * 1000
            
            return RaceResult(
                winner=winner,
                participants=results,
                race_time_ms=race_time_ms,
                status=RaceStatus.COMPLETED if winner and winner.success else RaceStatus.FAILED
            )
            
        except asyncio.TimeoutError:
            # Cancel all tasks
            for task in tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            race_time_ms = (time.time() - start_time) * 1000
            
            return RaceResult(
                race_time_ms=race_time_ms,
                status=RaceStatus.FAILED,
                error="Race timeout exceeded"
            )
    
    async def _run_provider(
        self, 
        provider: BaseProvider, 
        prompt: str, 
        **kwargs
    ) -> ProviderResponse:
        """Run a single provider"""
        try:
            return await provider.generate_response(prompt, **kwargs)
        except Exception as e:
            return provider.create_error_response(e)
    
    def _determine_winner(self, results: List[ProviderResponse]) -> Optional[ProviderResponse]:
        """Determine winner using deterministic tie-breaker"""
        if not results:
            return None
        
        # Filter successful results
        successful_results = [r for r in results if r.success]
        if not successful_results:
            return None
        
        # If only one successful result, return it
        if len(successful_results) == 1:
            return successful_results[0]
        
        # Apply tie-breaker based on provider type order
        for provider_type in self.tie_breaker_order:
            for result in successful_results:
                if result.provider == provider_type.value:
                    return result
        
        # Fallback to first successful result
        return successful_results[0]
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Check health of all providers"""
        health_tasks = []
        for provider in self.providers:
            task = asyncio.create_task(provider.health_check())
            health_tasks.append(task)
        
        health_results = await asyncio.gather(*health_tasks, return_exceptions=True)
        
        results = {}
        for i, (provider, health_result) in enumerate(zip(self.providers, health_results)):
            if isinstance(health_result, Exception):
                results[provider.provider_type.value] = {
                    "status": "unhealthy",
                    "error": str(health_result)
                }
            else:
                results[provider.provider_type.value] = health_result
        
        return results
