"""
Rico 4.0 - Autopilot API Router
REST-API für Autopilot-Funktionalität
"""

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import FileResponse
from typing import Dict, List, Optional
import logging
from pathlib import Path
import os

from ..autopilot import autopilot_manager
from ..services.health_monitor import health_monitor
from ..services.log_manager import log_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/autopilot", tags=["autopilot"])


@router.get("/status")
async def get_autopilot_status() -> Dict:
    """Gibt den aktuellen Autopilot-Status zurück"""
    try:
        return {
            "success": True,
            "data": autopilot_manager.get_status()
        }
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Autopilot-Status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_autopilot() -> Dict:
    """Startet den Autopilot-Scheduler"""
    try:
        success = autopilot_manager.start()
        if success:
            return {
                "success": True,
                "message": "Autopilot erfolgreich gestartet"
            }
        else:
            return {
                "success": False,
                "message": "Autopilot konnte nicht gestartet werden"
            }
    except Exception as e:
        logger.error(f"Fehler beim Starten des Autopilots: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_autopilot() -> Dict:
    """Stoppt den Autopilot-Scheduler"""
    try:
        success = autopilot_manager.stop()
        if success:
            return {
                "success": True,
                "message": "Autopilot erfolgreich gestoppt"
            }
        else:
            return {
                "success": False,
                "message": "Autopilot war nicht gestartet oder konnte nicht gestoppt werden"
            }
    except Exception as e:
        logger.error(f"Fehler beim Stoppen des Autopilots: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-task")
async def run_task_manually(task_id: str) -> Dict:
    """Führt einen Task manuell aus"""
    try:
        result = await autopilot_manager.run_task_manually(task_id)
        return {
            "success": result.get("success", False),
            "data": result
        }
    except Exception as e:
        logger.error(f"Fehler bei manueller Task-Ausführung {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results")
async def get_recent_results(limit: int = 10) -> Dict:
    """Gibt die letzten Task-Ergebnisse zurück"""
    try:
        results = autopilot_manager.get_recent_results(limit)
        return {
            "success": True,
            "data": results
        }
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Task-Ergebnisse: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks")
async def get_tasks() -> Dict:
    """Gibt alle konfigurierten Tasks zurück"""
    try:
        status = autopilot_manager.get_status()
        return {
            "success": True,
            "data": status["tasks"]
        }
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_system_health() -> Dict:
    """Gibt System-Health-Status zurück"""
    try:
        health_data = health_monitor.get_system_health()
        alerts = health_monitor.check_alerts()
        
        return {
            "success": True,
            "data": {
                "health": health_data,
                "alerts": alerts,
                "alerts_count": len(alerts)
            }
        }
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des System-Health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/trends")
async def get_health_trends(hours: int = 24) -> Dict:
    """Gibt Health-Trends zurück"""
    try:
        trends = health_monitor.get_health_trends(hours)
        return {
            "success": True,
            "data": trends
        }
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Health-Trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_system() -> Dict:
    """Führt System-Cleanup durch"""
    try:
        cleanup_stats = log_manager.cleanup_old_logs()
        return {
            "success": True,
            "message": "System-Cleanup erfolgreich durchgeführt",
            "data": cleanup_stats
        }
    except Exception as e:
        logger.error(f"Fehler beim System-Cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/stats")
async def get_log_stats() -> Dict:
    """Gibt Log-Statistiken zurück"""
    try:
        stats = log_manager.get_log_stats()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Log-Statistiken: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Export-Endpunkte
@router.get("/exports/list")
async def list_exports(
    task_id: Optional[str] = Query(None, description="Filter nach Task-ID"),
    limit: int = Query(50, description="Maximale Anzahl Ergebnisse")
) -> Dict:
    """Listet verfügbare Export-Dateien auf"""
    try:
        # Export-Verzeichnis ermitteln
        export_dir = autopilot_manager.export_config.get('dir', 'data/exports')
        export_dir = os.getenv('EXPORTS_DIR', export_dir)
        base_dir = Path(export_dir)
        
        if not base_dir.exists():
            return {
                "success": True,
                "data": [],
                "message": "Export-Verzeichnis existiert nicht"
            }
        
        # Alle Export-Dateien sammeln
        export_files = []
        for file_path in base_dir.iterdir():
            if file_path.is_file() and file_path.suffix in ['.json', '.csv']:
                # Task-ID aus Dateinamen extrahieren
                filename = file_path.name
                if '__' in filename:
                    file_task_id = filename.split('__')[0]
                else:
                    file_task_id = filename.split('_')[0] if '_' in filename else 'unknown'
                
                # Filter nach Task-ID
                if task_id and file_task_id != task_id:
                    continue
                
                stat = file_path.stat()
                export_files.append({
                    "task_id": file_task_id,
                    "filename": filename,
                    "size": stat.st_size,
                    "created_at": stat.st_mtime,
                    "url": f"/api/v1/exports/download?file={filename}"
                })
        
        # Nach Erstellungszeit sortieren (neueste zuerst)
        export_files.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Limit anwenden
        export_files = export_files[:limit]
        
        return {
            "success": True,
            "data": export_files,
            "count": len(export_files)
        }
        
    except Exception as e:
        logger.error(f"Fehler beim Auflisten der Export-Dateien: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exports/download")
async def download_export(
    file: str = Query(..., description="Dateiname relativ zum Export-Verzeichnis")
) -> FileResponse:
    """Lädt eine Export-Datei herunter"""
    try:
        # Export-Verzeichnis ermitteln
        export_dir = autopilot_manager.export_config.get('dir', 'data/exports')
        export_dir = os.getenv('EXPORTS_DIR', export_dir)
        base_dir = Path(export_dir)
        
        # Sicherheitsprüfung: Datei muss im Export-Verzeichnis sein
        file_path = base_dir / file
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="Datei nicht gefunden")
        
        # Sicherheitsprüfung: Pfad-Traversal verhindern
        try:
            file_path.resolve().relative_to(base_dir.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="Zugriff verweigert")
        
        # MIME-Type bestimmen
        if file_path.suffix == '.json':
            media_type = 'application/json'
        elif file_path.suffix == '.csv':
            media_type = 'text/csv'
        else:
            media_type = 'application/octet-stream'
        
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=file_path.name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Download der Export-Datei {file}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
