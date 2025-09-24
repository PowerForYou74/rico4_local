"""
Rico 4.0 - Health Monitor
System-Überwachung und Gesundheitschecks
"""

import asyncio
import logging
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class HealthMonitor:
    """System-Health-Monitor für Rico 4.0"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.metrics_history = []
        self.max_history = 100  # Maximale Anzahl gespeicherter Metriken
        
    def get_system_health(self) -> Dict[str, Any]:
        """Gibt aktuellen System-Health-Status zurück"""
        try:
            # CPU und Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Prozess-Informationen
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    if 'python' in proc.info['name'].lower():
                        processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cpu_percent': proc.info['cpu_percent'],
                            'memory_percent': proc.info['memory_percent']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Uptime berechnen
            uptime = datetime.now() - self.start_time
            
            health_data = {
                'timestamp': datetime.now().isoformat(),
                'uptime_seconds': int(uptime.total_seconds()),
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_gb': round(memory.available / (1024**3), 2),
                    'disk_percent': disk.percent,
                    'disk_free_gb': round(disk.free / (1024**3), 2)
                },
                'processes': processes,
                'health_score': self._calculate_health_score(cpu_percent, memory.percent, disk.percent)
            }
            
            # Metriken zur Historie hinzufügen
            self.metrics_history.append(health_data)
            if len(self.metrics_history) > self.max_history:
                self.metrics_history.pop(0)
                
            return health_data
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der System-Metriken: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'health_score': 0
            }
    
    def _calculate_health_score(self, cpu: float, memory: float, disk: float) -> int:
        """Berechnet Health-Score (0-100)"""
        try:
            # CPU Score (0-40 Punkte)
            cpu_score = max(0, 40 - (cpu / 2.5))  # 100% CPU = 0 Punkte
            
            # Memory Score (0-30 Punkte)
            memory_score = max(0, 30 - (memory / 3.33))  # 100% Memory = 0 Punkte
            
            # Disk Score (0-30 Punkte)
            disk_score = max(0, 30 - (disk / 3.33))  # 100% Disk = 0 Punkte
            
            total_score = int(cpu_score + memory_score + disk_score)
            return min(100, max(0, total_score))
            
        except Exception:
            return 50  # Neutraler Score bei Fehlern
    
    def get_health_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Gibt Health-Trends der letzten Stunden zurück"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # Filtere Metriken der letzten Stunden
            recent_metrics = [
                m for m in self.metrics_history 
                if datetime.fromisoformat(m['timestamp']) > cutoff_time
            ]
            
            if not recent_metrics:
                return {'error': 'Keine Metriken in den letzten Stunden verfügbar'}
            
            # Berechne Durchschnittswerte
            avg_cpu = sum(m['system']['cpu_percent'] for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m['system']['memory_percent'] for m in recent_metrics) / len(recent_metrics)
            avg_health = sum(m['health_score'] for m in recent_metrics) / len(recent_metrics)
            
            return {
                'period_hours': hours,
                'data_points': len(recent_metrics),
                'averages': {
                    'cpu_percent': round(avg_cpu, 2),
                    'memory_percent': round(avg_memory, 2),
                    'health_score': round(avg_health, 2)
                },
                'trend': self._calculate_trend(recent_metrics)
            }
            
        except Exception as e:
            logger.error(f"Fehler beim Berechnen der Health-Trends: {e}")
            return {'error': str(e)}
    
    def _calculate_trend(self, metrics: List[Dict]) -> str:
        """Berechnet Trend (steigend/fallend/stabil)"""
        if len(metrics) < 2:
            return 'unbekannt'
        
        try:
            # Vergleiche erste und letzte Hälfte
            mid_point = len(metrics) // 2
            first_half_avg = sum(m['health_score'] for m in metrics[:mid_point]) / mid_point
            second_half_avg = sum(m['health_score'] for m in metrics[mid_point:]) / (len(metrics) - mid_point)
            
            diff = second_half_avg - first_half_avg
            
            if diff > 5:
                return 'steigend'
            elif diff < -5:
                return 'fallend'
            else:
                return 'stabil'
                
        except Exception:
            return 'unbekannt'
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """Prüft auf kritische System-Alerts"""
        alerts = []
        
        try:
            health = self.get_system_health()
            system = health.get('system', {})
            
            # CPU Alert
            if system.get('cpu_percent', 0) > 90:
                alerts.append({
                    'type': 'cpu_high',
                    'severity': 'warning',
                    'message': f"CPU-Auslastung kritisch: {system['cpu_percent']:.1f}%",
                    'timestamp': datetime.now().isoformat()
                })
            
            # Memory Alert
            if system.get('memory_percent', 0) > 90:
                alerts.append({
                    'type': 'memory_high',
                    'severity': 'critical',
                    'message': f"Speicher-Auslastung kritisch: {system['memory_percent']:.1f}%",
                    'timestamp': datetime.now().isoformat()
                })
            
            # Disk Alert
            if system.get('disk_percent', 0) > 90:
                alerts.append({
                    'type': 'disk_high',
                    'severity': 'warning',
                    'message': f"Festplatten-Auslastung kritisch: {system['disk_percent']:.1f}%",
                    'timestamp': datetime.now().isoformat()
                })
            
            # Health Score Alert
            if health.get('health_score', 0) < 30:
                alerts.append({
                    'type': 'health_low',
                    'severity': 'critical',
                    'message': f"System-Health kritisch: {health['health_score']}/100",
                    'timestamp': datetime.now().isoformat()
                })
                
        except Exception as e:
            alerts.append({
                'type': 'monitor_error',
                'severity': 'error',
                'message': f"Health-Monitor Fehler: {str(e)}",
                'timestamp': datetime.now().isoformat()
            })
        
        return alerts


# Globale Instanz
health_monitor = HealthMonitor()
