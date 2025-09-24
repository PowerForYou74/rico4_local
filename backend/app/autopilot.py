"""
Rico 4.0 - Autopilot Manager
Vollautomatische Job-Ausführung basierend auf Cron-Schedules
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import yaml
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .services.orchestrator import RicoOrchestrator
from .monitor import TaskMonitor
from .services.result_store import write_result
from .utils.exporter import export_result, cleanup_old_exports

logger = logging.getLogger(__name__)


class AutopilotManager:
    """Manager für automatische Task-Ausführung"""
    
    def __init__(self, config_path: str = "data/autopilot/config.yaml"):
        self.config_path = Path(config_path)
        self.scheduler = AsyncIOScheduler()
        self.orchestrator = RicoOrchestrator()
        self.is_running = False
        self.tasks_config: List[Dict] = []
        self.export_config: Dict = {}
        self.results_dir = Path("data/autopilot/results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.monitor = TaskMonitor(str(self.results_dir))
        
    def load_config(self) -> bool:
        """Lädt die Autopilot-Konfiguration"""
        try:
            if not self.config_path.exists():
                logger.warning(f"Autopilot-Konfiguration nicht gefunden: {self.config_path}")
                return False
                
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            self.tasks_config = config.get('tasks', [])
            self.export_config = config.get('exports', {})
            
            # Export-Konfiguration mit Defaults
            if not self.export_config:
                self.export_config = {
                    'enabled': False,
                    'dir': 'data/exports',
                    'formats': ['json'],
                    'keep_days': 30
                }
            
            logger.info(f"Autopilot-Konfiguration geladen: {len(self.tasks_config)} Tasks, Export: {self.export_config.get('enabled', False)}")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Autopilot-Konfiguration: {e}")
            return False
    
    def start(self) -> bool:
        """Startet den Autopilot-Scheduler"""
        if self.is_running:
            logger.warning("Autopilot läuft bereits")
            return False
            
        if not self.load_config():
            return False
            
        # Scheduler starten
        self.scheduler.start()
        
        # Alle enabled Tasks planen
        scheduled_count = 0
        for task in self.tasks_config:
            if task.get('enabled', False):
                if self._schedule_task(task):
                    scheduled_count += 1
                    
        self.is_running = True
        logger.info(f"Autopilot gestartet: {scheduled_count} Tasks geplant")
        return True
    
    def stop(self) -> bool:
        """Stoppt den Autopilot-Scheduler"""
        if not self.is_running:
            logger.warning("Autopilot läuft nicht")
            return False
            
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("Autopilot gestoppt")
        return True
    
    def _schedule_task(self, task: Dict) -> bool:
        """Plant einen einzelnen Task"""
        try:
            task_id = task['id']
            schedule = task['schedule']
            
            # Cron-Syntax parsen und Job erstellen
            cron_parts = schedule.split()
            if len(cron_parts) != 5:
                logger.error(f"Ungültige Cron-Syntax für Task {task_id}: {schedule}")
                return False
                
            minute, hour, day, month, day_of_week = cron_parts
            
            # APScheduler Job erstellen
            self.scheduler.add_job(
                func=self._execute_task,
                trigger=CronTrigger(
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week
                ),
                args=[task],
                id=f"autopilot_{task_id}",
                name=f"Autopilot: {task.get('description', task_id)}",
                replace_existing=True
            )
            
            logger.info(f"Task geplant: {task_id} ({schedule})")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Planen von Task {task_id}: {e}")
            return False
    
    async def _execute_task(self, task: Dict):
        """Führt einen Task aus"""
        task_id = task['id']
        logger.info(f"Führe Autopilot-Task aus: {task_id}")
        
        start_time = datetime.now()
        result = None
        
        try:
            # Spezielle Behandlung für log_watcher Task
            if task_id == "log_watcher":
                result = await self._execute_log_watcher_task(task)
            else:
                # Standard Task-Ausführung
                result = await self.orchestrator.run_autopilot_task(task)
            
            # Berechne Dauer
            duration_sec = (datetime.now() - start_time).total_seconds()
            
            # Ergebnis in beiden Formaten speichern (bestehende + neue)
            self._save_result(task_id, result)
            
            # Neue Result Store Integration
            write_result(task_id, {
                'success': result.get('success', False),
                'duration_sec': duration_sec,
                'provider': result.get('provider', task.get('provider', 'auto')),
                'task_type': task.get('task_type', 'analysis'),
                'notes': result.get('result', {}).get('kurz_zusammenfassung', '') if isinstance(result.get('result'), dict) else None,
                'error': result.get('error')
            })
            
            # Export-Funktionalität
            export_files = self._handle_export(task_id, result)
            if export_files:
                result['export_files'] = export_files
            
            logger.info(f"Task {task_id} erfolgreich ausgeführt")
            
        except Exception as e:
            duration_sec = (datetime.now() - start_time).total_seconds()
            error_result = {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
            # Beide Speicher-Formate
            self._save_result(task_id, error_result)
            write_result(task_id, {
                'success': False,
                'duration_sec': duration_sec,
                'provider': task.get('provider', 'auto'),
                'task_type': task.get('task_type', 'analysis'),
                'error': str(e)
            })
            
            logger.error(f"Fehler bei Task-Ausführung {task_id}: {e}")
    
    async def _execute_log_watcher_task(self, task: Dict) -> Dict:
        """
        Spezielle Ausführung für log_watcher Task
        Sammelt Status aller überwachten Tasks
        """
        logger.info("Führe log_watcher Task aus")
        
        try:
            # Liste der zu überwachenden Tasks
            monitored_tasks = [
                "test_task",
                "daily_checkin", 
                "social_post",
                "weekly_analysis",
                "daily_briefing",
                "evening_check",
                "social_reels",
                "finance_focus",
                "praxis_tip"
            ]
            
            # Sammle Status aller Tasks
            status_summary = self.monitor.collect_task_status(monitored_tasks)
            
            # Erstelle strukturiertes Ergebnis im Rico-Format
            result = {
                "success": True,
                "task_id": "log_watcher",
                "task_type": "monitoring",
                "provider": "system",
                "timestamp": datetime.now().isoformat(),
                "result": {
                    "kurz_zusammenfassung": f"Task-Monitoring abgeschlossen: {status_summary['counts']['ok']} OK, {status_summary['counts']['failed']} Fehler, {status_summary['counts']['stale']} Stale",
                    "kernbefunde": [
                        f"✅ OK: {status_summary['counts']['ok']}",
                        f"❌ Fehler: {status_summary['counts']['failed']}",
                        f"⚠️ Stale: {status_summary['counts']['stale']}"
                    ],
                    "action_plan": self._generate_action_plan(status_summary),
                    "risiken": self._identify_risks(status_summary),
                    "cashflow_radar": {
                        "idee": "Automatisiertes Task-Monitoring für bessere Systemstabilität"
                    },
                    "team_rolle": {
                        "openai": False,
                        "claude": False,
                        "system": True
                    },
                    "aufgabenverteilung": [
                        "System-Monitoring durch Autopilot",
                        "Fehlerbehebung bei failed Tasks",
                        "Stale-Task Neustart"
                    ],
                    "orchestrator_log": f"TaskMonitor | {len(monitored_tasks)} Tasks | ✓ Status gesammelt",
                    "meta": {
                        "provider": "system",
                        "duration_s": 0.1,
                        "monitored_tasks": monitored_tasks,
                        "summary_file": "data/autopilot/results/log_watcher/summary.json"
                    },
                    "raw_text": "",
                    "task_details": status_summary["details"]
                },
                "error": None
            }
            
            logger.info(f"log_watcher Task erfolgreich: {status_summary['counts']}")
            return result
            
        except Exception as e:
            logger.error(f"Fehler bei log_watcher Task: {e}")
            return {
                "success": False,
                "task_id": "log_watcher",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_action_plan(self, status_summary: Dict) -> List[str]:
        """Generiert Action Plan basierend auf Task-Status"""
        actions = []
        counts = status_summary["counts"]
        
        if counts["failed"] > 0:
            actions.append("Fehlgeschlagene Tasks überprüfen und neu starten")
        
        if counts["stale"] > 0:
            actions.append("Stale Tasks identifizieren und Cron-Schedules prüfen")
        
        if counts["ok"] == status_summary["total_tasks"]:
            actions.append("Alle Tasks laufen optimal - System ist gesund")
        
        return actions
    
    def _identify_risks(self, status_summary: Dict) -> List[str]:
        """Identifiziert Risiken basierend auf Task-Status"""
        risks = []
        counts = status_summary["counts"]
        
        if counts["failed"] > 0:
            risks.append("Fehlgeschlagene Tasks können zu Datenverlust führen")
        
        if counts["stale"] > 0:
            risks.append("Stale Tasks deuten auf Scheduler-Probleme hin")
        
        if counts["failed"] + counts["stale"] > status_summary["total_tasks"] / 2:
            risks.append("Mehr als die Hälfte der Tasks hat Probleme - System-Überprüfung erforderlich")
        
        return risks
    
    def _handle_export(self, task_id: str, result: Dict) -> Optional[Dict]:
        """Behandelt Export von Task-Ergebnissen"""
        try:
            # Prüfe ob Export aktiviert ist
            if not self.export_config.get('enabled', False):
                return None
            
            # Export-Verzeichnis aus Konfiguration
            export_dir = self.export_config.get('dir', 'data/exports')
            # ENV-Variable überschreibt falls gesetzt
            export_dir = os.getenv('EXPORTS_DIR', export_dir)
            base_dir = Path(export_dir)
            
            # CSV-Export gewünscht?
            want_csv = 'csv' in self.export_config.get('formats', ['json'])
            
            # Export-Payload: das normalisierte Ergebnis
            payload = result.get('result', result)
            
            # Export durchführen
            export_meta = export_result(base_dir, task_id, payload, want_csv)
            
            # Cleanup alte Dateien (nur beim ersten Export)
            if self.export_config.get('keep_days', 0) > 0:
                cleanup_old_exports(base_dir, self.export_config['keep_days'])
            
            logger.info(f"Export für {task_id} erstellt: {export_meta}")
            return export_meta
            
        except Exception as e:
            logger.error(f"Fehler beim Export für {task_id}: {e}")
            return None
    
    def _save_result(self, task_id: str, result: Dict):
        """Speichert Task-Ergebnis"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{task_id}_{timestamp}.json"
            filepath = self.results_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Task-Ergebnisses {task_id}: {e}")
    
    async def run_task_manually(self, task_id: str) -> Dict:
        """Führt einen Task manuell aus"""
        task = next((t for t in self.tasks_config if t['id'] == task_id), None)
        if not task:
            return {'success': False, 'error': f'Task {task_id} nicht gefunden'}
            
        logger.info(f"Manuelle Task-Ausführung: {task_id}")
        
        start_time = datetime.now()
        
        try:
            result = await self.orchestrator.run_autopilot_task(task)
            duration_sec = (datetime.now() - start_time).total_seconds()
            
            # Beide Speicher-Formate
            self._save_result(task_id, result)
            write_result(task_id, {
                'success': result.get('success', False),
                'duration_sec': duration_sec,
                'provider': result.get('provider', task.get('provider', 'auto')),
                'task_type': task.get('task_type', 'analysis'),
                'notes': result.get('result', {}).get('kurz_zusammenfassung', '') if isinstance(result.get('result'), dict) else None,
                'error': result.get('error')
            })
            
            # Export-Funktionalität
            export_files = self._handle_export(task_id, result)
            if export_files:
                result['export_files'] = export_files
            
            return result
            
        except Exception as e:
            duration_sec = (datetime.now() - start_time).total_seconds()
            error_result = {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
            # Beide Speicher-Formate
            self._save_result(task_id, error_result)
            write_result(task_id, {
                'success': False,
                'duration_sec': duration_sec,
                'provider': task.get('provider', 'auto'),
                'task_type': task.get('task_type', 'analysis'),
                'error': str(e)
            })
            
            return error_result
    
    def get_status(self) -> Dict:
        """Gibt den aktuellen Autopilot-Status zurück"""
        return {
            'running': self.is_running,
            'tasks_count': len(self.tasks_config),
            'enabled_tasks': len([t for t in self.tasks_config if t.get('enabled', False)]),
            'scheduled_jobs': len(self.scheduler.get_jobs()) if self.is_running else 0,
            'tasks': [
                {
                    'id': task['id'],
                    'description': task.get('description', ''),
                    'schedule': task['schedule'],
                    'enabled': task.get('enabled', False),
                    'task_type': task.get('task_type', ''),
                    'provider': task.get('provider', 'auto')
                }
                for task in self.tasks_config
            ]
        }
    
    def get_recent_results(self, limit: int = 10) -> List[Dict]:
        """Gibt die letzten Task-Ergebnisse zurück"""
        try:
            result_files = list(self.results_dir.glob("*.json"))
            result_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            results = []
            for filepath in result_files[:limit]:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        result = json.load(f)
                        result['file'] = filepath.name
                        results.append(result)
                except Exception as e:
                    logger.warning(f"Fehler beim Lesen von Ergebnis-Datei {filepath}: {e}")
                    
            return results
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Ergebnisse: {e}")
            return []


# Globale Instanz für die API
autopilot_manager = AutopilotManager()
