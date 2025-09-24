"""
Rico 4.0 - Export Utility
Automatischer Export von Autopilot-Task-Ergebnissen als JSON/CSV
"""

from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import json
import csv
import re
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


def ensure_dir(p: Path) -> None:
    """Erstellt Verzeichnis falls es nicht existiert"""
    try:
        p.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Verzeichnisses {p}: {e}")
        raise


def is_tabular(payload: Any) -> bool:
    """
    True wenn payload eine Liste von Dicts mit identischen Keys ist.
    Prüft ob die Daten für CSV-Export geeignet sind.
    """
    if not isinstance(payload, list) or not payload:
        return False
    
    # Alle Elemente müssen Dicts sein
    if not all(isinstance(item, dict) for item in payload):
        return False
    
    # Alle Dicts müssen die gleichen Keys haben
    if len(payload) < 2:
        return True  # Einzelnes Element ist auch tabellarisch
    
    first_keys = set(payload[0].keys())
    return all(set(item.keys()) == first_keys for item in payload)


def sanitize_filename(s: str) -> str:
    """
    Nur [a-zA-Z0-9._-] erlauben, sonst '_' ersetzen.
    Macht Dateinamen sicher für das Dateisystem.
    """
    # Erlaubte Zeichen: Buchstaben, Zahlen, Punkte, Unterstriche, Bindestriche
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', s)
    # Mehrfache Unterstriche zu einem reduzieren
    sanitized = re.sub(r'_+', '_', sanitized)
    # Führende/Nachfolgende Unterstriche entfernen
    sanitized = sanitized.strip('_')
    return sanitized or 'export'


def timestamp() -> str:
    """Erstellt UTC-Zeitstempel im Format YYYYMMDD-HHMMSS"""
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def write_json(base: Path, task_id: str, payload: Any) -> Path:
    """Schreibt JSON-Export-Datei"""
    try:
        timestamp_str = timestamp()
        filename = f"{sanitize_filename(task_id)}__{timestamp_str}.json"
        filepath = base / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        
        logger.info(f"JSON-Export erstellt: {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"Fehler beim JSON-Export für {task_id}: {e}")
        raise


def write_csv(base: Path, task_id: str, payload: List[Dict[str, Any]]) -> Path:
    """Schreibt CSV-Export-Datei"""
    try:
        if not payload:
            raise ValueError("Leere Liste für CSV-Export")
        
        timestamp_str = timestamp()
        filename = f"{sanitize_filename(task_id)}__{timestamp_str}.csv"
        filepath = base / filename
        
        # Alle Keys aus allen Dicts sammeln
        all_keys = set()
        for item in payload:
            all_keys.update(item.keys())
        all_keys = sorted(list(all_keys))
        
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=all_keys)
            writer.writeheader()
            
            for item in payload:
                # Fehlende Keys mit leeren Strings füllen
                row = {key: item.get(key, '') for key in all_keys}
                writer.writerow(row)
        
        logger.info(f"CSV-Export erstellt: {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"Fehler beim CSV-Export für {task_id}: {e}")
        raise


def export_result(base_dir: Path, task_id: str, payload: Any, want_csv: bool) -> Dict[str, Any]:
    """
    Schreibt JSON, ggf. CSV. Gibt Metadaten zurück:
    { "task_id":..., "json": "relative/pfad.json", "csv": "relative/pfad.csv" | None,
      "size_json":..., "size_csv":..., "created_at": ... }
    """
    try:
        # Verzeichnis sicherstellen
        ensure_dir(base_dir)
        
        # JSON immer schreiben
        json_path = write_json(base_dir, task_id, payload)
        json_size = json_path.stat().st_size
        
        result = {
            "task_id": task_id,
            "json": str(json_path.relative_to(base_dir)),
            "csv": None,
            "size_json": json_size,
            "size_csv": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # CSV nur wenn gewünscht und Daten tabellarisch sind
        if want_csv and is_tabular(payload):
            try:
                csv_path = write_csv(base_dir, task_id, payload)
                csv_size = csv_path.stat().st_size
                result["csv"] = str(csv_path.relative_to(base_dir))
                result["size_csv"] = csv_size
            except Exception as e:
                logger.warning(f"CSV-Export für {task_id} fehlgeschlagen: {e}")
                # JSON-Export war erfolgreich, CSV-Fehler nicht fatal
        
        return result
        
    except Exception as e:
        logger.error(f"Export für {task_id} fehlgeschlagen: {e}")
        raise


def cleanup_old_exports(base_dir: Path, keep_days: int) -> Dict[str, Any]:
    """
    Löscht Export-Dateien älter als keep_days.
    Gibt Statistiken über gelöschte Dateien zurück.
    """
    try:
        if not base_dir.exists():
            return {"deleted_files": 0, "freed_bytes": 0}
        
        cutoff_time = datetime.now(timezone.utc).timestamp() - (keep_days * 24 * 3600)
        deleted_files = 0
        freed_bytes = 0
        
        for file_path in base_dir.iterdir():
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                try:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    deleted_files += 1
                    freed_bytes += file_size
                    logger.info(f"Alte Export-Datei gelöscht: {file_path}")
                except Exception as e:
                    logger.warning(f"Fehler beim Löschen von {file_path}: {e}")
        
        return {
            "deleted_files": deleted_files,
            "freed_bytes": freed_bytes,
            "keep_days": keep_days
        }
        
    except Exception as e:
        logger.error(f"Fehler beim Cleanup der Export-Dateien: {e}")
        return {"deleted_files": 0, "freed_bytes": 0, "error": str(e)}
