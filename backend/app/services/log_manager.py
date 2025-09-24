"""
Rico 4.0 - Log Manager
Automatische Log-Rotation und Cleanup
"""

import os
import glob
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)


class LogManager:
    """Manager für Log-Rotation und Cleanup"""
    
    def __init__(self, log_dir: str = "logs", results_dir: str = "data/autopilot/results"):
        self.log_dir = Path(log_dir)
        self.results_dir = Path(results_dir)
        self.max_log_files = 10  # Maximale Anzahl Log-Dateien
        self.max_results_days = 30  # Ergebnisse älter als 30 Tage löschen
        
    def cleanup_old_logs(self) -> Dict[str, int]:
        """Bereinigt alte Log-Dateien"""
        cleaned = {
            "logs_removed": 0,
            "results_removed": 0,
            "space_freed_mb": 0
        }
        
        try:
            # Log-Dateien bereinigen
            log_files = list(self.log_dir.glob("*.log*"))
            if len(log_files) > self.max_log_files:
                # Nach Änderungsdatum sortieren
                log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                # Älteste Dateien löschen
                for old_file in log_files[self.max_log_files:]:
                    try:
                        size_mb = old_file.stat().st_size / (1024 * 1024)
                        old_file.unlink()
                        cleaned["logs_removed"] += 1
                        cleaned["space_freed_mb"] += size_mb
                        logger.info(f"Alte Log-Datei gelöscht: {old_file}")
                    except Exception as e:
                        logger.warning(f"Fehler beim Löschen von {old_file}: {e}")
            
            # Alte Results bereinigen
            cutoff_date = datetime.now() - timedelta(days=self.max_results_days)
            result_files = list(self.results_dir.glob("*.json"))
            
            for result_file in result_files:
                try:
                    file_time = datetime.fromtimestamp(result_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        size_mb = result_file.stat().st_size / (1024 * 1024)
                        result_file.unlink()
                        cleaned["results_removed"] += 1
                        cleaned["space_freed_mb"] += size_mb
                        logger.info(f"Altes Result gelöscht: {result_file}")
                except Exception as e:
                    logger.warning(f"Fehler beim Löschen von {result_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Fehler beim Log-Cleanup: {e}")
            
        return cleaned
    
    def get_log_stats(self) -> Dict[str, any]:
        """Gibt Log-Statistiken zurück"""
        try:
            log_files = list(self.log_dir.glob("*.log*"))
            result_files = list(self.results_dir.glob("*.json"))
            
            total_log_size = sum(f.stat().st_size for f in log_files) / (1024 * 1024)
            total_result_size = sum(f.stat().st_size for f in result_files) / (1024 * 1024)
            
            return {
                "log_files_count": len(log_files),
                "result_files_count": len(result_files),
                "total_log_size_mb": round(total_log_size, 2),
                "total_result_size_mb": round(total_result_size, 2),
                "total_size_mb": round(total_log_size + total_result_size, 2)
            }
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Log-Statistiken: {e}")
            return {}


# Globale Instanz
log_manager = LogManager()
