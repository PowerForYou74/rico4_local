#!/usr/bin/env python3
"""
Rico4 Spezifische Regeln Tests
==============================

Tests für die wichtigsten und kritischsten Rico4-Regeln:
- JSON-Schema-Validierung
- Provider-Auswahl-Logik
- Fallback-Mechanismen
- Error-Handling
- Performance-Grenzen
"""

import pytest
import json
import time
from typing import Dict, Any, List
import sys
import os

# Projekt-Pfad hinzufügen
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.orchestrator import (
    RicoOrchestrator,
    normalize_result,
    massage_to_schema,
    try_parse_json,
    _coerce_list,
    SCHEMA_EXAMPLE,
    system_prompt,
    user_prompt
)


class TestRico4CriticalRules:
    """Tests für die kritischsten Rico4-Regeln"""
    
    def setup_method(self):
        """Setup für jeden Test"""
        self.orchestrator = RicoOrchestrator()

    # ============================================================================
    # KRITISCHE REGEL 1: JSON-Schema muss IMMER eingehalten werden
    # ============================================================================
    
    def test_schema_compliance_mandatory(self):
        """KRITISCH: Schema-Compliance ist zwingend erforderlich"""
        # Test: Jede Antwort muss alle Pflichtfelder haben
        required_fields = [
            "kurz_zusammenfassung",
            "kernbefunde",
            "action_plan", 
            "risiken",
            "cashflow_radar",
            "team_rolle"
        ]
        
        # Test mit verschiedenen Eingaben
        test_inputs = [
            {},  # Leere Eingabe
            {"test": "value"},  # Falsche Felder
            None,  # None-Eingabe
            "String-Eingabe"  # String-Eingabe
        ]
        
        for test_input in test_inputs:
            result = massage_to_schema(test_input, "openai")
            
            # ALLE Pflichtfelder müssen vorhanden sein
            for field in required_fields:
                assert field in result, f"KRITISCH: Pflichtfeld '{field}' fehlt nach Schema-Massage"
                
            # Datentypen müssen korrekt sein
            assert isinstance(result["kurz_zusammenfassung"], str)
            assert isinstance(result["kernbefunde"], list)
            assert isinstance(result["action_plan"], list)
            assert isinstance(result["risiken"], list)
            assert isinstance(result["cashflow_radar"], dict)
            assert isinstance(result["team_rolle"], dict)
    
    def test_schema_field_types_never_break(self):
        """KRITISCH: Schema-Feldtypen dürfen niemals brechen"""
        # Test: Auch bei ungültigen Eingaben müssen Typen stimmen
        problematic_inputs = [
            {"kernbefunde": "String statt Liste"},
            {"action_plan": 123},
            {"risiken": None},
            {"cashflow_radar": "String statt Dict"},
            {"team_rolle": "String statt Dict"}
        ]
        
        for problematic_input in problematic_inputs:
            result = massage_to_schema(problematic_input, "openai")
            
            # Typen müssen IMMER korrekt sein
            assert isinstance(result["kernbefunde"], list), "kernbefunde muss immer Liste sein"
            assert isinstance(result["action_plan"], list), "action_plan muss immer Liste sein"
            assert isinstance(result["risiken"], list), "risiken muss immer Liste sein"
            assert isinstance(result["cashflow_radar"], dict), "cashflow_radar muss immer Dict sein"
            assert isinstance(result["team_rolle"], dict), "team_rolle muss immer Dict sein"

    # ============================================================================
    # KRITISCHE REGEL 2: Provider-Auswahl muss korrekt funktionieren
    # ============================================================================
    
    def test_provider_selection_auto_mode(self):
        """KRITISCH: Auto-Modus muss Provider korrekt auswählen"""
        # Test: Auto-Modus sollte funktionieren (auch wenn APIs nicht verfügbar)
        # Das ist ein struktureller Test - die Logik muss vorhanden sein
        
        # Test mit verschiedenen Provider-Einstellungen
        valid_providers = ["auto", "openai", "claude"]
        
        for provider in valid_providers:
            # Test: Provider-Parameter wird korrekt verarbeitet
            result = massage_to_schema({}, provider)
            
            # Team-Rolle muss Provider korrekt reflektieren
            if provider == "openai":
                assert result["team_rolle"]["openai"] is True
            elif provider == "claude":
                assert result["team_rolle"]["claude"] is True
            # Auto wird durch tatsächliche Provider-Auswahl bestimmt
    
    def test_provider_team_role_consistency(self):
        """KRITISCH: Team-Rolle muss mit Provider konsistent sein"""
        test_cases = [
            ("openai", True, False),
            ("claude", False, True)
        ]
        
        for provider, expected_openai, expected_claude in test_cases:
            result = massage_to_schema({}, provider)
            
            assert result["team_rolle"]["openai"] == expected_openai, \
                f"OpenAI-Rolle falsch für Provider {provider}"
            assert result["team_rolle"]["claude"] == expected_claude, \
                f"Claude-Rolle falsch für Provider {provider}"

    # ============================================================================
    # KRITISCHE REGEL 3: Fallback muss IMMER funktionieren
    # ============================================================================
    
    def test_fallback_always_works(self):
        """KRITISCH: Fallback muss bei JEDEM Fehler funktionieren"""
        # Test: Auch bei komplett kaputten Eingaben muss Fallback funktionieren
        
        broken_inputs = [
            None,
            "",
            "Kein JSON",
            {"unbekanntes_feld": "wert"},
            {"kernbefunde": {"falscher_typ": "dict"}},
            {"cashflow_radar": ["falscher_typ", "liste"]},
            {"team_rolle": ["falscher_typ", "liste"]}
        ]
        
        for broken_input in broken_inputs:
            # Fallback muss IMMER funktionieren
            result = normalize_result(str(broken_input), "openai")
            
            # Alle Pflichtfelder müssen vorhanden sein
            required_fields = ["kurz_zusammenfassung", "kernbefunde", "action_plan",
                              "risiken", "cashflow_radar", "team_rolle"]
            
            for field in required_fields:
                assert field in result, f"Fallback fehlt Feld '{field}' für Input: {broken_input}"
            
            # Typen müssen korrekt sein
            assert isinstance(result["kernbefunde"], list)
            assert isinstance(result["action_plan"], list)
            assert isinstance(result["risiken"], list)
            assert isinstance(result["cashflow_radar"], dict)
            assert isinstance(result["team_rolle"], dict)
    
    def test_fallback_provider_tracking(self):
        """KRITISCH: Fallback muss Provider korrekt tracken"""
        for provider in ["openai", "claude"]:
            fallback = normalize_result("Test", provider)
            
            assert fallback["team_rolle"]["provider"] == provider or \
                   (fallback["team_rolle"]["openai"] if provider == "openai" else fallback["team_rolle"]["claude"])

    # ============================================================================
    # KRITISCHE REGEL 4: JSON-Parsing muss robust sein
    # ============================================================================
    
    def test_json_parsing_robustness(self):
        """KRITISCH: JSON-Parsing muss alle Edge-Cases behandeln"""
        test_cases = [
            # Gültiges JSON
            ('{"test": "value"}', {"test": "value"}),
            
            # JSON in Codeblock
            ('```json\n{"test": "value"}\n```', {"test": "value"}),
            
            # Einfache Anführungszeichen
            ("{'test': 'value'}", {"test": "value"}),
            
            # Leere Strings
            ("", None),
            ("   ", None),
            
            # Ungültiges JSON
            ("Das ist kein JSON", None),
            ("{unclosed", None),
            
            # Gemischte Anführungszeichen
            ('{"test": \'value\'}', {"test": "value"}),
        ]
        
        for input_json, expected in test_cases:
            result = try_parse_json(input_json)
            
            if expected is None:
                assert result is None, f"Ungültiges JSON sollte None zurückgeben: {input_json}"
            else:
                assert result == expected, f"JSON-Parsing fehlgeschlagen für: {input_json}"

    # ============================================================================
    # KRITISCHE REGEL 5: Performance-Grenzen einhalten
    # ============================================================================
    
    def test_performance_critical_paths(self):
        """KRITISCH: Kritische Pfade müssen performant sein"""
        # Test: JSON-Parsing Performance
        large_json = json.dumps({
            "kurz_zusammenfassung": "Test " * 1000,
            "kernbefunde": [f"Item {i}" for i in range(100)],
            "action_plan": [f"Plan {i}" for i in range(50)]
        })
        
        start_time = time.time()
        result = try_parse_json(large_json)
        parsing_time = time.time() - start_time
        
        assert parsing_time < 0.1, f"JSON-Parsing zu langsam: {parsing_time:.3f}s"
        assert result is not None
        
        # Test: Schema-Massage Performance
        large_data = {
            "kurz_zusammenfassung": "Test " * 1000,
            "kernbefunde": [f"Item {i}" for i in range(100)],
            "action_plan": [f"Plan {i}" for i in range(50)]
        }
        
        start_time = time.time()
        result = massage_to_schema(large_data, "openai")
        massage_time = time.time() - start_time
        
        assert massage_time < 0.1, f"Schema-Massage zu langsam: {massage_time:.3f}s"

    # ============================================================================
    # KRITISCHE REGEL 6: Error-Handling muss vollständig sein
    # ============================================================================
    
    def test_error_handling_completeness(self):
        """KRITISCH: Error-Handling muss alle Fehlerarten abdecken"""
        # Test: Alle Funktionen müssen auch bei Fehlern nicht crashen
        
        error_cases = [
            # massage_to_schema Error-Cases
            (lambda: massage_to_schema(None, "openai"), dict),
            (lambda: massage_to_schema("string", "openai"), dict),
            (lambda: massage_to_schema([], "openai"), dict),
            
            # try_parse_json Error-Cases  
            (lambda: try_parse_json(None), type(None)),
            (lambda: try_parse_json(123), type(None)),
            (lambda: try_parse_json({}), type(None)),
            
            # normalize_result Error-Cases
            (lambda: normalize_result(None, "openai"), dict),
            (lambda: normalize_result(123, "openai"), dict),
        ]
        
        for error_func, expected_type in error_cases:
            try:
                result = error_func()
                
                # Funktion sollte nicht crashen
                assert result is not None or expected_type == type(None)
                
                if expected_type != type(None):
                    assert isinstance(result, expected_type)
                    
            except Exception as e:
                pytest.fail(f"Error-Handling fehlgeschlagen: {e}")

    # ============================================================================
    # KRITISCHE REGEL 7: Metadaten müssen korrekt sein
    # ============================================================================
    
    def test_metadata_accuracy(self):
        """KRITISCH: Metadaten müssen immer korrekt sein"""
        # Test: Provider-Metadaten
        for provider in ["openai", "claude"]:
            result = massage_to_schema({}, provider)
            
            assert "meta" in result, "Meta-Informationen fehlen"
            assert result["meta"]["provider"] == provider, f"Provider-Metadaten falsch: {provider}"
        
        # Test: Raw-Text-Preservation
        test_text = "Original-Text für Test"
        result = massage_to_schema({"raw_text": test_text}, "openai")
        
        assert result["raw_text"] == test_text, "Raw-Text wurde nicht korrekt gespeichert"


