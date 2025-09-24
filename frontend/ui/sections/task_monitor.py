"""Task Monitor Panel - Monitoring von Rico-Aufgaben"""
import streamlit as st
import os
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from ..layout import status_chip, info_card
from .toast import show_error, show_info

def _get_ui_api_base() -> str:
    """Holt UI_API_BASE aus .env.local oder verwendet Default"""
    return os.getenv("UI_API_BASE", "http://localhost:8000")

def _get_autopilot_base() -> str:
    """Baut Autopilot-API-Base mit UI_API_BASE"""
    api_base = _get_ui_api_base()
    return f"{api_base}/api/v1/autopilot"

def _get_monitor_base() -> str:
    """Baut Monitor-API-Base mit UI_API_BASE"""
    api_base = _get_ui_api_base()
    return f"{api_base}/api/monitor"

def render_task_monitor():
    """Task-Monitor Panel für Autopilot und Monitoring"""
    
    st.markdown("### 📊 Task-Monitor")
    
    # Autopilot-Status
    autopilot_status = _check_autopilot_status()
    
    if autopilot_status.get("enabled", False):
        status_chip("Autopilot aktiv", "ok")
        
        # Autopilot-Controls
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("⏸️ Pause", key="autopilot_pause", use_container_width=True):
                _pause_autopilot()
        
        with col2:
            if st.button("▶️ Start", key="autopilot_start", use_container_width=True):
                _start_autopilot()
        
        # Aktuelle Tasks
        _show_active_tasks()
        
    else:
        status_chip("Autopilot inaktiv", "neutral")
        
        # Autopilot-Info
        info_card(
            title="🤖 Autopilot-Status",
            content="Autopilot ist derzeit deaktiviert. Aktiviere ihn über die Konfiguration.",
            status="info"
        )
    
    st.markdown("---")
    
    # Task-Historie
    _show_task_history()
    
    # Performance-Metriken
    _show_performance_metrics()

def _check_autopilot_status() -> Dict[str, Any]:
    """Prüft Autopilot-Status"""
    try:
        autopilot_base = _get_autopilot_base()
        response = requests.get(f"{autopilot_base}/status", timeout=5)
        
        if response.ok:
            return response.json()
        else:
            return {"enabled": False, "error": f"Status {response.status_code}"}
    except Exception as e:
        return {"enabled": False, "error": str(e)}

def _pause_autopilot():
    """Pausiert Autopilot"""
    try:
        autopilot_base = _get_autopilot_base()
        response = requests.post(f"{autopilot_base}/pause", timeout=10)
        
        if response.ok:
            show_info("Autopilot pausiert")
            st.rerun()
        else:
            show_error("server", f"Fehler beim Pausieren: {response.status_code}")
    except Exception as e:
        show_error("server", f"Fehler beim Pausieren: {e}")

def _start_autopilot():
    """Startet Autopilot"""
    try:
        autopilot_base = _get_autopilot_base()
        response = requests.post(f"{autopilot_base}/start", timeout=10)
        
        if response.ok:
            show_info("Autopilot gestartet")
            st.rerun()
        else:
            show_error("server", f"Fehler beim Starten: {response.status_code}")
    except Exception as e:
        show_error("server", f"Fehler beim Starten: {e}")

def _show_active_tasks():
    """Zeigt aktive Tasks"""
    st.markdown("**🔄 Aktive Tasks:**")
    
    try:
        monitor_base = _get_monitor_base()
        response = requests.get(f"{monitor_base}/active", timeout=5)
        
        if response.ok:
            active_tasks = response.json()
            
            if active_tasks:
                for task in active_tasks:
                    task_name = task.get("name", "Unbekannte Aufgabe")
                    task_status = task.get("status", "unknown")
                    task_started = task.get("started_at", "N/A")
                    
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{task_name}**")
                    
                    with col2:
                        status_chip(task_status.upper(), task_status, show_icon=False)
                    
                    with col3:
                        st.markdown(f"<small>{task_started}</small>", unsafe_allow_html=True)
            else:
                st.info("Keine aktiven Tasks")
        else:
            st.warning(f"Fehler beim Laden aktiver Tasks: {response.status_code}")
            
    except Exception as e:
        st.warning(f"Fehler beim Laden aktiver Tasks: {e}")

def _show_task_history():
    """Zeigt Task-Historie"""
    st.markdown("**📈 Task-Historie (letzte 24h):**")
    
    try:
        monitor_base = _get_monitor_base()
        response = requests.get(f"{monitor_base}/history", timeout=5)
        
        if response.ok:
            history = response.json()
            
            if history:
                # Letzte 10 Tasks
                recent_tasks = history[:10]
                
                for task in recent_tasks:
                    task_name = task.get("name", "Unbekannte Aufgabe")
                    task_status = task.get("status", "unknown")
                    task_duration = task.get("duration_s", 0)
                    task_timestamp = task.get("timestamp", "N/A")
                    
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{task_name}**")
                    
                    with col2:
                        status_chip(task_status.upper(), task_status, show_icon=False)
                    
                    with col3:
                        if isinstance(task_duration, (int, float)):
                            st.markdown(f"<small>{task_duration:.1f}s</small>", unsafe_allow_html=True)
                        else:
                            st.markdown("<small>N/A</small>", unsafe_allow_html=True)
                    
                    with col4:
                        st.markdown(f"<small>{task_timestamp}</small>", unsafe_allow_html=True)
            else:
                st.info("Keine Task-Historie verfügbar")
        else:
            st.warning(f"Fehler beim Laden der Historie: {response.status_code}")
            
    except Exception as e:
        st.warning(f"Fehler beim Laden der Historie: {e}")

def _show_performance_metrics():
    """Zeigt Performance-Metriken"""
    st.markdown("**📊 Performance-Metriken:**")
    
    try:
        monitor_base = _get_monitor_base()
        response = requests.get(f"{monitor_base}/metrics", timeout=5)
        
        if response.ok:
            metrics = response.json()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_tasks = metrics.get("total_tasks", 0)
                st.metric("Gesamt Tasks", total_tasks)
            
            with col2:
                success_rate = metrics.get("success_rate", 0)
                st.metric("Erfolgsrate", f"{success_rate:.1%}")
            
            with col3:
                avg_duration = metrics.get("avg_duration_s", 0)
                st.metric("Ø Dauer", f"{avg_duration:.1f}s")
        else:
            st.warning(f"Fehler beim Laden der Metriken: {response.status_code}")
            
    except Exception as e:
        st.warning(f"Fehler beim Laden der Metriken: {e}")
    
    # Footer-Info
    st.markdown("---")
    st.markdown("""
    <small style="color: var(--rico-text-muted)">
        📊 <strong>Monitoring:</strong> Überwacht Autopilot-Tasks und Performance<br>
        🔄 <strong>Auto-Refresh:</strong> Aktualisiert sich automatisch alle 30 Sekunden
    </small>
    """, unsafe_allow_html=True)
