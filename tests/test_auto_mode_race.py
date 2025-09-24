"""
Rico 4.5 - Auto-Modus Race-Logic Tests
Spezifische Tests für Race-Conditions und Task-Cleanup
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from backend.app.services.orchestrator import RicoOrchestrator


class TestAutoModeRaceLogic:
    """Tests für Auto-Modus Race-Logic"""
    
    @pytest.fixture
    def orchestrator(self):
        return RicoOrchestrator()
    
    @pytest.mark.asyncio
    async def test_race_condition_first_wins(self, orchestrator):
        """Test: Erste erfolgreiche Antwort gewinnt"""
        with patch('backend.app.services.orchestrator._call_openai') as mock_openai, \
             patch('backend.app.services.orchestrator._call_claude') as mock_claude, \
             patch('backend.app.services.orchestrator._call_perplexity') as mock_perplexity:
            
            # OpenAI antwortet schnell und erfolgreich
            mock_openai.return_value = (True, {
                "kurz_zusammenfassung": "OpenAI gewinnt",
                "team_rolle": {"openai": True, "claude": False, "perplexity": False},
                "meta": {"provider": "openai", "duration_s": 0.1}
            }, 0.1)
            
            # Claude antwortet langsam
            async def slow_claude():
                await asyncio.sleep(0.5)
                return (True, {
                    "kurz_zusammenfassung": "Claude zu langsam",
                    "team_rolle": {"openai": False, "claude": True, "perplexity": False},
                    "meta": {"provider": "claude", "duration_s": 0.5}
                }, 0.5)
            mock_claude.return_value = slow_claude()
            
            # Perplexity antwortet auch langsam
            async def slow_perplexity():
                await asyncio.sleep(0.5)
                return (True, {
                    "kurz_zusammenfassung": "Perplexity zu langsam",
                    "team_rolle": {"openai": False, "claude": False, "perplexity": True},
                    "meta": {"provider": "perplexity", "duration_s": 0.5}
                }, 0.5)
            mock_perplexity.return_value = slow_perplexity()
            
            result = await orchestrator.run_rico_loop("Test prompt", "analysis", "auto")
            
            # OpenAI sollte gewinnen
            assert result["ok"] is True
            assert result["used_provider"] == "openai"
            assert "OpenAI gewinnt" in result["result"]["kurz_zusammenfassung"]
    
    @pytest.mark.asyncio
    async def test_race_condition_second_wins(self, orchestrator):
        """Test: Zweite Antwort gewinnt wenn erste fehlschlägt"""
        with patch('backend.app.services.orchestrator._call_openai') as mock_openai, \
             patch('backend.app.services.orchestrator._call_claude') as mock_claude, \
             patch('backend.app.services.orchestrator._call_perplexity') as mock_perplexity:
            
            # OpenAI fehlschlägt
            mock_openai.return_value = (False, {"error": "auth"}, 0.1)
            
            # Claude antwortet erfolgreich
            mock_claude.return_value = (True, {
                "kurz_zusammenfassung": "Claude gewinnt",
                "team_rolle": {"openai": False, "claude": True, "perplexity": False},
                "meta": {"provider": "claude", "duration_s": 0.2}
            }, 0.2)
            
            # Perplexity antwortet langsam
            async def slow_perplexity():
                await asyncio.sleep(0.5)
                return (True, {
                    "kurz_zusammenfassung": "Perplexity zu langsam",
                    "team_rolle": {"openai": False, "claude": False, "perplexity": True},
                    "meta": {"provider": "perplexity", "duration_s": 0.5}
                }, 0.5)
            mock_perplexity.return_value = slow_perplexity()
            
            result = await orchestrator.run_rico_loop("Test prompt", "analysis", "auto")
            
            # Claude sollte gewinnen
            assert result["ok"] is True
            assert result["used_provider"] == "claude"
            assert "Claude gewinnt" in result["result"]["kurz_zusammenfassung"]
    
    @pytest.mark.asyncio
    async def test_race_condition_all_fail(self, orchestrator):
        """Test: Alle Provider fehlschlagen"""
        with patch('backend.app.services.orchestrator._call_openai') as mock_openai, \
             patch('backend.app.services.orchestrator._call_claude') as mock_claude, \
             patch('backend.app.services.orchestrator._call_perplexity') as mock_perplexity:
            
            # Alle Provider fehlschlagen
            mock_openai.return_value = (False, {"error": "auth"}, 0.1)
            mock_claude.return_value = (False, {"error": "rate_limit"}, 0.1)
            mock_perplexity.return_value = (False, {"error": "server"}, 0.1)
            
            result = await orchestrator.run_rico_loop("Test prompt", "analysis", "auto")
            
            # Alle sollten fehlschlagen
            assert result["ok"] is False
            assert "error" in result["result"]
    
    @pytest.mark.asyncio
    async def test_task_cleanup_on_success(self, orchestrator):
        """Test: Sauberes Cleanup von abgebrochenen Tasks"""
        cancelled_tasks = []
        
        with patch('backend.app.services.orchestrator._call_openai') as mock_openai, \
             patch('backend.app.services.orchestrator._call_claude') as mock_claude, \
             patch('backend.app.services.orchestrator._call_perplexity') as mock_perplexity:
            
            # OpenAI antwortet schnell
            mock_openai.return_value = (True, {
                "kurz_zusammenfassung": "OpenAI gewinnt",
                "team_rolle": {"openai": True, "claude": False, "perplexity": False},
                "meta": {"provider": "openai", "duration_s": 0.1}
            }, 0.1)
            
            # Claude und Perplexity antworten langsam
            async def slow_claude():
                await asyncio.sleep(1.0)
                return (True, {
                    "kurz_zusammenfassung": "Claude zu langsam",
                    "team_rolle": {"openai": False, "claude": True, "perplexity": False},
                    "meta": {"provider": "claude", "duration_s": 1.0}
                }, 1.0)
            mock_claude.return_value = slow_claude()
            
            async def slow_perplexity():
                await asyncio.sleep(1.0)
                return (True, {
                    "kurz_zusammenfassung": "Perplexity zu langsam",
                    "team_rolle": {"openai": False, "claude": False, "perplexity": True},
                    "meta": {"provider": "perplexity", "duration_s": 1.0}
                }, 1.0)
            mock_perplexity.return_value = slow_perplexity()
            
            # Mock asyncio.wait_for um Cancellation zu tracken
            original_wait_for = asyncio.wait_for
            
            async def mock_wait_for(coro, timeout=None):
                try:
                    return await original_wait_for(coro, timeout)
                except asyncio.CancelledError:
                    cancelled_tasks.append("task_cancelled")
                    raise
            
            with patch('asyncio.wait_for', side_effect=mock_wait_for):
                result = await orchestrator.run_rico_loop("Test prompt", "analysis", "auto")
            
            # OpenAI sollte gewinnen
            assert result["ok"] is True
            assert result["used_provider"] == "openai"
    
    @pytest.mark.asyncio
    async def test_used_provider_meta_data(self, orchestrator):
        """Test: Korrekte Meta-Daten im Ergebnis"""
        with patch('backend.app.services.orchestrator._call_openai') as mock_openai, \
             patch('backend.app.services.orchestrator._call_claude') as mock_claude, \
             patch('backend.app.services.orchestrator._call_perplexity') as mock_perplexity:
            
            # OpenAI gewinnt
            mock_openai.return_value = (True, {
                "kurz_zusammenfassung": "OpenAI Test",
                "team_rolle": {"openai": True, "claude": False, "perplexity": False},
                "meta": {"provider": "openai", "duration_s": 0.1}
            }, 0.1)
            
            # Andere Provider langsam
            mock_claude.return_value = asyncio.sleep(1.0).then(lambda: (True, {}, 1.0))
            mock_perplexity.return_value = asyncio.sleep(1.0).then(lambda: (True, {}, 1.0))
            
            result = await orchestrator.run_rico_loop("Test prompt", "analysis", "auto")
            
            # Meta-Daten prüfen
            assert result["ok"] is True
            assert result["used_provider"] == "openai"
            assert result["result"]["meta"]["provider"] == "openai"
            assert result["result"]["meta"]["used_provider"] == "openai"
            assert "duration_s" in result["result"]["meta"]
    
    @pytest.mark.asyncio
    async def test_team_rolle_correctness(self, orchestrator):
        """Test: Korrekte Team-Rolle-Zuweisung"""
        with patch('backend.app.services.orchestrator._call_openai') as mock_openai, \
             patch('backend.app.services.orchestrator._call_claude') as mock_claude, \
             patch('backend.app.services.orchestrator._call_perplexity') as mock_perplexity:
            
            # Claude gewinnt
            mock_openai.return_value = (False, {"error": "auth"}, 0.1)
            mock_claude.return_value = (True, {
                "kurz_zusammenfassung": "Claude Test",
                "team_rolle": {"openai": False, "claude": True, "perplexity": False},
                "meta": {"provider": "claude", "duration_s": 0.2}
            }, 0.2)
            mock_perplexity.return_value = (False, {"error": "server"}, 0.1)
            
            result = await orchestrator.run_rico_loop("Test prompt", "analysis", "auto")
            
            # Team-Rolle prüfen
            assert result["ok"] is True
            assert result["used_provider"] == "claude"
            assert result["result"]["team_rolle"]["claude"] is True
            assert result["result"]["team_rolle"]["openai"] is False
            assert result["result"]["team_rolle"]["perplexity"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
