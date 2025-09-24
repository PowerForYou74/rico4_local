"""
Rico 4.0 - Autopilot Task Monitor
Überwacht Task-Status und erstellt Dashboard-Status
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import glob

logger = logging.getLogger(__name__)


class TaskMonitor:
    """Monitor für Autopilot-Tasks"""
    
    def __init__(self, results_dir: str = "data/autopilot/results"):
        self.results_dir = Path(results_dir)
        self.summary_dir = self.results_dir / "log_watcher"
        self.summary_dir.mkdir(parents=True, exist_ok=True)
        
    def collect_task_status(self, tasks: List[str]) -> Dict:
        """
        Sammelt Status-Informationen für eine Liste von Tasks
        
        Args:
            tasks: Liste von Task-IDs zum Überwachen
            
        Returns:
            Dict mit Status-Informationen
        """
        logger.info(f"Sammele Status für {len(tasks)} Tasks: {tasks}")
        
        task_details = {}
        counts = {"ok": 0, "failed": 0, "stale": 0}
        
        for task_id in tasks:
            try:
                status_info = self._get_task_status(task_id)
                task_details[task_id] = status_info
                
                # Zähle Status
                if status_info["stale"]:
                    counts["stale"] += 1
                elif status_info["ok"]:
                    counts["ok"] += 1
                else:
                    counts["failed"] += 1
                    
            except Exception as e:
                logger.error(f"Fehler beim Sammeln des Status für Task {task_id}: {e}")
                task_details[task_id] = {
                    "ok": False,
                    "error": f"Monitor-Fehler: {str(e)}",
                    "ts": None,
                    "stale": False
                }
                counts["failed"] += 1
        
        # Erstelle Summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "counts": counts,
            "details": task_details,
            "total_tasks": len(tasks),
            "monitored_tasks": tasks
        }
        
        # Speichere Summary
        self._save_summary(summary)
        
        logger.info(f"Status gesammelt: {counts}")
        return summary
    
    def _get_task_status(self, task_id: str) -> Dict:
        """
        Ermittelt den Status eines einzelnen Tasks
        
        Args:
            task_id: ID des Tasks
            
        Returns:
            Dict mit Status-Informationen
        """
        # Suche neueste Result-Datei für diesen Task
        pattern = str(self.results_dir / f"{task_id}_*.json")
        result_files = glob.glob(pattern)
        
        if not result_files:
            return {
                "ok": False,
                "error": "Keine Result-Datei gefunden",
                "ts": None,
                "stale": True
            }
        
        # Sortiere nach Zeitstempel (neueste zuerst)
        result_files.sort(key=lambda x: Path(x).stat().st_mtime, reverse=True)
        latest_file = result_files[0]
        
        try:
            # Lade neueste Result-Datei
            with open(latest_file, 'r', encoding='utf-8') as f:
                result_data = json.load(f)
            
            # Extrahiere Status-Informationen
            success = result_data.get("success", False)
            error = result_data.get("error")
            timestamp_str = result_data.get("timestamp")
            
            # Parse Zeitstempel
            ts = None
            if timestamp_str:
                try:
                    ts = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except:
                    # Fallback: Datei-Modifikationszeit
                    ts = datetime.fromtimestamp(Path(latest_file).stat().st_mtime)
            
            # Prüfe auf Stale (älter als 2x Cron-Intervall)
            stale = self._is_stale(ts, task_id)
            
            return {
                "ok": success and not stale,
                "error": error if not success else None,
                "ts": ts.isoformat() if ts else None,
                "stale": stale,
                "file": Path(latest_file).name
            }
            
        except Exception as e:
            logger.error(f"Fehler beim Lesen der Result-Datei {latest_file}: {e}")
            return {
                "ok": False,
                "error": f"Datei-Fehler: {str(e)}",
                "ts": None,
                "stale": True
            }
    
    def _is_stale(self, timestamp: Optional[datetime], task_id: str) -> bool:
        """
        Prüft ob ein Task stale ist (älter als 2x Cron-Intervall)
        
        Args:
            timestamp: Zeitstempel der letzten Ausführung
            task_id: ID des Tasks
            
        Returns:
            True wenn stale, False sonst
        """
        if not timestamp:
            return True
        
        # Fallback: 15 Minuten (3x5min) wenn Intervall nicht bekannt
        max_age_minutes = 15
        
        # Versuche Cron-Intervall zu ermitteln (vereinfacht)
        # Für häufige Patterns: */2 = 2min, */5 = 5min, 0 */1 = 60min, etc.
        if "*/2" in task_id or "test" in task_id.lower():
            max_age_minutes = 4  # 2x2min
        elif "*/5" in task_id or "log_watcher" in task_id:
            max_age_minutes = 10  # 2x5min
        elif "daily" in task_id.lower() or "evening" in task_id.lower():
            max_age_minutes = 60  # 2x30min für tägliche Tasks
        elif "weekly" in task_id.lower():
            max_age_minutes = 1440  # 2x12h für wöchentliche Tasks
        
        max_age = timedelta(minutes=max_age_minutes)
        return datetime.now() - timestamp > max_age
    
    def _save_summary(self, summary: Dict):
        """
        Speichert die Summary in eine JSON-Datei
        
        Args:
            summary: Summary-Daten
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"summary_{timestamp}.json"
            filepath = self.summary_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            # Speichere auch als "summary.json" (neueste Version)
            latest_filepath = self.summary_dir / "summary.json"
            with open(latest_filepath, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Summary gespeichert: {filepath}")
            
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Summary: {e}")
    
    def get_latest_summary(self) -> Optional[Dict]:
        """
        Lädt die neueste Summary
        
        Returns:
            Dict mit Summary-Daten oder None
        """
        try:
            summary_file = self.summary_dir / "summary.json"
            if summary_file.exists():
                with open(summary_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Fehler beim Laden der Summary: {e}")
        
        return None