class TestRico4BusinessRules:
    """Tests für geschäftskritische Rico4-Regeln"""
    
    def test_business_logic_consistency(self):
        """KRITISCH: Geschäftslogik muss konsistent sein"""
        # Test: Cashflow-Radar muss immer ein Dict mit "idee" sein
        test_cases = [
            {"cashflow_radar": "String"},
            {"cashflow_radar": {"idee": "Test"}},
            {"cashflow_radar": {"andere_key": "Wert"}},
            {"cashflow_radar": None},
        ]
        
        for test_case in test_cases:
            result = massage_to_schema(test_case, "openai")
            
            # Cashflow-Radar muss IMMER ein Dict mit "idee" sein
            assert isinstance(result["cashflow_radar"], dict)
            assert "idee" in result["cashflow_radar"]
    
    def test_list_handling_business_logic(self):
        """KRITISCH: Listen-Handling muss geschäftslogisch korrekt sein"""
        # Test: Verschiedene Listen-Formate müssen korrekt verarbeitet werden
        
        list_test_cases = [
            # Normale Listen
            ["Item 1", "Item 2"],
            
            # String mit Zeilenumbrüchen
            "Item 1\nItem 2\n- Item 3",
            
            # Leere Listen
            [],
            
            # None
            None,
        ]
        
        for test_list in list_test_cases:
            result = _coerce_list(test_list)
            
            # Ergebnis muss IMMER eine Liste sein
            assert isinstance(result, list), f"Liste-Handling fehlgeschlagen für: {test_list}"


