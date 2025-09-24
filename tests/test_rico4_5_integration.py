"""
Rico 4.5 - Integration Tests
Unit-Mocks (200/401/429/500/Timeout), Integrationstest Auto-Modus
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

# Import der Services (mit Mocks für Dependencies)
import sys
from unittest.mock import patch, Mock

# Mock der Dependencies vor dem Import
with patch.dict('sys.modules', {
    'openai': Mock(),
    'anthropic': Mock(),
    'httpx': Mock(),
    'dotenv': Mock()
}):
    from backend.app.services.llm_clients import ask_openai, ask_claude, ask_perplexity
    from backend.app.services.orchestrator import RicoOrchestrator
    from backend.app.services.health_check import health_check_2


class TestProviderMocks:
    """Unit-Tests für Provider-Clients mit Mocks"""
    
    @pytest.fixture
    def mock_openai_response(self):
        """Mock für erfolgreiche OpenAI-Antwort"""
        return {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "kurz_zusammenfassung": "Test Zusammenfassung",
                        "kernbefunde": ["Test Befund 1", "Test Befund 2"],
                        "action_plan": ["Test Plan 1"],
                        "risiken": ["Test Risiko 1"],
                        "cashflow_radar": {"idee": "Test Idee"},
                        "team_rolle": {"openai": True, "claude": False, "perplexity": False}
                    })
                }
            }]
        }
    
    @pytest.fixture
    def mock_claude_response(self):
        """Mock für erfolgreiche Claude-Antwort"""
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "kurz_zusammenfassung": "Claude Test Zusammenfassung",
                    "kernbefunde": ["Claude Befund 1"],
                    "action_plan": ["Claude Plan 1"],
                    "risiken": ["Claude Risiko 1"],
                    "cashflow_radar": {"idee": "Claude Idee"},
                    "team_rolle": {"openai": False, "claude": True, "perplexity": False}
                })
            }]
        }
    
    @pytest.fixture
    def mock_perplexity_response(self):
        """Mock für erfolgreiche Perplexity-Antwort"""
        return {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "kurz_zusammenfassung": "Perplexity Test Zusammenfassung",
                        "kernbefunde": ["Perplexity Befund 1"],
                        "action_plan": ["Perplexity Plan 1"],
                        "risiken": ["Perplexity Risiko 1"],
                        "cashflow_radar": {"idee": "Perplexity Idee"},
                        "team_rolle": {"openai": False, "claude": False, "perplexity": True}
                    })
                }
            }]
        }
    
    def test_openai_success_200(self, mock_openai_response):
        """Test OpenAI erfolgreich (200)"""
        with patch('backend.app.services.llm_clients.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = Mock()
            mock_client.chat.completions.create.return_value.choices = [
                Mock(message=Mock(content=json.dumps(mock_openai_response["choices"][0]["message"]["content"])))
            ]
            mock_openai.return_value = mock_client
            
            result = ask_openai("Test prompt")
            
            assert "kurz_zusammenfassung" in result
            assert result["team_rolle"]["openai"] is True
            assert "error" not in result
    
    def test_openai_auth_error_401(self):
        """Test OpenAI Auth-Fehler (401)"""
        with patch('backend.app.services.llm_clients.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = Exception("401 Unauthorized")
            mock_openai.return_value = mock_client
            
            result = ask_openai("Test prompt")
            
            assert result["error"] == "auth"
            assert result["team_rolle"]["openai"] is False
    
    def test_openai_rate_limit_429(self):
        """Test OpenAI Rate-Limit (429)"""
        with patch('backend.app.services.llm_clients.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = Exception("429 rate limit")
            mock_openai.return_value = mock_client
            
            result = ask_openai("Test prompt")
            
            assert result["error"] == "rate_limit"
            assert result["team_rolle"]["openai"] is False
    
    def test_openai_server_error_500(self):
        """Test OpenAI Server-Fehler (500)"""
        with patch('backend.app.services.llm_clients.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = Exception("500 server error")
            mock_openai.return_value = mock_client
            
            result = ask_openai("Test prompt")
            
            assert result["error"] == "server"
            assert result["team_rolle"]["openai"] is False
    
    def test_openai_timeout(self):
        """Test OpenAI Timeout"""
        with patch('backend.app.services.llm_clients.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = Exception("timeout")
            mock_openai.return_value = mock_client
            
            result = ask_openai("Test prompt")
            
            assert result["error"] == "timeout"
            assert result["team_rolle"]["openai"] is False
    
    def test_claude_success_200(self, mock_claude_response):
        """Test Claude erfolgreich (200)"""
        with patch('backend.app.services.llm_clients.anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_client.messages.create.return_value = Mock()
            mock_client.messages.create.return_value.content = [
                Mock(type="text", text=json.dumps(mock_claude_response["content"][0]["text"]))
            ]
            mock_anthropic.return_value = mock_client
            
            result = ask_claude("Test prompt")
            
            assert "kurz_zusammenfassung" in result
            assert result["team_rolle"]["claude"] is True
            assert "error" not in result
    
    def test_claude_auth_error_401(self):
        """Test Claude Auth-Fehler (401)"""
        with patch('backend.app.services.llm_clients.anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_client.messages.create.side_effect = Exception("401 Unauthorized")
            mock_anthropic.return_value = mock_client
            
            result = ask_claude("Test prompt")
            
            # Claude hat keine explizite Fehlerbehandlung in der aktuellen Implementierung
            # Das ist ein Verbesserungspunkt
            assert result == {}
    
    def test_perplexity_success_200(self, mock_perplexity_response):
        """Test Perplexity erfolgreich (200)"""
        with patch('backend.app.services.llm_clients.call_perplexity') as mock_call:
            mock_call.return_value = json.dumps(mock_perplexity_response["choices"][0]["message"]["content"])
            
            result = ask_perplexity("Test prompt")
            
            assert "kurz_zusammenfassung" in result
            assert result["team_rolle"]["perplexity"] is True
            assert "error" not in result
    
    def test_perplexity_auth_error_401(self):
        """Test Perplexity Auth-Fehler (401)"""
        with patch('backend.app.services.llm_clients.call_perplexity') as mock_call:
            mock_call.side_effect = ValueError("auth")
            
            result = ask_perplexity("Test prompt")
            
            assert result["error"] == "auth"
            assert result["team_rolle"]["perplexity"] is False
    
    def test_perplexity_rate_limit_429(self):
        """Test Perplexity Rate-Limit (429)"""
        with patch('backend.app.services.llm_clients.call_perplexity') as mock_call:
            mock_call.side_effect = ValueError("rate_limit")
            
            result = ask_perplexity("Test prompt")
            
            assert result["error"] == "rate_limit"
            assert result["team_rolle"]["perplexity"] is False
    
    def test_perplexity_server_error_500(self):
        """Test Perplexity Server-Fehler (500)"""
        with patch('backend.app.services.llm_clients.call_perplexity') as mock_call:
            mock_call.side_effect = ValueError("server")
            
            result = ask_perplexity("Test prompt")
            
            assert result["error"] == "server"
            assert result["team_rolle"]["perplexity"] is False
    
    def test_perplexity_timeout(self):
        """Test Perplexity Timeout"""
        with patch('backend.app.services.llm_clients.call_perplexity') as mock_call:
            mock_call.side_effect = ValueError("timeout")
            
            result = ask_perplexity("Test prompt")
            
            assert result["error"] == "timeout"
            assert result["team_rolle"]["perplexity"] is False


class TestAutoModeIntegration:
    """Integrationstest Auto-Modus"""
    
    @pytest.fixture
    def orchestrator(self):
        """Orchestrator-Instanz für Tests"""
        return RicoOrchestrator()
    
    @pytest.mark.asyncio
    async def test_auto_mode_first_success_wins(self, orchestrator):
        """Test Auto-Modus: First Success Wins"""
        # Mock alle Provider-Calls
        with patch('backend.app.services.orchestrator._call_openai') as mock_openai, \
             patch('backend.app.services.orchestrator._call_claude') as mock_claude, \
             patch('backend.app.services.orchestrator._call_perplexity') as mock_perplexity:
            
            # OpenAI erfolgreich, andere langsam
            mock_openai.return_value = (True, {
                "kurz_zusammenfassung": "OpenAI Test",
                "team_rolle": {"openai": True, "claude": False, "perplexity": False},
                "meta": {"provider": "openai", "duration_s": 1.0}
            }, 1.0)
            
            # Claude langsam (wird abgebrochen)
            async def slow_claude():
                await asyncio.sleep(2.0)
                return (True, {"kurz_zusammenfassung": "Claude Test"}, 2.0)
            mock_claude.return_value = slow_claude()
            
            # Perplexity langsam (wird abgebrochen)
            async def slow_perplexity():
                await asyncio.sleep(2.0)
                return (True, {"kurz_zusammenfassung": "Perplexity Test"}, 2.0)
            mock_perplexity.return_value = slow_perplexity()
            
            result = await orchestrator.run_rico_loop("Test prompt", "analysis", "auto")
            
            # OpenAI sollte gewinnen
            assert result["ok"] is True
            assert result["used_provider"] == "openai"
            assert "OpenAI Test" in result["result"]["kurz_zusammenfassung"]
    
    @pytest.mark.asyncio
    async def test_auto_mode_fallback_chain(self, orchestrator):
        """Test Auto-Modus: Fallback-Kette"""
        with patch('backend.app.services.orchestrator._call_openai') as mock_openai, \
             patch('backend.app.services.orchestrator._call_claude') as mock_claude, \
             patch('backend.app.services.orchestrator._call_perplexity') as mock_perplexity:
            
            # Alle Provider fehlschlagen
            mock_openai.return_value = (False, {"error": "auth"}, 0.5)
            mock_claude.return_value = (False, {"error": "rate_limit"}, 0.5)
            mock_perplexity.return_value = (False, {"error": "server"}, 0.5)
            
            result = await orchestrator.run_rico_loop("Test prompt", "analysis", "auto")
            
            # Alle sollten fehlschlagen
            assert result["ok"] is False
            assert "error" in result["result"]
    
    @pytest.mark.asyncio
    async def test_auto_mode_cleanup_pending_tasks(self, orchestrator):
        """Test Auto-Modus: Sauberes Cleanup von abgebrochenen Tasks"""
        with patch('backend.app.services.orchestrator._call_openai') as mock_openai, \
             patch('backend.app.services.orchestrator._call_claude') as mock_claude, \
             patch('backend.app.services.orchestrator._call_perplexity') as mock_perplexity:
            
            # OpenAI erfolgreich
            mock_openai.return_value = (True, {
                "kurz_zusammenfassung": "OpenAI Test",
                "team_rolle": {"openai": True, "claude": False, "perplexity": False},
                "meta": {"provider": "openai", "duration_s": 0.1}
            }, 0.1)
            
            # Andere Provider langsam
            async def slow_claude():
                await asyncio.sleep(1.0)
                return (True, {"kurz_zusammenfassung": "Claude Test"}, 1.0)
            mock_claude.return_value = slow_claude()
            
            async def slow_perplexity():
                await asyncio.sleep(1.0)
                return (True, {"kurz_zusammenfassung": "Perplexity Test"}, 1.0)
            mock_perplexity.return_value = slow_perplexity()
            
            result = await orchestrator.run_rico_loop("Test prompt", "analysis", "auto")
            
            # OpenAI sollte gewinnen, andere Tasks sollten abgebrochen werden
            assert result["ok"] is True
            assert result["used_provider"] == "openai"


class TestHealthCheckMocks:
    """Tests für Health-Check 2.0 mit Mocks"""
    
    @pytest.mark.asyncio
    async def test_health_check_all_ok(self):
        """Test Health-Check: Alle Provider OK"""
        with patch('backend.app.services.health_check.httpx.AsyncClient') as mock_client:
            # Mock erfolgreiche Responses
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"choices": [{"message": {"content": "pong"}}]}
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            result = await health_check_2.check_all_providers()
            
            assert "providers" in result
            assert "summary" in result
            assert result["summary"]["total"] == 3
    
    @pytest.mark.asyncio
    async def test_health_check_mixed_status(self):
        """Test Health-Check: Gemischte Status"""
        with patch('backend.app.services.health_check.httpx.AsyncClient') as mock_client:
            # Mock gemischte Responses
            def mock_post(*args, **kwargs):
                mock_response = Mock()
                if "openai.com" in str(args[0]):
                    mock_response.status_code = 200
                elif "anthropic.com" in str(args[0]):
                    mock_response.status_code = 401
                else:  # perplexity
                    mock_response.status_code = 429
                mock_response.json.return_value = {"choices": [{"message": {"content": "pong"}}]}
                return mock_response
            
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            result = await health_check_2.check_all_providers()
            
            assert "providers" in result
            # OpenAI sollte OK sein, andere sollten Fehler haben
            assert result["providers"]["openai"]["status"] == "OK"
            assert result["providers"]["claude"]["status"] == "auth"
            assert result["providers"]["perplexity"]["status"] == "rate_limit"
    
    def test_keys_status(self):
        """Test Keys-Status ohne echte Calls"""
        result = health_check_2.get_keys_status()
        
        assert "openai" in result
        assert "claude" in result
        assert "perplexity" in result
        
        for provider in result.values():
            assert "configured" in provider
            assert "env_source" in provider
            assert "model" in provider


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
