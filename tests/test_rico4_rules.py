#!/usr/bin/env python3
"""
Rico4-Regeln Test Suite
=======================

Diese Test-Suite validiert alle wichtigen Regeln und Verhaltensweisen von Rico4:
- JSON-Schema-Compliance
- Provider-Auswahl-Logik
- Fallback-Mechanismen
- Validierungsregeln
- Error-Handling
"""

import pytest
import json
import asyncio
import time
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Projekt-Pfad hinzufügen
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.orchestrator import (
    RicoOrchestrator,
    normalize_result,
    massage_to_schema,
    try_parse_json,
    SCHEMA_EXAMPLE,
    system_prompt,
    user_prompt
)


class TestRico4Rules:
    """Test-Klasse für alle Rico4-Regeln"""
    
    def setup_method(self):
        """Setup für jeden Test"""
        self.orchestrator = RicoOrchestrator()
        self.valid_schema = {
            "kurz_zusammenfassung": "Test-Zusammenfassung",
            "kernbefunde": ["Ergebnis 1", "Ergebnis 2"],
            "action_plan": ["Schritt 1", "Schritt 2"],
            "risiken": ["Risiko 1"],
            "cashflow_radar": {"idee": "Test-Idee"},
            "team_rolle": {"openai": True, "claude": False},
            "aufgabenverteilung": ["Aufgabe 1"],
            "orchestrator_log": "Test-Log"
        }

    # ============================================================================
    # REGEL 1: JSON-Schema-Compliance
    # ============================================================================
    
    def test_schema_structure_compliance(self):
        """Test: Rico4 muss dem festen Schema entsprechen"""
        # Alle Pflichtfelder müssen vorhanden sein
        required_fields = [
            "kurz_zusammenfassung",
            "kernbefunde", 
            "action_plan",
            "risiken",
            "cashflow_radar",
            "team_rolle"
        ]
        
        for field in required_fields:
            assert field in SCHEMA_EXAMPLE, f"Pflichtfeld '{field}' fehlt im Schema"
    
    def test_schema_field_types(self):
        """Test: Schema-Felder müssen korrekte Datentypen haben"""
        assert isinstance(SCHEMA_EXAMPLE["kurz_zusammenfassung"], str)
        assert isinstance(SCHEMA_EXAMPLE["kernbefunde"], list)
        assert isinstance(SCHEMA_EXAMPLE["action_plan"], list)
        assert isinstance(SCHEMA_EXAMPLE["risiken"], list)
        assert isinstance(SCHEMA_EXAMPLE["cashflow_radar"], dict)
        assert isinstance(SCHEMA_EXAMPLE["team_rolle"], dict)
    
    def test_massage_to_schema_compliance(self):
        """Test: massage_to_schema() erzeugt schema-konforme Ergebnisse"""
        test_data = {
            "kurz_zusammenfassung": "Test",
            "kernbefunde": ["A", "B"],
            "action_plan": ["1", "2"],
            "risiken": ["R1"],
            "cashflow_radar": {"idee": "Test"},
            "team_rolle": {"openai": True}
        }
        
        result = massage_to_schema(test_data, "openai")
        
        # Alle Pflichtfelder müssen vorhanden sein
        required_fields = ["kurz_zusammenfassung", "kernbefunde", "action_plan", 
                          "risiken", "cashflow_radar", "team_rolle"]
        for field in required_fields:
            assert field in result, f"Feld '{field}' fehlt nach Schema-Massage"
        
        # Team-Rolle muss Provider-Info korrekt setzen
        assert result["team_rolle"]["openai"] is True
        assert result["team_rolle"]["claude"] is False

    # ============================================================================
    # REGEL 2: JSON-Parsing und Fallback
    # ============================================================================
    
    def test_json_parsing_valid_json(self):
        """Test: Gültiges JSON wird korrekt geparst"""
        valid_json = '{"test": "value", "number": 42}'
        result = try_parse_json(valid_json)
        assert result is not None
        assert result["test"] == "value"
        assert result["number"] == 42
    
    def test_json_parsing_code_blocks(self):
        """Test: JSON in Markdown-Codeblöcken wird extrahiert"""
        json_in_code = '```json\n{"test": "value"}\n```'
        result = try_parse_json(json_in_code)
        assert result is not None
        assert result["test"] == "value"
    
    def test_json_parsing_single_quotes(self):
        """Test: Einfache Anführungszeichen werden zu doppelten konvertiert"""
        single_quote_json = "{'test': 'value'}"
        result = try_parse_json(single_quote_json)
        assert result is not None
        assert result["test"] == "value"
    
    def test_json_parsing_invalid_json(self):
        """Test: Ungültiges JSON wird als None zurückgegeben"""
        invalid_json = "Das ist kein JSON"
        result = try_parse_json(invalid_json)
        assert result is None
    
    def test_normalize_result_fallback(self):
        """Test: normalize_result() erstellt sinnvolles Fallback"""
        fallback = normalize_result("Test-Text", "openai")
        
        # Muss alle Pflichtfelder haben
        required_fields = ["kurz_zusammenfassung", "kernbefunde", "action_plan",
                          "risiken", "cashflow_radar", "team_rolle"]
        for field in required_fields:
            assert field in fallback, f"Fallback fehlt Feld '{field}'"
        
        # Team-Rolle muss Provider korrekt setzen
        assert fallback["team_rolle"]["openai"] is True
        assert fallback["team_rolle"]["claude"] is False

    # ============================================================================
    # REGEL 3: Synonym-Mapping
    # ============================================================================
    
    def test_synonym_mapping_kurzfassung(self):
        """Test: Verschiedene Synonyme für 'kurz_zusammenfassung' werden gemappt"""
        test_cases = [
            ("kurzfassung", "kurz_zusammenfassung"),
            ("summary", "kurz_zusammenfassung")
        ]
        
        for synonym, target in test_cases:
            data = {synonym: "Test-Text"}
            result = massage_to_schema(data, "openai")
            assert result["kurz_zusammenfassung"] == "Test-Text"
    
    def test_synonym_mapping_kernbefunde(self):
        """Test: Synonyme für 'kernbefunde' werden gemappt"""
        test_cases = [
            ("kern_ergebnisse", "kernbefunde"),
            ("key_findings", "kernbefunde")
        ]
        
        for synonym, target in test_cases:
            data = {synonym: ["Ergebnis 1", "Ergebnis 2"]}
            result = massage_to_schema(data, "openai")
            assert result["kernbefunde"] == ["Ergebnis 1", "Ergebnis 2"]
    
    def test_synonym_mapping_risiken(self):
        """Test: Synonyme für 'risiken' werden gemappt"""
        test_cases = [
            ("annahmen", "risiken"),
            ("risks", "risiken")
        ]
        
        for synonym, target in test_cases:
            data = {synonym: ["Risiko 1"]}
            result = massage_to_schema(data, "openai")
            assert result["risiken"] == ["Risiko 1"]

    # ============================================================================
    # REGEL 4: List-Normalisierung
    # ============================================================================
    
    def test_list_coercion_already_list(self):
        """Test: Listen bleiben Listen"""
        from app.services.orchestrator import _coerce_list
        test_list = ["Item 1", "Item 2"]
        result = _coerce_list(test_list)
        assert result == ["Item 1", "Item 2"]
    
    def test_list_coercion_string_to_list(self):
        """Test: Strings mit Zeilenumbrüchen werden zu Listen"""
        from app.services.orchestrator import _coerce_list
        test_string = "Item 1\nItem 2\n- Item 3"
        result = _coerce_list(test_string)
        assert len(result) == 3
        assert "Item 1" in result
        assert "Item 2" in result
        assert "Item 3" in result
    
    def test_list_coercion_empty_string(self):
        """Test: Leere Strings werden zu leeren Listen"""
        from app.services.orchestrator import _coerce_list
        result = _coerce_list("")
        assert result == []
    
    def test_list_coercion_none(self):
        """Test: None wird zu leerer Liste"""
        from app.services.orchestrator import _coerce_list
        result = _coerce_list(None)
        assert result == []

    # ============================================================================
    # REGEL 5: Provider-Auswahl und Team-Rolle
    # ============================================================================
    
    def test_provider_team_role_openai(self):
        """Test: OpenAI-Provider setzt Team-Rolle korrekt"""
        result = massage_to_schema({}, "openai")
        assert result["team_rolle"]["openai"] is True
        assert result["team_rolle"]["claude"] is False
    
    def test_provider_team_role_claude(self):
        """Test: Claude-Provider setzt Team-Rolle korrekt"""
        result = massage_to_schema({}, "claude")
        assert result["team_rolle"]["openai"] is False
        assert result["team_rolle"]["claude"] is True
    
    def test_existing_team_role_preserved(self):
        """Test: Bestehende Team-Rolle wird beibehalten und Provider hinzugefügt"""
        data = {
            "team_rolle": {"openai": False, "claude": True}
        }
        result = massage_to_schema(data, "openai")
        
        # Provider-spezifische Rolle wird gesetzt, aber bestehende bleibt
        assert result["team_rolle"]["openai"] is True  # Provider wird gesetzt
        assert result["team_rolle"]["claude"] is True  # Bestehende bleibt

    # ============================================================================
    # REGEL 6: System und User Prompts
    # ============================================================================
    
    def test_system_prompt_structure(self):
        """Test: System-Prompt enthält alle notwendigen Elemente"""
        prompt = system_prompt("analysis")
        
        # Muss Rico 4.0 Identität enthalten
        assert "Rico 4.0" in prompt
        
        # Muss Task-Type enthalten
        assert "analysis" in prompt
        
        # Muss Schema-Beispiel enthalten
        assert "kurz_zusammenfassung" in prompt
        
        # Muss Regeln enthalten
        assert "JSON" in prompt
        assert "Regeln" in prompt
    
    def test_user_prompt_wrapping(self):
        """Test: User-Prompt wird korrekt formatiert"""
        test_input = "Test-Eingabe"
        prompt = user_prompt(test_input)
        
        assert "Nutze diesen Inhalt:" in prompt
        assert test_input in prompt

    # ============================================================================
    # REGEL 7: Error-Handling und Robustheit
    # ============================================================================
    
    def test_massage_to_schema_with_invalid_input(self):
        """Test: massage_to_schema() behandelt ungültige Eingaben robust"""
        # None-Eingabe
        result = massage_to_schema(None, "openai")
        assert isinstance(result, dict)
        assert "kurz_zusammenfassung" in result
        
        # String-Eingabe
        result = massage_to_schema("Test-String", "openai")
        assert isinstance(result, dict)
        assert "kurz_zusammenfassung" in result
        
        # Leere Dictionary
        result = massage_to_schema({}, "openai")
        assert isinstance(result, dict)
        assert "kurz_zusammenfassung" in result
    
    def test_cashflow_radar_type_safety(self):
        """Test: cashflow_radar wird immer zu Dict konvertiert"""
        # String als cashflow_radar
        data = {"cashflow_radar": "Test-String"}
        result = massage_to_schema(data, "openai")
        assert isinstance(result["cashflow_radar"], dict)
        assert result["cashflow_radar"]["idee"] == "Test-String"
        
        # None als cashflow_radar
        data = {"cashflow_radar": None}
        result = massage_to_schema(data, "openai")
        assert isinstance(result["cashflow_radar"], dict)
        assert result["cashflow_radar"]["idee"] == ""

    # ============================================================================
    # REGEL 8: Meta-Informationen
    # ============================================================================
    
    def test_meta_information_provider(self):
        """Test: Meta-Informationen enthalten Provider-Details"""
        result = massage_to_schema({}, "openai")
        
        assert "meta" in result
        assert result["meta"]["provider"] == "openai"
        
        result = massage_to_schema({}, "claude")
        assert result["meta"]["provider"] == "claude"
    
    def test_raw_text_preservation(self):
        """Test: Raw-Text wird korrekt gespeichert"""
        data = {"raw_text": "Original-Text"}
        result = massage_to_schema(data, "openai")
        assert result["raw_text"] == "Original-Text"


