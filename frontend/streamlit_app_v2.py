# Rico 4.0 - Modulare Streamlit App
import json
import time
import requests
from typing import Any, Dict, List
from datetime import datetime, timezone

import streamlit as st

# Rico 4.0 UI Module
from ui.theme import inject_theme
from ui.layout import app_header, sidebar_panel, status_chip, info_card
from ui.sections.health_panel import render_health_panel
from ui.sections.provider_controls import render_provider_controls
from ui.sections.result_tabs import render_result_tabs
from ui.sections.n8n_panel import render_n8n_panel
from ui.sections.toast import show_success, show_error, show_warning, show_info

# ============================================================================
# RICO 4.0 SESSION STATE MANAGEMENT
# ============================================================================

# Session State Keys (konsistent verwenden)
SS_KEYS = {
    'ss_input_text': '',
    'ss_provider': 'auto', 
    'ss_task_type': 'analyse',
    'ss_last_result': None,
    'ss_last_meta': None,
    'ss_auto_send_triggered': False,
    'ss_backend_reachable': True
}

# Initialisierung
for key, default in SS_KEYS.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ============================================================================
# RICO 4.0 THEME & LAYOUT
# ============================================================================

# Theme aktivieren
inject_theme()

# Haupt-Header
app_header(
    title="Rico 4.0", 
    subtitle="Das modulare Regenerationssystem für Pferd · Hund · Exoten",
    reachable=st.session_state.ss_backend_reachable
)

# ============================================================================
# API CONFIGURATION
# ============================================================================

API_BASE = "http://127.0.0.1:8000"
TASK_URL = f"{API_BASE}/api/v1/task"
CHECK_URL = f"{API_BASE}/check-keys"
AUTOPILOT_BASE = f"{API_BASE}/api/v1/autopilot"
MONITOR_BASE = f"{API_BASE}/api/monitor"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def to_bool(x) -> bool:
    """Robuste Konvertierung zu Boolean für UI-Flags/Statuses"""
    if isinstance(x, dict):
        return str(x.get("status", "")).strip().lower() == "ok"
    if isinstance(x, bool):
        return x
    if x is None:
        return False
    return str(x).strip().lower() in ("ok", "true", "1", "yes")

@st.cache_data(ttl=10.0, show_spinner=False)
def check_backend() -> Dict[str, Any]:
    """Backend-Erreichbarkeit prüfen"""
    info = {"reachable": False, "error": None}
    try:
        r = requests.get(CHECK_URL, timeout=5)
        if r.ok:
            info["reachable"] = True
            st.session_state.ss_backend_reachable = True
        else:
            info["error"] = f"Status {r.status_code}"
            st.session_state.ss_backend_reachable = False
    except Exception as e:
        info["error"] = str(e)
        st.session_state.ss_backend_reachable = False
    return info

def make_curl(payload: Dict[str, Any]) -> str:
    """Generiert cURL-Command für Debugging"""
    body = json.dumps(payload, ensure_ascii=False)
    return (
        "curl -X POST \\\n"
        f"  '{TASK_URL}' \\\n"
        "  -H 'accept: application/json' \\\n"
        "  -H 'Content-Type: application/json' \\\n"
        f"  -d '{body}'"
    )

# ============================================================================
# SIDEBAR LAYOUT
# ============================================================================

# Health-Check Panel
with st.sidebar:
    st.header("🚦 System-Status")
    render_health_panel()

# n8n Panel (optional)
with st.sidebar:
    st.header("🔗 n8n Integration")
    render_n8n_panel()