def run_critical_rules_tests():
    """Führt alle kritischen Rico4-Regel-Tests aus"""
    print("🚨 Rico4 Kritische Regeln Tests")
    print("=" * 50)
    
    test_categories = [
        ("Schema-Compliance", TestRico4CriticalRules.test_schema_compliance_mandatory),
        ("Provider-Auswahl", TestRico4CriticalRules.test_provider_selection_auto_mode),
        ("Fallback-Mechanismus", TestRico4CriticalRules.test_fallback_always_works),
        ("JSON-Parsing-Robustheit", TestRico4CriticalRules.test_json_parsing_robustness),
        ("Performance-Grenzen", TestRico4CriticalRules.test_performance_critical_paths),
        ("Error-Handling", TestRico4CriticalRules.test_error_handling_completeness),
        ("Metadaten-Genauigkeit", TestRico4CriticalRules.test_metadata_accuracy),
        ("Geschäftslogik", TestRico4BusinessRules.test_business_logic_consistency)
    ]
    
    passed = 0
    failed = 0
    
    for category, test_func in test_categories:
        try:
            test_instance = TestRico4CriticalRules()
            test_instance.setup_method()
            test_func(test_instance)
            print(f"✅ {category}")
            passed += 1
        except Exception as e:
            print(f"❌ {category}: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"KRITISCHE TESTS: {passed} bestanden, {failed} fehlgeschlagen")
    
    if failed == 0:
        print("🎉 ALLE KRITISCHEN REGELN BESTANDEN!")
        print("Rico4 ist bereit für den Produktionseinsatz.")
    else:
        print("⚠️  KRITISCHE REGELN FEHLGESCHLAGEN!")
        print("Rico4 sollte NICHT produktiv eingesetzt werden.")
    
    return failed == 0


if __name__ == "__main__":
    success = run_critical_rules_tests()
    exit(0 if success else 1)