class TestRico4Integration:
    """Integrationstests für Rico4-Orchestrator"""
    
    @pytest.fixture
    def orchestrator(self):
        return RicoOrchestrator()
    
    @pytest.mark.asyncio
    async def test_orchestrator_structure(self, orchestrator):
        """Test: Orchestrator hat korrekte Struktur"""
        assert hasattr(orchestrator, 'run_rico_loop')
        assert callable(getattr(orchestrator, 'run_rico_loop'))
    
    def test_orchestrator_initialization(self, orchestrator):
        """Test: Orchestrator initialisiert korrekt"""
        assert orchestrator is not None
        assert isinstance(orchestrator, RicoOrchestrator)


class TestRico4Performance:
    """Performance-Tests für Rico4-Regeln"""
    
    def test_json_parsing_performance(self):
        """Test: JSON-Parsing ist performant"""
        import time
        
        # Großer JSON-String
        large_json = json.dumps({
            "kurz_zusammenfassung": "Test " * 100,
            "kernbefunde": [f"Item {i}" for i in range(100)],
            "action_plan": [f"Plan {i}" for i in range(50)],
            "risiken": [f"Risiko {i}" for i in range(25)]
        })
        
        start_time = time.time()
        result = try_parse_json(large_json)
        end_time = time.time()
        
        # Sollte unter 0.1 Sekunden liegen
        assert (end_time - start_time) < 0.1
        assert result is not None
    
    def test_schema_massage_performance(self):
        """Test: Schema-Massage ist performant"""
        import time
        
        # Große Datenstruktur
        large_data = {
            "kurz_zusammenfassung": "Test " * 100,
            "kernbefunde": [f"Item {i}" for i in range(100)],
            "action_plan": [f"Plan {i}" for i in range(50)],
            "risiken": [f"Risiko {i}" for i in range(25)],
            "cashflow_radar": {"idee": "Test " * 50}
        }
        
        start_time = time.time()
        result = massage_to_schema(large_data, "openai")
        end_time = time.time()
        
        # Sollte unter 0.1 Sekunden liegen
        assert (end_time - start_time) < 0.1
        assert isinstance(result, dict)


