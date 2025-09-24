"""
Rico 4.0 - Result Store Helper
Leichtgewichtige Persistenz für Task-Ergebnisse
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


def write_result(task_id: str, payload: dict) -> str:
    """
    Schreibt ein Task-Ergebnis in das Result-Format
    
    Args:
        task_id: Eindeutige Task-ID
        payload: Task-Ergebnis-Daten
        
    Returns:
        Pfad zur gespeicherten Datei
    """
    try:
        # Erstelle Task-spezifischen Ordner
        results_dir = Path("data/results") / task_id
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # UTC-Zeitstempel für Dateiname
        now = datetime.now(timezone.utc)
        timestamp_str = now.strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp_str}.json"
        filepath = results_dir / filename
        
        # Normalisiere das Payload in das Standard-Schema
        result_data = {
            "ts": now.isoformat().replace("+00:00", "Z"),
            "ok": payload.get("success", False),
            "status": "success" if payload.get("success", False) else "error",
            "duration_sec": payload.get("duration_sec"),
            "provider": payload.get("provider"),
            "prompt_type": payload.get("task_type"),
            "notes": payload.get("notes"),
            "error": payload.get("error")
        }
        
        # Schreibe JSON-Datei
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)
            
        return str(filepath)
        
    except Exception as e:
        # Logge Fehler, aber wirf keine Exception um Autopilot nicht zu stören
        print(f"Fehler beim Speichern von Result für {task_id}: {e}")
        return ""


def read_latest(task_id: str) -> Optional[dict]:
    """
    Liest das neueste Ergebnis für einen Task
    
    Args:
        task_id: Task-ID
        
    Returns:
        Neuestes Result-Dict oder None
    """
    try:
        results_dir = Path("data/results") / task_id
        if not results_dir.exists():
            return None
            
        # Finde neueste Datei
        json_files = list(results_dir.glob("*.json"))
        if not json_files:
            return None
            
        latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    except Exception as e:
        print(f"Fehler beim Lesen von latest Result für {task_id}: {e}")
        return None


def read_many(task_id: str, limit: int = 50) -> List[dict]:
    """
    Liest mehrere Ergebnisse für einen Task (neueste zuerst)
    
    Args:
        task_id: Task-ID
        limit: Maximale Anzahl Ergebnisse
        
    Returns:
        Liste von Result-Dicts
    """
    try:
        results_dir = Path("data/results") / task_id
        if not results_dir.exists():
            return []
            
        # Finde alle JSON-Dateien und sortiere nach Modifikationszeit
        json_files = list(results_dir.glob("*.json"))
        json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        results = []
        for filepath in json_files[:limit]:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                    results.append(result)
            except Exception as e:
                print(f"Fehler beim Lesen von {filepath}: {e}")
                continue
                
        return results
        
    except Exception as e:
        print(f"Fehler beim Lesen von Results für {task_id}: {e}")
        return []
