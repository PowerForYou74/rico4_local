#!/usr/bin/env python3
"""
Perplexity Integration Tests
===========================

Diese Tests prüfen die Perplexity-Integration in Rico 4.0:
- PPLX-Client Funktionalität
- Orchestrator-Integration mit Perplexity
- Health-Check für Perplexity
- Auto-Modus mit/ohne PPLX-Key
"""

import pytest
import json
import asyncio
import requests
import time
from typing import Dict, Any
import sys
import os
from unittest.mock import patch, AsyncMock

# Projekt-Pfad hinzufügen
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.orchestrator import RicoOrchestrator
from app.services.llm_clients import call_perplexity, ask_perplexity


class TestPerplexityClient:
    """Tests für den Perplexity-Client"""
    
    @pytest.mark.asyncio
    async def test_call_perplexity_success(self):
        """Test: Erfolgreicher Perplexity-API-Call"""
        mock_response = {
            "choices": [{
                "message": {
                    "content": '{"kurz_zusammenfassung": "Test-Zusammenfassung", "kernbefunde": ["Test 1", "Test 2"]}'
                }
            }]
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value.json.return_value = mock_response
            mock_client.return_value.__aenter__.return_value.post.return_value.raise_for_status.return_value = None
            
            with patch.dict(os.environ, {'PPLX_API_KEY': 'test-key'}):
                result = await call_perplexity(
                    prompt="Test prompt",
                    system="Test system",
                    model="sonar",
                    timeout=30.0
                )
                
                assert result == '{"kurz_zusammenfassung": "Test-Zusammenfassung", "kernbefunde": ["Test 1", "Test 2"]}'
    
    @pytest.mark.asyncio
    async def test_call_perplexity_no_key(self):
        """Test: Perplexity-Call ohne API-Key"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="PPLX_API_KEY not configured"):
                await call_perplexity(
                    prompt="Test prompt",
                    system="Test system", 
                    model="sonar",
                    timeout=30.0
                )
    
    @pytest.mark.asyncio
    async def test_call_perplexity_http_error(self):
        """Test: Perplexity-Call mit HTTP-Fehler"""
        with patch('httpx.AsyncClient') as mock_client:
            from httpx import HTTPStatusError
            mock_response = AsyncMock()
            mock_response.status_code = 401
            mock_error = HTTPStatusError("Unauthorized", request=AsyncMock(), response=mock_response)
            mock_client.return_value.__aenter__.return_value.post.side_effect = mock_error
            
            with patch.dict(os.environ, {'PPLX_API_KEY': 'test-key'}):
                with pytest.raises(ValueError, match="Invalid Perplexity API key"):
                    await call_perplexity(
                        prompt="Test prompt",
                        system="Test system",
                        model="sonar", 
                        timeout=30.0
                    )
    
    def test_ask_perplexity_success(self):
        """Test: Synchroner Perplexity-Call"""
        mock_result = '{"kurz_zusammenfassung": "Test", "team_rolle": {"perplexity": true}}'
        
        with patch('app.services.llm_clients.call_perplexity', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_result
            
            with patch.dict(os.environ, {'PPLX_API_KEY': 'test-key', 'PPLX_MODEL': 'sonar'}):
                result = ask_perplexity("Test prompt")
                
                assert result["kurz_zusammenfassung"] == "Test"
                assert result["team_rolle"]["perplexity"] is True
    
    def test_ask_perplexity_no_key(self):
        """Test: Synchroner Perplexity-Call ohne Key"""
        with patch.dict(os.environ, {}, clear=True):
            result = ask_perplexity("Test prompt")
            assert result == {}


class TestPerplexityOrchestrator:
    """Tests für Perplexity-Integration im Orchestrator"""
    
    @pytest.mark.asyncio
    async def test_orchestrator_perplexity_provider(self):
        """Test: Orchestrator mit Perplexity-Provider"""
        orchestrator = RicoOrchestrator()
        
        # Mock Perplexity-Response
        mock_response = {
            "choices": [{
                "message": {
                    "content": '{"kurz_zusammenfassung": "Perplexity Test", "kernbefunde": ["PPLX 1", "PPLX 2"]}'
                }
            }]
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value.json.return_value = mock_response
            mock_client.return_value.__aenter__.return_value.post.return_value.raise_for_status.return_value = None
            
            with patch.dict(os.environ, {'PPLX_API_KEY': 'test-key', 'PPLX_MODEL': 'sonar'}):
                result = await orchestrator.run_rico_loop(
                    prompt="Test prompt",
                    task_type="analysis",
                    provider="perplexity"
                )
                
                assert result["ok"] is True
                assert result["used_provider"] == "perplexity"
                assert "Perplexity Test" in result["result"]["kurz_zusammenfassung"]
                assert result["result"]["team_rolle"]["perplexity"] is True
    
    @pytest.mark.asyncio
    async def test_orchestrator_auto_with_pplx_key(self):
        """Test: Auto-Modus mit PPLX-Key"""
        orchestrator = RicoOrchestrator()
        
        # Mock alle Provider-Responses
        mock_pplx_response = {
            "choices": [{
                "message": {
                    "content": '{"kurz_zusammenfassung": "Perplexity Auto Test", "kernbefunde": ["Auto PPLX"]}'
                }
            }]
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value.json.return_value = mock_pplx_response
            mock_client.return_value.__aenter__.return_value.post.return_value.raise_for_status.return_value = None
            
            with patch.dict(os.environ, {
                'PPLX_API_KEY': 'test-key',
                'PPLX_MODEL': 'sonar',
                'OPENAI_API_KEY': 'test-openai-key',
                'ANTHROPIC_API_KEY': 'test-claude-key'
            }):
                result = await orchestrator.run_rico_loop(
                    prompt="Test prompt",
                    task_type="analysis", 
                    provider="auto"
                )
                
                # Auto-Modus sollte einen der Provider verwenden
                assert result["ok"] is True
                assert result["used_provider"] in ["openai", "claude", "perplexity"]
    
    @pytest.mark.asyncio
    async def test_orchestrator_auto_without_pplx_key(self):
        """Test: Auto-Modus ohne PPLX-Key"""
        orchestrator = RicoOrchestrator()
        
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-openai-key',
            'ANTHROPIC_API_KEY': 'test-claude-key'
            # PPLX_API_KEY nicht gesetzt
        }):
            # Mock OpenAI/Claude responses
            with patch('httpx.AsyncClient') as mock_client:
                mock_response = {
                    "choices": [{
                        "message": {
                            "content": '{"kurz_zusammenfassung": "OpenAI Test", "kernbefunde": ["OpenAI"]}'
                        }
                    }]
                }
                mock_client.return_value.__aenter__.return_value.post.return_value.json.return_value = mock_response
                mock_client.return_value.__aenter__.return_value.post.return_value.raise_for_status.return_value = None
                
                result = await orchestrator.run_rico_loop(
                    prompt="Test prompt",
                    task_type="analysis",
                    provider="auto"
                )
                
                # Sollte nur OpenAI/Claude verwenden, nicht Perplexity
                assert result["ok"] is True
                assert result["used_provider"] in ["openai", "claude"]


class TestPerplexityHealthCheck:
    """Tests für Perplexity Health-Check"""
    
    def test_check_keys_with_pplx(self):
        """Test: Health-Check mit Perplexity-Key"""
        try:
            response = requests.get("http://127.0.0.1:8000/check-keys", timeout=5)
            assert response.status_code == 200
            
            data = response.json()
            assert "perplexity" in data
            assert "models" in data
            assert "perplexity" in data["models"]
            
            # Status sollte OK, N/A oder Fehler sein
            assert data["perplexity"] in ["OK", "N/A", "Fehler"]
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend nicht verfügbar")
    
    def test_check_keys_models_field(self):
        """Test: Models-Feld enthält alle Provider"""
        try:
            response = requests.get("http://127.0.0.1:8000/check-keys", timeout=5)
            assert response.status_code == 200
            
            data = response.json()
            models = data.get("models", {})
            
            assert "openai" in models
            assert "claude" in models  
            assert "perplexity" in models
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend nicht verfügbar")


class TestPerplexityAPI:
    """Tests für Perplexity API-Endpunkte"""
    
    API_BASE = "http://127.0.0.1:8000"
    
    def test_task_endpoint_perplexity(self):
        """Test: Task-Endpunkt mit Perplexity-Provider"""
        try:
            payload = {
                "prompt": "Kurzer Perplexity-Test.",
                "task_type": "analysis",
                "provider": "perplexity"
            }
            
            response = requests.post(
                f"{self.API_BASE}/api/v1/task",
                json=payload,
                timeout=30
            )
            
            # Sollte 200 oder 422 (falls kein PPLX-Key) sein
            assert response.status_code in [200, 422]
            
            if response.status_code == 200:
                data = response.json()
                assert "result" in data
                assert "used_provider" in data
                
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend nicht verfügbar")
    
    def test_task_endpoint_auto_with_pplx(self):
        """Test: Task-Endpunkt Auto-Modus mit PPLX-Key"""
        try:
            payload = {
                "prompt": "Auto-Modus Test mit Perplexity.",
                "task_type": "analysis", 
                "provider": "auto"
            }
            
            response = requests.post(
                f"{self.API_BASE}/api/v1/task",
                json=payload,
                timeout=30
            )
            
            # Sollte 200 oder 422 sein
            assert response.status_code in [200, 422]
            
            if response.status_code == 200:
                data = response.json()
                assert "result" in data
                assert "used_provider" in data
                # Auto-Modus könnte Perplexity verwenden
                assert data["used_provider"] in ["openai", "claude", "perplexity"]
                
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend nicht verfügbar")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
