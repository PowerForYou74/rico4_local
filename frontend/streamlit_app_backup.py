# frontend/streamlit_app.py
import json
import time
from typing import Any, Dict, List
from datetime import datetime, timezone

import requests
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="Rico 4.0 – Starter UI", layout="wide")
st.title("🧠 Rico 4.0 – Starter UI")

def to_bool(x) -> bool:
    """Robuste Konvertierung zu Boolean für UI-Flags/Statuses.
    
    Behandelt:
    - Dict: True nur wenn {"status": "OK"}
    - Bool: Direkte Rückgabe
    - String: True für "OK", "true", "1", "yes" (case-insensitive)
    - None: False
    - Sonst: False
    """
    if isinstance(x, dict):
        return str(x.get("status", "")).strip().lower() == "ok"
    if isinstance(x, bool):
        return x
    if x is None:
        return False
    return str(x).strip().lower() in ("ok", "true", "1", "yes")

API_BASE = "http://127.0.0.1:8000"
TASK_URL = f"{API_BASE}/api/v1/task"
CHECK_URL = f"{API_BASE}/check-keys"
AUTOPILOT_BASE = f"{API_BASE}/api/v1/autopilot"
MONITOR_BASE = f"{API_BASE}/api/monitor"

if "history" not in st.session_state:
    st.session_state.history: List[Dict[str, Any]] = []

@st.cache_data(ttl=10.0, show_spinner=False)
def check_backend() -> Dict[str, Any]:
    info = {"reachable": False, "openai": "unknown", "claude": "unknown", "perplexity": "unknown", "error": None}
    try:
        r = requests.get(CHECK_URL, timeout=5)
        if r.ok:
            info["reachable"] = True
            try:
                data = r.json()
                info["openai"] = data.get("openai", "unknown")
                info["claude"] = data.get("claude", "unknown")
                info["perplexity"] = data.get("perplexity", "unknown")
            except Exception:
                pass
        else:
            info["error"] = f"Status {r.status_code}"
    except Exception as e:
        info["error"] = str(e)
    return info