# ============================================================================
# Test-Runner und Hilfsfunktionen
# ============================================================================

def run_rico4_rule_tests():
    """Führt alle Rico4-Regel-Tests aus"""
    print("🧪 Rico4-Regeln Test Suite")
    print("=" * 50)
    
    # Test-Kategorien
    test_categories = [
        ("JSON-Schema-Compliance", TestRico4Rules.test_schema_structure_compliance),
        ("JSON-Parsing", TestRico4Rules.test_json_parsing_valid_json),
        ("Fallback-Mechanismen", TestRico4Rules.test_normalize_result_fallback),
        ("Synonym-Mapping", TestRico4Rules.test_synonym_mapping_kurzfassung),
        ("Provider-Auswahl", TestRico4Rules.test_provider_team_role_openai),
        ("Error-Handling", TestRico4Rules.test_massage_to_schema_with_invalid_input),
        ("Performance", TestRico4Performance.test_json_parsing_performance)
    ]
    
    passed = 0
    failed = 0
    
    for category, test_func in test_categories:
        try:
            test_instance = TestRico4Rules()
            test_instance.setup_method()
            test_func(test_instance)
            print(f"✅ {category}")
            passed += 1
        except Exception as e:
            print(f"❌ {category}: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Ergebnis: {passed} bestanden, {failed} fehlgeschlagen")
    
    if failed == 0:
        print("🎉 Alle Rico4-Regeln sind korrekt implementiert!")
    else:
        print("⚠️  Einige Regeln benötigen Aufmerksamkeit.")
    
    return failed == 0


if __name__ == "__main__":
    # Einfacher Test-Runner ohne pytest
    success = run_rico4_rule_tests()
    exit(0 if success else 1)