# Beispiel-Buttons
with st.sidebar:
    st.markdown("---")
    st.subheader("💡 Beispiele")
    
    if st.button("💡 Cashflow-Idee analysieren", use_container_width=True):
        st.session_state.ss_input_text = """
        Analysiere diese Cashflow-Idee für mein Startup:
        - Monatliche Abo-Modelle für Tierbesitzer
        - Premium-Beratung für Pferde- und Hundezüchter
        - Online-Kurse für Tiergesundheit
        """
        st.session_state.ss_auto_send_triggered = True
        st.rerun()
    
    if st.button("📊 Quartalsfokus vorschlagen", use_container_width=True):
        st.session_state.ss_input_text = """
        Erstelle einen Quartalsfokus für mein Tiergesundheits-Business:
        - Q1: Markteinführung
        - Q2: Kundenakquise  
        - Q3: Skalierung
        - Q4: Optimierung
        """
        st.session_state.ss_auto_send_triggered = True
        st.rerun()
    
    if st.button("🧩 Risiken & Maßnahmen", use_container_width=True):
        st.session_state.ss_input_text = """
        Identifiziere Risiken und Maßnahmen für mein Tiergesundheits-Startup:
        - Marktrisiken
        - Technische Risiken
        - Finanzielle Risiken
        - Rechtliche Risiken
        """
        st.session_state.ss_auto_send_triggered = True
        st.rerun()

# ============================================================================
# MAIN CONTENT AREA
# ============================================================================

# Provider Controls
render_provider_controls()

# Auto-Send Logic
if st.session_state.ss_auto_send_triggered:
    st.session_state.ss_auto_send_triggered = False
    
    if st.session_state.ss_input_text.strip():
        # Simuliere Button-Click für Request
        st.session_state.send_request_clicked = True
    else:
        show_warning("Kein Text eingegeben")

# Request Processing
if st.session_state.get('send_request_clicked', False):
    st.session_state.send_request_clicked = False
    
    if not st.session_state.ss_input_text.strip():
        show_warning("Bitte gib zuerst einen Text ein.")
    else:
        payload: Dict[str, Any] = {
            "prompt": st.session_state.ss_input_text.strip(),
            "task_type": st.session_state.ss_task_type,
            "provider": st.session_state.ss_provider,
        }
        
        with st.spinner("Rico denkt…"):
            t0 = time.time()
            try:
                resp = requests.post(TASK_URL, json=payload, timeout=120)
                dur = time.time() - t0
            except requests.exceptions.ConnectionError:
                show_error('server', "Keine Verbindung zum Backend. Läuft Uvicorn auf Port 8000?")
                resp = None
                dur = 0.0
            except Exception as e:
                show_error('server', f"Fehler bei Anfrage: {e}")
                resp = None
                dur = 0.0

        if resp is None:
            st.stop()

        try:
            data = resp.json()
        except Exception:
            data = {"raw_text": resp.text if resp is not None else ""}

        # Session State für Ergebnis speichern
        if resp.ok:
            st.session_state.ss_last_result = data.get("result", data)
            st.session_state.ss_last_meta = {
                "used_provider": data.get("used_provider", st.session_state.ss_provider),
                "provider_model": data.get("provider_model", "N/A"),
                "duration_s": round(dur, 2),
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "orchestrator_log": data.get("orchestrator_log", "Kein Log verfügbar")
            }
            show_success("Antwort von Rico erhalten")
        else:
            show_error('server', f"Fehler {resp.status_code}")

# Ergebnis-Darstellung
render_result_tabs()

# ============================================================================
# DEBUG SECTION (nur bei Bedarf)
# ============================================================================

if st.sidebar.checkbox("🔧 Debug-Modus", value=False):
    with st.sidebar:
        st.markdown("---")
        st.subheader("🔧 Debug-Info")
        
        # Session State
        st.markdown("**Session State:**")
        for key, value in st.session_state.items():
            if key.startswith('ss_'):
                st.caption(f"{key}: {str(value)[:50]}...")
        
        # Backend-Status
        backend_status = check_backend()
        st.markdown("**Backend-Status:**")
        st.caption(f"Erreichbar: {backend_status['reachable']}")
        if backend_status.get('error'):
            st.caption(f"Fehler: {backend_status['error']}")
        
        # cURL-Command
        if st.session_state.ss_input_text:
            payload = {
                "prompt": st.session_state.ss_input_text,
                "task_type": st.session_state.ss_task_type,
                "provider": st.session_state.ss_provider,
            }
            st.markdown("**cURL-Command:**")
            st.code(make_curl(payload), language='bash')