@st.cache_data(ttl=15.0, show_spinner=False)
def get_health_check_status() -> Dict[str, Any]:
    """Health-Check 2.0: Mini-Pings für alle Provider"""
    try:
        r = requests.get(f"{MONITOR_BASE}/health-check", timeout=10)
        if r.ok:
            return r.json()
        else:
            return {"error": f"Status {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=30.0, show_spinner=False)
def get_keys_status() -> Dict[str, Any]:
    """Prüft Status der API-Keys (ohne echte Calls)"""
    try:
        r = requests.get(f"{MONITOR_BASE}/check-keys", timeout=5)
        if r.ok:
            return r.json()
        else:
            return {"error": f"Status {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=5.0, show_spinner=False)
def get_autopilot_status() -> Dict[str, Any]:
    """Holt den aktuellen Autopilot-Status"""
    try:
        r = requests.get(f"{AUTOPILOT_BASE}/status", timeout=5)
        if r.ok:
            return r.json()
        else:
            return {"success": False, "error": f"Status {r.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@st.cache_data(ttl=5.0, show_spinner=False)
def get_autopilot_results(limit: int = 5) -> Dict[str, Any]:
    """Holt die letzten Autopilot-Ergebnisse"""
    try:
        r = requests.get(f"{AUTOPILOT_BASE}/results", params={"limit": limit}, timeout=5)
        if r.ok:
            return r.json()
        else:
            return {"success": False, "error": f"Status {r.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@st.cache_data(ttl=15.0, show_spinner=False)
def get_monitor_status() -> Dict[str, Any]:
    """Holt den Monitor-Status"""
    try:
        r = requests.get(f"{MONITOR_BASE}/status", timeout=5)
        if r.ok:
            return r.json()
        else:
            return {"error": f"Status {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=15.0, show_spinner=False)
def get_monitor_tasks() -> List[Dict[str, Any]]:
    """Holt alle Tasks mit Status"""
    try:
        r = requests.get(f"{MONITOR_BASE}/tasks", timeout=5)
        if r.ok:
            return r.json()
        else:
            return []
    except Exception as e:
        return []

@st.cache_data(ttl=15.0, show_spinner=False)
def get_monitor_logs(task_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Holt Task-Logs für einen spezifischen Task"""
    try:
        r = requests.get(f"{MONITOR_BASE}/logs", params={"task_id": task_id, "limit": limit}, timeout=5)
        if r.ok:
            return r.json()
        else:
            return []
    except Exception as e:
        return []

@st.cache_data(ttl=10.0, show_spinner=False)
def get_exports_list(task_id: str = None, limit: int = 5) -> Dict[str, Any]:
    """Holt die letzten Export-Dateien"""
    try:
        params = {"limit": limit}
        if task_id:
            params["task_id"] = task_id
        
        r = requests.get(f"{AUTOPILOT_BASE}/exports/list", params=params, timeout=5)
        if r.ok:
            return r.json()
        else:
            return {"success": False, "error": f"Status {r.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def autopilot_action(action: str, task_id: str = None) -> Dict[str, Any]:
    """Führt eine Autopilot-Aktion aus"""
    try:
        if action == "start":
            r = requests.post(f"{AUTOPILOT_BASE}/start", timeout=10)
        elif action == "stop":
            r = requests.post(f"{AUTOPILOT_BASE}/stop", timeout=10)
        elif action == "run_task" and task_id:
            r = requests.post(f"{AUTOPILOT_BASE}/run-task", params={"task_id": task_id}, timeout=60)
        else:
            return {"success": False, "error": "Unbekannte Aktion"}
            
        if r.ok:
            return r.json()
        else:
            return {"success": False, "error": f"Status {r.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def render_list(items: Any) -> None:
    """Defensive Rendering von Listen mit robusten Checks"""
    if isinstance(items, (list, tuple)):
        if not items:
            st.caption("– keine Einträge –")
        else:
            for i in items:
                # Defensive Behandlung: auch None/leere Werte anzeigen
                display_text = str(i) if i is not None else "– leer –"
                st.markdown(f"- {display_text}")
    elif isinstance(items, str) and items.strip():
        # Falls String übergeben wird, als einzelnes Element behandeln
        st.markdown(f"- {items.strip()}")
    else:
        st.caption("– keine Einträge –")

def render_result_block(result: Dict[str, Any]) -> None:
    """Defensive Rendering der Ergebnisblöcke mit robusten Checks"""
    with st.expander("📝 Kurz­zusammenfassung", expanded=True):
        text = result.get("kurz_zusammenfassung") or result.get("kurzfassung") or result.get("summary") or ""
        # Defensive Behandlung: auch leere Strings anzeigen
        display_text = str(text).strip() if text is not None else ""
        st.write(display_text if display_text else "– leer –")

    c1, c2 = st.columns(2)
    with c1:
        with st.expander("🔎 Kern­ergebnisse", expanded=False):
            render_list(result.get("kernbefunde") or result.get("kern_ergebnisse") or result.get("key_findings") or [])

        with st.expander("🛠️ Action Plan", expanded=False):
            render_list(result.get("action_plan") or [])

    with c2:
        with st.expander("💰 Cashflow-Radar", expanded=False):
            radar = result.get("cashflow_radar") or {}
            if isinstance(radar, dict) and radar:
                st.json(radar)
            else:
                st.caption("– leer –")

        with st.expander("⚠️ Risiken & Annahmen", expanded=False):
            render_list(result.get("risiken") or result.get("annahmen") or result.get("risks") or [])

    with st.expander("👥 Team-Rollen", expanded=False):
        roles = result.get("team_rolle") or {}
        if roles:
            nice = {k: ("aktiv" if v else "aus") for k, v in roles.items()}
            st.json(nice)
        else:
            st.caption("– leer –")

    # Neue Felder: Aufgabenverteilung und Orchestrator-Log
    with st.expander("🧭 Aufgabenverteilung", expanded=False):
        aufgaben = result.get("aufgabenverteilung") or result.get("aufgaben") or result.get("tasks") or result.get("task_distribution") or []
        if isinstance(aufgaben, (list, tuple)) and aufgaben:
            for aufgabe in aufgaben:
                st.markdown(f"- {aufgabe}")
        else:
            st.caption("– keine Aufgaben verteilt –")

    with st.expander("📓 Orchestrator-Log", expanded=False):
        log_text = result.get("orchestrator_log") or result.get("log") or result.get("orchestrator") or ""
        if log_text:
            st.code(log_text, language="text")
        else:
            st.caption("– kein Log verfügbar –")

def make_curl(payload: Dict[str, Any]) -> str:
    body = json.dumps(payload, ensure_ascii=False)
    return (
        "curl -X POST \\\n"
        f"  '{TASK_URL}' \\\n"
        "  -H 'accept: application/json' \\\n"
        "  -H 'Content-Type: application/json' \\\n"
        f"  -d '{body}'"
    )

# Seitenleiste / Status
st.sidebar.header("⚙️ Einstellungen")
status = check_backend()
is_reachable = to_bool(status.get("reachable", False))
if is_reachable:
    st.sidebar.success("Backend erreichbar")
    st.sidebar.caption(f"OpenAI: {status['openai']} · Claude: {status['claude']} · Perplexity: {status.get('perplexity', 'unknown')}")
else:
    st.sidebar.error("Backend **nicht** erreichbar")
    if status.get("error"):
        st.sidebar.caption(status["error"])
    st.sidebar.markdown(f"[Backend öffnen]({API_BASE}/api/v1/docs)")

# Health-Check 2.0 Sidebar
with st.sidebar.expander("🔍 Health-Check 2.0", expanded=False):
    health_status = get_health_check_status()
    keys_status = get_keys_status()
    
    if "error" not in health_status:
        providers = health_status.get("providers", {})
        summary = health_status.get("summary", {})
        
        st.metric("Provider Status", f"{summary.get('ok', 0)}/{summary.get('total', 0)} OK")
        
        # Provider-Ampeln
        for provider, data in providers.items():
            provider_status = data.get("status", "unknown") if isinstance(data, dict) else str(data)
            latency = data.get("latency_ms", 0) if isinstance(data, dict) else 0
            model = data.get("model", "") if isinstance(data, dict) else ""
            
            # Status-Icon
            if provider_status == "OK":
                icon = "🟢"
            elif provider_status == "N/A":
                icon = "⚪"
            else:
                icon = "🔴"
            
            st.caption(f"{icon} {provider.upper()}: {provider_status}")
            if latency > 0:
                st.caption(f"   ⏱️ {latency}ms · {model}")
    else:
        st.error(f"Health-Check Fehler: {health_status.get('error', 'Unbekannt')}")
    
    # Keys-Status
    if "error" not in keys_status:
        st.subheader("API-Keys")
        for provider, data in keys_status.items():
            if provider != "error":
                if isinstance(data, dict):
                    configured = to_bool(data.get("configured", False))
                    env_source = data.get("env_source", "unknown")
                    model = data.get("model", "")
                else:
                    configured = to_bool(data)
                    env_source = "unknown"
                    model = ""
                
                icon = "🔑" if configured else "❌"
                st.caption(f"{icon} {provider.upper()}: {'Gesetzt' if configured else 'Nicht gesetzt'}")
                if configured and isinstance(data, dict):
                    st.caption(f"   📁 {env_source} · {model}")
    else:
        st.caption(f"Keys-Status: {keys_status.get('error', 'Unbekannt')}")

# Autopilot-Sektion
st.sidebar.header("🤖 Autopilot")
autopilot_status = get_autopilot_status()

if to_bool(autopilot_status.get("success", False)):
    data = autopilot_status.get("data", {})
    is_running = to_bool(data.get("running", False)) if isinstance(data, dict) else False
    
    # Status-Anzeige
    if is_running:
        st.sidebar.success("🟢 Autopilot läuft")
        if st.sidebar.button("⏹️ Autopilot stoppen", use_container_width=True):
            result = autopilot_action("stop")
            if result.get("success"):
                st.sidebar.success("Autopilot gestoppt")
                st.cache_data.clear()
            else:
                st.sidebar.error(f"Fehler: {result.get('message', 'Unbekannter Fehler')}")
    else:
        st.sidebar.warning("🔴 Autopilot gestoppt")
        if st.sidebar.button("▶️ Autopilot starten", use_container_width=True):
            result = autopilot_action("start")
            if result.get("success"):
                st.sidebar.success("Autopilot gestartet")
                st.cache_data.clear()
            else:
                st.sidebar.error(f"Fehler: {result.get('message', 'Unbekannter Fehler')}")
    
    # Task-Übersicht
    tasks = data.get("tasks", [])
    enabled_tasks = [t for t in tasks if isinstance(t, dict) and to_bool(t.get("enabled", False))]
    
    if tasks:
        st.sidebar.subheader(f"📋 Tasks ({len(enabled_tasks)}/{len(tasks)} aktiv)")
        
        for task in tasks:
            if not isinstance(task, dict):
                continue
            task_id = task.get("id", "unknown")
            description = task.get("description", "")
            enabled = to_bool(task.get("enabled", False))
            schedule = task.get("schedule", "")
            
            # Task-Status-Icon
            status_icon = "🟢" if enabled else "🔴"
            
            with st.sidebar.expander(f"{status_icon} {description[:30]}..."):
                st.caption(f"ID: {task_id}")
                st.caption(f"Schedule: {schedule}")
                st.caption(f"Type: {task.get('task_type', '')}")
                st.caption(f"Provider: {task.get('provider', 'auto')}")
                
                # Manueller Trigger-Button
                if st.button(f"▶️ {task_id} ausführen", key=f"run_{task_id}"):
                    with st.spinner(f"Führe Task {task_id} aus..."):
                        result = autopilot_action("run_task", task_id)
                        if result.get("success"):
                            st.success(f"Task {task_id} ausgeführt")
                        else:
                            st.error(f"Fehler: {result.get('error', 'Unbekannter Fehler')}")
    
    # Letzte Ergebnisse
    st.sidebar.subheader("📊 Letzte Ergebnisse")
    results = get_autopilot_results(3)
    
    if to_bool(results.get("success", False)):
        recent_results = results.get("data", [])
        if recent_results:
            for result in recent_results:
                if not isinstance(result, dict):
                    continue
                task_id = result.get("task_id", "unknown")
                success = to_bool(result.get("success", False))
                timestamp = result.get("timestamp", "")
                
                # Zeit-Formatierung
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime("%H:%M")
                except:
                    time_str = timestamp[:5] if timestamp else "??:??"
                
                status_icon = "✅" if success else "❌"
                st.sidebar.caption(f"{status_icon} {task_id} - {time_str}")
        else:
            st.sidebar.caption("Keine Ergebnisse verfügbar")
    else:
        st.sidebar.caption("Fehler beim Laden der Ergebnisse")
        
else:
    st.sidebar.error("Autopilot-Status nicht verfügbar")
    if autopilot_status.get("error"):
        st.sidebar.caption(autopilot_status["error"])

# Task-Monitor Sidebar
with st.sidebar.expander("📊 Task-Monitor", expanded=False):
    # Monitor-Status
    monitor_status = get_monitor_status()
    
    if "error" not in monitor_status:
        autopilot_running = to_bool(monitor_status.get("autopilot_running", False)) if isinstance(monitor_status, dict) else False
        st.metric("Autopilot", "🟢 Läuft" if autopilot_running else "🔴 Gestoppt")
        active_tasks = monitor_status.get('active_tasks', 0) if isinstance(monitor_status, dict) else 0
        total_tasks = monitor_status.get('total_tasks', 0) if isinstance(monitor_status, dict) else 0
        st.metric("Tasks", f"{active_tasks}/{total_tasks}")
        
        # Task-Tabelle
        tasks = get_monitor_tasks()
        if tasks:
            st.subheader("Task-Status")
            
            # Erstelle DataFrame für bessere Darstellung
            task_data = []
            for task in tasks:
                if not isinstance(task, dict):
                    continue
                    
                # Status-Icon
                last_status = task.get("last_status", "pending")
                status_icon = {
                    "success": "🟢",
                    "error": "🔴", 
                    "pending": "⚪",
                    "stale": "🟡"
                }.get(last_status, "⚪")
                
                # Letzter Run formatieren
                last_run = task.get("last_run", "")
                if last_run:
                    try:
                        dt = datetime.fromisoformat(last_run.replace("Z", "+00:00"))
                        last_run_str = dt.strftime("%H:%M")
                    except:
                        last_run_str = last_run[:5] if last_run else "—"
                else:
                    last_run_str = "—"
                
                task_data.append({
                    "Status": f"{status_icon} {last_status}",
                    "ID": task.get("id", ""),
                    "Schedule": task.get("schedule", ""),
                    "Provider": task.get("provider", ""),
                    "Enabled": "✅" if to_bool(task.get("enabled", False)) else "❌",
                    "Letzter Run": last_run_str,
                    "Dauer (s)": f"{task.get('last_duration_sec', 0):.1f}" if task.get('last_duration_sec') else "—"
                })
            
            if task_data:
                df = pd.DataFrame(task_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Task-Detail-Auswahl
            st.subheader("Task-Details")
            task_ids = [task["id"] for task in tasks if isinstance(task, dict) and task.get("id")]
            selected_task = st.selectbox("Task wählen", task_ids, key="monitor_task_select")
            
            if selected_task:
                # Hole Logs für ausgewählten Task
                logs = get_monitor_logs(selected_task, 20)
                
                if logs:
                    st.subheader("Letzte Läufe")
                    
                    # Log-Tabelle
                    log_data = []
                    for log in logs:
                        if not isinstance(log, dict):
                            continue
                            
                        # Zeit formatieren
                        try:
                            dt = datetime.fromisoformat(log.get("ts", "").replace("Z", "+00:00"))
                            time_str = dt.strftime("%m-%d %H:%M")
                        except:
                            time_str = log.get("ts", "")[:10]
                        
                        log_status = log.get("status", "")
                        notes = log.get("notes", "")
                        
                        log_data.append({
                            "Zeit": time_str,
                            "Status": "✅" if log_status == "success" else "❌",
                            "Dauer (s)": f"{log.get('duration_sec', 0):.1f}" if log.get('duration_sec') else "—",
                            "Provider": log.get("provider", ""),
                            "Notes": notes[:50] + "..." if notes and len(notes) > 50 else notes
                        })
                    
                    if log_data:
                        log_df = pd.DataFrame(log_data)
                        st.dataframe(log_df, use_container_width=True, hide_index=True)
                        
                        # Dauer-Chart
                        if len(logs) > 1:
                            st.subheader("Dauer-Verlauf")
                            durations = [log.get("duration_sec", 0) for log in logs if isinstance(log, dict) and log.get("duration_sec") is not None]
                            if durations:
                                fig, ax = plt.subplots(figsize=(8, 4))
                                ax.plot(range(len(durations)), durations, marker='o')
                                ax.set_xlabel("Lauf")
                                ax.set_ylabel("Dauer (s)")
                                ax.set_title("Task-Dauer über Zeit")
                                ax.grid(True, alpha=0.3)
                                st.pyplot(fig)
                else:
                    st.caption("Keine Logs verfügbar")
                
                # Export-Sektion hinzufügen
                st.subheader("📁 Letzte Exporte")
                exports = get_exports_list(selected_task, 5)
                
                if to_bool(exports.get("success", False)) and exports.get("data"):
                    export_files = exports["data"]
                    
                    for export in export_files:
                        if not isinstance(export, dict):
                            continue
                        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                        
                        with col1:
                            # Dateiname und Zeit
                            filename = export.get("filename", "")
                            created_at = export.get("created_at", 0)
                            try:
                                from datetime import datetime
                                dt = datetime.fromtimestamp(created_at)
                                time_str = dt.strftime("%m-%d %H:%M")
                            except:
                                time_str = "—"
                            
                            st.caption(f"📄 {filename}")
                            st.caption(f"🕒 {time_str} · {export.get('size', 0)} bytes")
                        
                        with col2:
                            # JSON Download Button
                            if filename.endswith('.json') or 'json' in filename:
                                download_url = f"{API_BASE}{export.get('url', '')}"
                                st.markdown(f"[📄 JSON]({download_url})")
                        
                        with col3:
                            # CSV Download Button
                            if filename.endswith('.csv') or 'csv' in filename:
                                download_url = f"{API_BASE}{export.get('url', '')}"
                                st.markdown(f"[📊 CSV]({download_url})")
                        
                        with col4:
                            # Größe anzeigen
                            size_kb = export.get('size', 0) / 1024
                            st.caption(f"{size_kb:.1f} KB")
                    
                    # Manueller Export-Button
                    if st.button("🧾 Export jetzt erzeugen", key=f"export_{selected_task}"):
                        with st.spinner(f"Erzeuge Export für {selected_task}..."):
                            result = autopilot_action("run_task", selected_task)
                            if result.get("success"):
                                st.success(f"Task {selected_task} ausgeführt - Export erstellt")
                                st.cache_data.clear()  # Cache leeren für neue Daten
                            else:
                                st.error(f"Fehler: {result.get('error', 'Unbekannter Fehler')}")
                else:
                    st.caption("Keine Exporte verfügbar")
                    
                    # Manueller Export-Button auch wenn keine Exporte vorhanden
                    if st.button("🧾 Export jetzt erzeugen", key=f"export_{selected_task}_empty"):
                        with st.spinner(f"Erzeuge Export für {selected_task}..."):
                            result = autopilot_action("run_task", selected_task)
                            if result.get("success"):
                                st.success(f"Task {selected_task} ausgeführt - Export erstellt")
                                st.cache_data.clear()  # Cache leeren für neue Daten
                            else:
                                st.error(f"Fehler: {result.get('error', 'Unbekannter Fehler')}")
        else:
            st.caption("Keine Tasks gefunden")
    else:
        st.error(f"Monitor-Fehler: {monitor_status.get('error', 'Unbekannt')}")

st.sidebar.markdown("---")
st.sidebar.subheader("Beispiele")
st.sidebar.button("💡 Cashflow-Idee analysieren", use_container_width=True)
st.sidebar.button("📊 Quartalsfokus vorschlagen", use_container_width=True)
st.sidebar.button("🧩 Risiken & Maßnahmen", use_container_width=True)

# Neuer Button für Rollen-Aufgabenplan
if st.sidebar.button("🎯 Rollen-Aufgabenplan erstellen", use_container_width=True):
    # Vordefinierter Prompt für Rollen-Aufgabenplan
    rollen_prompt = """
Erstelle einen strukturierten Rollen-Aufgabenplan für ein Startup oder Unternehmen mit folgenden Bereichen:

STRATEGIE:
- Marktanalyse und Zielgruppen-Definition
- Geschäftsmodell-Validierung
- Wettbewerbsanalyse und Positionierung
- Roadmap-Entwicklung und Meilenstein-Planung

TECHNIK:
- Systemarchitektur und Technologie-Stack
- MVP-Entwicklung und Prototyping
- Datenbank-Design und API-Entwicklung
- Sicherheit und Performance-Optimierung

UMSETZUNG:
- Projektmanagement und Sprint-Planung
- Team-Koordination und Kommunikation
- Qualitätssicherung und Testing
- Deployment und Monitoring

Bitte strukturiere die Aufgabenverteilung nach diesen drei Hauptbereichen und weise konkrete, umsetzbare Aufgaben zu.
    """
    
    # Automatisch den Prompt in das Textfeld setzen und senden
    st.session_state.auto_prompt = rollen_prompt.strip()
    st.session_state.auto_send = True

# Prüfe ob ein automatischer Prompt gesetzt wurde
if hasattr(st.session_state, 'auto_prompt') and st.session_state.auto_prompt:
    default_prompt = st.session_state.auto_prompt
    # Session State zurücksetzen
    st.session_state.auto_prompt = None
else:
    default_prompt = ""

prompt = st.text_area(
    "Dein Input an Rico",
    height=160,
    placeholder="Beschreibe dein Ziel, Text oder Idee…",
    value=default_prompt,
)

col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    provider = st.selectbox(
        "KI-Provider",
        options=["auto", "openai", "claude", "perplexity"],
        index=0,
        help="auto = Rico wählt selbst, sonst fest OpenAI oder Claude.",
    )
with col2:
    task_type = st.selectbox(
        "Task-Typ",
        options=["analysis"],
        index=0,
    )
with col3:
    st.caption(f"**Request-Ziel:** `{TASK_URL}`")

# Prüfe ob automatisches Senden aktiviert ist
auto_send_triggered = hasattr(st.session_state, 'auto_send') and to_bool(st.session_state.auto_send)
if auto_send_triggered:
    # Session State zurücksetzen
    st.session_state.auto_send = None

if st.button("🚀 An Rico senden", use_container_width=True, disabled=not is_reachable) or auto_send_triggered:
    if not prompt.strip():
        st.warning("Bitte gib zuerst einen Text ein.")
    else:
        payload: Dict[str, Any] = {
            "prompt": prompt.strip(),
            "task_type": task_type,
            "provider": provider,
        }
        with st.spinner("Rico denkt…"):
            t0 = time.time()
            try:
                resp = requests.post(TASK_URL, json=payload, timeout=120)
                dur = time.time() - t0
            except requests.exceptions.ConnectionError:
                st.error("Keine Verbindung zum Backend. Läuft Uvicorn auf Port 8000?")
                resp = None
                dur = 0.0
            except Exception as e:
                st.error(f"Fehler bei Anfrage: {e}")
                resp = None
                dur = 0.0

        tabs = st.tabs(["Antwort", "Rohdaten", "Header", "cURL", "Verlauf"])

        if resp is None:
            with tabs[0]:
                st.stop()

        try:
            data = resp.json()
        except Exception:
            data = {"raw_text": resp.text if resp is not None else ""}

        st.session_state.history.insert(
            0,
            {
                "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": resp.status_code if resp is not None else "ERR",
                "duration_s": round(dur, 2) if resp is not None else None,
                "payload": payload,
                "response": data,
            },
        )

        with tabs[0]:
            st.write(f"**Status:** {resp.status_code}")
            if resp.ok:
                st.success("Antwort von Rico")
                used = data.get("used_provider") or provider
                st.caption(f"Verwendeter Provider: **{used}** · Dauer: {round(dur, 2)} s")

                result = data.get("result", data)
                if isinstance(result, dict):
                    render_result_block(result)
                else:
                    st.json(result)
            else:
                st.error(f"Fehler {resp.status_code}")
                st.code(resp.text or "", language="bash")

        with tabs[1]:
            st.json(data)
        with tabs[2]:
            try:
                st.json(dict(resp.headers))
            except Exception:
                st.caption("– keine Header –")
        with tabs[3]:
            st.code(make_curl(payload), language="bash")
        with tabs[4]:
            for ix, item in enumerate(st.session_state.history):
                with st.expander(f"#{ix+1} – {item['ts']} · Status {item['status']}"):
                    st.caption(f"Dauer: {item.get('duration_s')} s")
                    st.markdown("**Payload**")
                    st.json(item["payload"])
                    st.markdown("**Response**")
                    st.json(item["response"])
else:
    st.markdown("---")
    st.caption("Tipp: Wähle oben einen Provider (oder **auto**) und sende deinen Text an Rico.")