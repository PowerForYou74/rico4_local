#!/usr/bin/env python3
"""
Rico System V5 - Auto-Load-Routine für KI-Prompts
Lädt automatisch alle relevanten Prompt-Dateien beim Start des Rico-Systems.
"""

import json
import os
import sys
from pathlib import Path

# Konfiguration
REGISTRY_FILE = 'docs/prompt_registry.json'
PROJECT_ROOT = Path(__file__).parent

def load_prompt_registry():
    """Lädt die Prompt-Registry aus der JSON-Datei."""
    try:
        registry_path = PROJECT_ROOT / REGISTRY_FILE
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        return registry
    except FileNotFoundError:
        print(f"❌ Registry-Datei nicht gefunden: {REGISTRY_FILE}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Fehler beim Parsen der Registry: {e}")
        sys.exit(1)

def load_prompt_file(file_path):
    """Lädt eine einzelne Prompt-Datei und gibt den Inhalt zurück."""
    try:
        full_path = PROJECT_ROOT / file_path
        if not full_path.exists():
            print(f"⚠️  Datei nicht gefunden: {file_path}")
            return None
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content
    except Exception as e:
        print(f"❌ Fehler beim Laden von {file_path}: {e}")
        return None

def load_all_prompts():
    """Lädt alle Prompts gemäß Registry und gibt Bestätigung aus."""
    print("🚀 Rico System V5 - Auto-Load-Routine gestartet")
    print("=" * 50)
    
    # Registry laden
    registry = load_prompt_registry()
    
    # Metadaten anzeigen
    if 'metadata' in registry:
        meta = registry['metadata']
        print(f"📋 Version: {meta.get('version', 'Unknown')}")
        print(f"📅 Letzte Aktualisierung: {meta.get('last_updated', 'Unknown')}")
        print(f"🎨 Theme: {meta.get('theme', {}).get('primary_color', 'Unknown')}")
        print()
    
    # Prompts laden
    loaded_prompts = {}
    success_count = 0
    
    # Master-Prompt laden
    if 'master' in registry:
        master_file = registry['master']
        content = load_prompt_file(master_file)
        if content:
            loaded_prompts['master'] = content
            print(f"✅ Master-Prompt geladen: {Path(master_file).name}")
            success_count += 1
        else:
            print(f"❌ Master-Prompt konnte nicht geladen werden: {master_file}")
    
    # KI-spezifische Prompts laden
    ki_prompts = ['claude', 'perplexity', 'cursor']
    for ki in ki_prompts:
        if ki in registry:
            prompt_file = registry[ki]
            content = load_prompt_file(prompt_file)
            if content:
                loaded_prompts[ki] = content
                print(f"✅ {ki.capitalize()}-Einstiegsprompt geladen")
                success_count += 1
            else:
                print(f"❌ {ki.capitalize()}-Einstiegsprompt konnte nicht geladen werden: {prompt_file}")
    
    print()
    # Nur die tatsächlichen Prompt-Dateien zählen (ohne metadata)
    prompt_files = [k for k in registry.keys() if k != 'metadata']
    expected_count = len(prompt_files)
    
    print("=" * 50)
    print(f"📊 Zusammenfassung: {success_count}/{expected_count} Prompts erfolgreich geladen")
    
    if success_count == expected_count:
        print("🎉 Alle Prompts erfolgreich geladen - Rico System V5 bereit!")
        return loaded_prompts
    else:
        print("⚠️  Einige Prompts konnten nicht geladen werden")
        return loaded_prompts

def get_prompt_for_ki(ki_name):
    """Gibt den Prompt für eine spezifische KI zurück."""
    registry = load_prompt_registry()
    
    if ki_name in registry:
        content = load_prompt_file(registry[ki_name])
        if content:
            return content
        else:
            print(f"❌ Prompt für {ki_name} konnte nicht geladen werden")
            return None
    else:
        print(f"❌ Kein Prompt für {ki_name} in der Registry gefunden")
        return None

def main():
    """Hauptfunktion - lädt alle Prompts beim Start."""
    try:
        prompts = load_all_prompts()
        
        # Prompts in Session-Variablen speichern (für weitere Verwendung)
        if prompts:
            # Hier könnten die Prompts in globale Variablen oder eine Session gespeichert werden
            print("\n💾 Prompts sind für die Session verfügbar")
        
        return prompts
        
    except Exception as e:
        print(f"💥 Kritischer Fehler beim Laden der Prompts: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
