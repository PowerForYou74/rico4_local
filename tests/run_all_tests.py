#!/usr/bin/env python3
"""
Rico4 Komplette Test-Suite
=========================

Führt alle Rico4-Tests aus und gibt einen umfassenden Bericht zurück.
"""

import sys
import os
import time
from typing import List, Tuple

# Projekt-Pfad hinzufügen
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Test-Module importieren
from test_rico4_rules import run_rico4_rule_tests
from test_rico4_integration import run_integration_tests

# Autopilot-Tests importieren
import pytest
import subprocess
import sys


def run_all_rico4_tests() -> Tuple[bool, dict]:
    """
    Führt alle Rico4-Tests aus und gibt Ergebnisse zurück.
    
    Returns:
        Tuple[bool, dict]: (alle_tests_bestanden, detaillierte_ergebnisse)
    """
    print("🚀 Rico4 Komplette Test-Suite")
    print("=" * 60)
    print()
    
    start_time = time.time()
    results = {}
    
    # 1. Regel-Tests
    print("📋 Phase 1: Rico4-Regeln Tests")
    print("-" * 40)
    try:
        rules_success = run_rico4_rule_tests()
        results["regel_tests"] = {"success": rules_success, "error": None}
    except Exception as e:
        results["regel_tests"] = {"success": False, "error": str(e)}
        print(f"❌ Fehler bei Regel-Tests: {e}")
    
    print()
    
    # 2. Integration-Tests
    print("🔗 Phase 2: Integration Tests")
    print("-" * 40)
    try:
        integration_success = run_integration_tests()
        results["integration_tests"] = {"success": integration_success, "error": None}
    except Exception as e:
        results["integration_tests"] = {"success": False, "error": str(e)}
        print(f"❌ Fehler bei Integration-Tests: {e}")
    
    print()
    
    # 3. Autopilot-Tests
    print("🤖 Phase 3: Autopilot Tests")
    print("-" * 40)
    try:
        autopilot_success = run_autopilot_tests()
        results["autopilot_tests"] = {"success": autopilot_success, "error": None}
    except Exception as e:
        results["autopilot_tests"] = {"success": False, "error": str(e)}
        print(f"❌ Fehler bei Autopilot-Tests: {e}")
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Gesamtergebnis berechnen
    all_passed = all(result["success"] for result in results.values())
    
    # Zusammenfassung
    print("\n" + "=" * 60)
    print("📊 ZUSAMMENFASSUNG")
    print("=" * 60)
    
    for test_category, result in results.items():
        status = "✅ BESTANDEN" if result["success"] else "❌ FEHLGESCHLAGEN"
        print(f"{test_category.replace('_', ' ').title():<25} {status}")
        
        if result["error"]:
            print(f"{'':25} Fehler: {result['error']}")
    
    print(f"\n⏱️  Gesamtdauer: {duration:.2f} Sekunden")
    
    if all_passed:
        print("\n🎉 ALLE TESTS BESTANDEN!")
        print("Rico4 ist vollständig funktionsfähig und alle Regeln sind korrekt implementiert.")
    else:
        print("\n⚠️  EINIGE TESTS FEHLGESCHLAGEN!")
        print("Bitte überprüfen Sie die fehlgeschlagenen Tests und beheben Sie die Probleme.")
    
    return all_passed, results


def run_autopilot_tests() -> bool:
    """
    Führt alle Autopilot-Tests aus.
    
    Returns:
        bool: True wenn alle Tests bestanden, False sonst
    """
    test_files = [
        "test_autopilot_manager.py",
        "test_autopilot_api.py", 
        "test_autopilot_integration.py"
    ]
    
    tests_dir = os.path.dirname(__file__)
    all_passed = True
    
    for test_file in test_files:
        test_path = os.path.join(tests_dir, test_file)
        if not os.path.exists(test_path):
            print(f"⚠️  Test-Datei nicht gefunden: {test_file}")
            continue
            
        print(f"🧪 Führe {test_file} aus...")
        
        try:
            # pytest mit subprocess ausführen
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                test_path, "-v", "--tb=short"
            ], 
            cwd=os.path.dirname(__file__),
            capture_output=True, 
            text=True, 
            timeout=60
            )
            
            if result.returncode == 0:
                print(f"✅ {test_file}: BESTANDEN")
            else:
                print(f"❌ {test_file}: FEHLGESCHLAGEN")
                print(f"   Ausgabe: {result.stdout}")
                if result.stderr:
                    print(f"   Fehler: {result.stderr}")
                all_passed = False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_file}: TIMEOUT")
            all_passed = False
        except Exception as e:
            print(f"❌ {test_file}: FEHLER - {e}")
            all_passed = False
    
    if all_passed:
        print("🎉 Alle Autopilot-Tests bestanden!")
    else:
        print("⚠️  Einige Autopilot-Tests fehlgeschlagen!")
    
    return all_passed


def generate_test_report(results: dict, duration: float) -> str:
    """Generiert einen detaillierten Test-Bericht"""
    report = []
    report.append("# Rico4 Test-Bericht")
    report.append(f"**Datum:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"**Dauer:** {duration:.2f} Sekunden")
    report.append("")
    
    report.append("## Test-Kategorien")
    report.append("")
    
    for category, result in results.items():
        status = "✅ BESTANDEN" if result["success"] else "❌ FEHLGESCHLAGEN"
        report.append(f"### {category.replace('_', ' ').title()}")
        report.append(f"- **Status:** {status}")
        
        if result["error"]:
            report.append(f"- **Fehler:** {result['error']}")
        
        report.append("")
    
    report.append("## Empfehlungen")
    report.append("")
    
    if all(result["success"] for result in results.values()):
        report.append("- ✅ Alle Tests bestanden - Rico4 ist bereit für den Produktionseinsatz")
        report.append("- 🔄 Regelmäßige Tests durchführen um Qualität zu gewährleisten")
    else:
        report.append("- 🔧 Fehlgeschlagene Tests beheben bevor Rico4 produktiv eingesetzt wird")
        report.append("- 📝 Fehlerprotokolle überprüfen und entsprechende Maßnahmen einleiten")
    
    return "\n".join(report)


def main():
    """Hauptfunktion für die Test-Suite"""
    try:
        success, results = run_all_rico4_tests()
        
        # Test-Bericht generieren
        duration = sum(1 for _ in range(100))  # Placeholder für echte Dauer
        report = generate_test_report(results, duration)
        
        # Bericht in Datei speichern
        report_file = os.path.join(os.path.dirname(__file__), "test_report.md")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"\n📄 Detaillierter Bericht gespeichert: {report_file}")
        
        # Exit-Code setzen
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests durch Benutzer abgebrochen")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unerwarteter Fehler: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
