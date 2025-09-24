#!/usr/bin/env python3
"""
Anthropic API Test-Skript für Rico4
Testet die Verbindung zur Anthropic API und zeigt verfügbare Modelle an.
"""

import os
import requests
import sys
from typing import Dict, Any, List

# Konfiguration - bevorzuge CLAUDE_API_KEY, fallback zu ANTHROPIC_API_KEY
API_KEY = os.getenv("CLAUDE_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
if not API_KEY:
    print("❌ Bitte setze die Umgebungsvariable CLAUDE_API_KEY oder ANTHROPIC_API_KEY")
    sys.exit(1)

BASE_URL = "https://api.anthropic.com/v1"
HEADERS = {
    "x-api-key": API_KEY,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json"
}

def get_available_models() -> List[Dict[str, Any]]:
    """Holt verfügbare Modelle von der Anthropic API."""
    print("📡 Hole verfügbare Modelle...")
    models_resp = requests.get(f"{BASE_URL}/models", headers=HEADERS)

    if models_resp.status_code != 200:
        print(f"❌ Fehler beim Abruf der Modelle: {models_resp.status_code} {models_resp.text}")
        return []

    models = models_resp.json().get("data", [])
    print("✅ Modelle gefunden:")
    for m in models:
        print(" -", m.get("id"))
    
    return models

def test_model_completion(model_id: str, test_prompt: str = "Sag mir bitte einen kurzen Fakt über Pferde.") -> Dict[str, Any]:
    """Testet ein spezifisches Modell mit einem einfachen Prompt."""
    print(f"\n🎯 Teste Modell: {model_id}")
    
    payload = {
        "model": model_id,
        "max_tokens": 50,
        "messages": [
            {"role": "user", "content": test_prompt}
        ]
    }

    resp = requests.post(f"{BASE_URL}/messages", headers=HEADERS, json=payload)

    if resp.status_code == 200:
        print("✅ Erfolgreiche Antwort:")
        response_data = resp.json()
        print(response_data)
        return response_data
    else:
        print(f"❌ Fehler {resp.status_code}: {resp.text}")
        if resp.status_code == 401:
            print("👉 Hinweis: Prüfe CLAUDE_API_KEY oder ANTHROPIC_API_KEY, Workspace und Header (x-api-key, anthropic-version).")
        elif resp.status_code == 404:
            print("👉 Modell-ID nicht gültig – erneut /v1/models prüfen.")
        return {"error": f"HTTP {resp.status_code}: {resp.text}"}

def test_rico_integration() -> bool:
    """Testet die Integration mit dem bestehenden Rico4 LLM-Client."""
    print("\n🔗 Teste Rico4 Integration...")
    
    try:
        # Import des bestehenden LLM-Clients
        sys.path.append('/Users/ow-winkel/Projects/rico4_local/backend/app/services')
        from llm_clients import ask_claude
        
        # Test mit dem Rico4-Format
        test_input = "Was sind die wichtigsten Trends in der Künstlichen Intelligenz?"
        result = ask_claude(test_input)
        
        if result and not result.get("error"):
            print("✅ Rico4 Claude-Integration funktioniert:")
            print(f"   Zusammenfassung: {result.get('kurz_zusammenfassung', 'N/A')}")
            print(f"   Kern-Ergebnisse: {len(result.get('kernergebnisse', []))} Punkte")
            return True
        else:
            print(f"❌ Rico4 Integration fehlgeschlagen: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Fehler bei Rico4 Integration: {e}")
        return False

def main():
    """Hauptfunktion für den API-Test."""
    print("🚀 Anthropic API Test für Rico4")
    print("=" * 50)
    
    # 1. Verfügbare Modelle abrufen
    models = get_available_models()
    
    if not models:
        print("❌ Keine Modelle verfügbar – prüfe API-Key/Workspace!")
        sys.exit(1)
    
    # 2. Erstes Modell testen
    test_model = models[0]["id"]
    completion_result = test_model_completion(test_model)
    
    # 3. Rico4 Integration testen
    rico_success = test_rico_integration()
    
    # 4. Zusammenfassung
    print("\n" + "=" * 50)
    print("📊 Test-Zusammenfassung:")
    print(f"   ✅ Modelle abrufen: {'Erfolgreich' if models else 'Fehlgeschlagen'}")
    print(f"   ✅ Modell-Test: {'Erfolgreich' if not completion_result.get('error') else 'Fehlgeschlagen'}")
    print(f"   ✅ Rico4 Integration: {'Erfolgreich' if rico_success else 'Fehlgeschlagen'}")
    
    if models and not completion_result.get('error') and rico_success:
        print("\n🎉 Alle Tests erfolgreich! Anthropic API ist bereit für Rico4.")
        return 0
    else:
        print("\n⚠️  Einige Tests fehlgeschlagen. Prüfe die Konfiguration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
