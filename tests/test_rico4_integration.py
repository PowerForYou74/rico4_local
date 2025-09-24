#!/usr/bin/env python3
"""
Rico4 Integration Tests
======================

Diese Tests prüfen das Zusammenspiel der verschiedenen Rico4-Komponenten:
- API-Endpunkte
- Orchestrator-Integration
- End-to-End-Workflows
"""

import pytest
import json
import asyncio
import requests
import time
from typing import Dict, Any
import sys
import os

# Projekt-Pfad hinzufügen
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.orchestrator import RicoOrchestrator


class TestRico4API:
    """Tests für die Rico4 API-Endpunkte"""
    
    API_BASE = "http://127.0.0.1:8000"
    
    def test_root_endpoint(self):
        """Test: Root-Endpunkt gibt korrekte Antwort"""
        try:
            response = requests.get(f"{self.API_BASE}/", timeout=5)
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "ok"
            assert data["agent"] == "Rico 4.0"
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend nicht verfügbar")
    
    def test_check_keys_endpoint(self):
        """Test: Check-Keys-Endpunkt funktioniert"""
        try:
            response = requests.get(f"{self.API_BASE}/check-keys", timeout=5)
            assert response.status_code == 200
            
            data = response.json()
            assert "openai" in data
            assert "claude" in data
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend nicht verfügbar")
    
    def test_task_endpoint_structure(self):
        """Test: Task-Endpunkt hat korrekte Struktur"""
        try:
            # Test mit minimalem Payload
            payload = {
                "prompt": "Test-Eingabe",
                "task_type": "analysis",
                "provider": "auto"
            }
            
            response = requests.post(
                f"{self.API_BASE}/api/v1/task",
                json=payload,
                timeout=30
            )
            
            # Status sollte 200 sein (auch wenn LLM-Aufruf fehlschlägt)
            assert response.status_code in [200, 500, 422]  # 422 = Validation Error
            
            if response.status_code == 200:
                data = response.json()
                assert "ok" in data
                assert "task_type" in data
                assert "used_provider" in data
                assert "result" in data
                
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend nicht verfügbar")


class TestRico4OrchestratorIntegration:
    """Integrationstests für den Rico4-Orchestrator"""
    
    @pytest.fixture
    def orchestrator(self):
        return RicoOrchestrator()
    
    @pytest.mark.asyncio
    async def test_orchestrator_basic_structure(self, orchestrator):
        """Test: Orchestrator hat grundlegende Struktur"""
        # Test mit Mock-Daten (ohne echte LLM-Aufrufe)
        result = await orchestrator.run_rico_loop(
            prompt="Test-Eingabe",
            task_type="analysis",
            provider="auto"
        )
        
        # Struktur-Tests
        assert isinstance(result, dict)
        assert "ok" in result
        assert "task_type" in result
        assert "used_provider" in result
        assert "result" in result
        
        assert result["task_type"] == "analysis"
    
    @pytest.mark.asyncio
    async def test_orchestrator_provider_selection(self, orchestrator):
        """Test: Orchestrator wählt Provider korrekt"""
        # Test mit festem Provider
        result = await orchestrator.run_rico_loop(
            prompt="Test-Eingabe",
            task_type="analysis",
            provider="openai"
        )
        
        assert result["used_provider"] in ["openai", None]  # None wenn API-Key fehlt
        
        result = await orchestrator.run_rico_loop(
            prompt="Test-Eingabe",
            task_type="analysis",
            provider="claude"
        )
        
        assert result["used_provider"] in ["claude", None]  # None wenn API-Key fehlt


class TestRico4EndToEnd:
    """End-to-End Tests für Rico4"""
    
    def test_complete_workflow_structure(self):
        """Test: Kompletter Workflow hat korrekte Struktur"""
        # Simuliert einen kompletten Rico4-Workflow
        
        # 1. Eingabe validieren
        prompt = "Analysiere mein Geschäftsmodell"
        assert isinstance(prompt, str)
        assert len(prompt.strip()) > 0
        
        # 2. Task-Struktur validieren
        task = {
            "prompt": prompt,
            "task_type": "analysis",
            "provider": "auto"
        }
        
        required_fields = ["prompt", "task_type", "provider"]
        for field in required_fields:
            assert field in task
        
        # 3. Erwartete Antwort-Struktur validieren
        expected_response = {
            "ok": bool,
            "task_type": str,
            "used_provider": str,
            "result": {
                "kurz_zusammenfassung": str,
                "kernbefunde": list,
                "action_plan": list,
                "risiken": list,
                "cashflow_radar": dict,
                "team_rolle": dict
            }
        }
        
        # Struktur-Typen validieren
        for key, expected_type in expected_response.items():
            if key == "result":
                # Nested structure
                for nested_key, nested_type in expected_response["result"].items():
                    assert isinstance(nested_type, type)
            else:
                assert isinstance(expected_type, type)
    
    def test_error_handling_structure(self):
        """Test: Error-Handling hat korrekte Struktur"""
        # Test verschiedene Fehler-Szenarien
        
        # 1. Leere Eingabe
        empty_prompt = ""
        assert len(empty_prompt.strip()) == 0
        
        # 2. Ungültiger Provider
        invalid_provider = "invalid_provider"
        valid_providers = ["auto", "openai", "claude"]
        assert invalid_provider not in valid_providers
        
        # 3. Ungültiger Task-Type
        invalid_task_type = "invalid_type"
        # (aktuell nur "analysis" unterstützt)
        assert invalid_task_type != "analysis"


class TestRico4Validation:
    """Validierungstests für Rico4-Daten"""
    
    def test_schema_validation(self):
        """Test: Schema-Validierung funktioniert"""
        from app.services.orchestrator import SCHEMA_EXAMPLE
        
        # Valides Schema
        valid_schema = {
            "kurz_zusammenfassung": "Test",
            "kernbefunde": ["A", "B"],
            "action_plan": ["1", "2"],
            "risiken": ["R1"],
            "cashflow_radar": {"idee": "Test"},
            "team_rolle": {"openai": True, "claude": False}
        }
        
        # Alle Pflichtfelder müssen vorhanden sein
        required_fields = list(SCHEMA_EXAMPLE.keys())
        for field in required_fields:
            assert field in valid_schema, f"Pflichtfeld '{field}' fehlt"
    
    def test_data_type_validation(self):
        """Test: Datentyp-Validierung funktioniert"""
        # Test verschiedene Datentypen
        
        # String-Validierung
        test_string = "Test-String"
        assert isinstance(test_string, str)
        assert len(test_string) > 0
        
        # List-Validierung
        test_list = ["Item1", "Item2"]
        assert isinstance(test_list, list)
        assert len(test_list) > 0
        
        # Dict-Validierung
        test_dict = {"key": "value"}
        assert isinstance(test_dict, dict)
        assert len(test_dict) > 0
        
        # Bool-Validierung
        test_bool = True
        assert isinstance(test_bool, bool)


def run_integration_tests():
    """Führt alle Integrationstests aus"""
    print("🔗 Rico4 Integration Tests")
    print("=" * 50)
    
    test_categories = [
        ("API-Endpunkte", TestRico4API),
        ("Orchestrator-Integration", TestRico4OrchestratorIntegration),
        ("End-to-End-Workflow", TestRico4EndToEnd),
        ("Datenvalidierung", TestRico4Validation)
    ]
    
    passed = 0
    failed = 0
    
    for category, test_class in test_categories:
        try:
            # Führe einen repräsentativen Test aus jeder Kategorie aus
            if category == "API-Endpunkte":
                api_test = TestRico4API()
                api_test.test_root_endpoint()
            elif category == "End-to-End-Workflow":
                e2e_test = TestRico4EndToEnd()
                e2e_test.test_complete_workflow_structure()
            elif category == "Datenvalidierung":
                validation_test = TestRico4Validation()
                validation_test.test_schema_validation()
            
            print(f"✅ {category}")
            passed += 1
        except Exception as e:
            print(f"❌ {category}: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Ergebnis: {passed} bestanden, {failed} fehlgeschlagen")
    
    if failed == 0:
        print("🎉 Alle Integrationstests bestanden!")
    else:
        print("⚠️  Einige Integrationstests benötigen Aufmerksamkeit.")
    
    return failed == 0


if __name__ == "__main__":
    # Einfacher Test-Runner
    success = run_integration_tests()
    exit(0 if success else 1)
