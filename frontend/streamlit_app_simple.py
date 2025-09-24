# Rico 4.0 - Vereinfachte Streamlit App (funktionsfähig)
import streamlit as st
import requests
import json
import time
import os
from datetime import datetime

# Theme aktivieren
st.set_page_config(
    layout="wide", 
    page_title="Rico 4.0 - Das Tierkonzept",
    page_icon="🐾",
    initial_sidebar_state="expanded"
)

# Session State initialisieren
if 'ss_input_text' not in st.session_state:
    st.session_state.ss_input_text = ''
if 'ss_provider' not in st.session_state:
    st.session_state.ss_provider = 'auto'
if 'ss_task_type' not in st.session_state:
    st.session_state.ss_task_type = 'analyse'
if 'ss_last_result' not in st.session_state:
    st.session_state.ss_last_result = None
if 'ss_last_meta' not in st.session_state:
    st.session_state.ss_last_meta = None
if 'ss_backend_reachable' not in st.session_state:
    st.session_state.ss_backend_reachable = True

# API Configuration
UI_API_BASE = os.getenv("UI_API_BASE", "http://localhost:8000")
TASK_URL = f"{UI_API_BASE}/api/v1/task"
CHECK_URL = f"{UI_API_BASE}/check-keys"

# Header
st.markdown("""
# 🐾 Rico 4.0
## Das modulare Regenerationssystem für Pferd · Hund · Exoten
""")

# Backend-Status prüfen
try:
    response = requests.get(CHECK_URL, timeout=5)
    if response.ok:
        st.session_state.ss_backend_reachable = True
        st.success("🟢 Backend erreichbar")
    else:
        st.session_state.ss_backend_reachable = False
        st.error("🔴 Backend offline")
except:
    st.session_state.ss_backend_reachable = False
    st.error("🔴 Backend offline")

# Sidebar
with st.sidebar:
    st.header("🚦 System-Status")
    
    # Health Check
    try:
        response = requests.get(CHECK_URL, timeout=5)
        health_data = response.json()
        
        # Provider-Status anzeigen
        if 'providers' in health_data:
            providers = health_data['providers']
        else:
            # Adapter für alte API-Form
            providers = {k: v for k, v in health_data.items() if isinstance(v, dict) and 'status' in v}
        
        for provider, data in providers.items():
            status = data.get('status', 'unknown')
            if status == 'ok':
                st.success(f"✅ {provider}")
            else:
                st.error(f"❌ {provider}")
        
        st.markdown(f"**API Base:** {UI_API_BASE}")
        
    except Exception as e:
        st.error(f"Health-Check fehlgeschlagen: {e}")

# Main Content
st.header("📝 Request-Composer")

# Input
input_text = st.text_area(
    "Deine Anfrage an Rico:",
    value=st.session_state.ss_input_text,
    height=120,
    placeholder="Beschreibe deine Aufgabe für Rico..."
)
st.session_state.ss_input_text = input_text

# Controls
col1, col2, col3 = st.columns(3)

with col1:
    provider = st.selectbox(
        "Provider:",
        ["auto", "openai", "claude", "perplexity"],
        index=["auto", "openai", "claude", "perplexity"].index(st.session_state.ss_provider)
    )
    st.session_state.ss_provider = provider

with col2:
    task_type = st.selectbox(
        "Task-Typ:",
        ["analyse", "recherche", "strategie", "code"],
        index=["analyse", "recherche", "strategie", "code"].index(st.session_state.ss_task_type)
    )
    st.session_state.ss_task_type = task_type

with col3:
    st.markdown("**Request-URL:**")
    st.code(f"POST {TASK_URL}?provider={provider}&task_type={task_type}")

# Send Button
if st.button("🚀 An Rico senden", disabled=not input_text.strip() or not st.session_state.ss_backend_reachable):
    if not input_text.strip():
        st.warning("Bitte gib zuerst einen Text ein.")
    else:
        payload = {
            "prompt": input_text.strip(),
            "task_type": task_type,
            "provider": provider,
        }
        
        with st.spinner("Rico denkt…"):
            t0 = time.time()
            try:
                resp = requests.post(TASK_URL, json=payload, timeout=120)
                dur = time.time() - t0
            except Exception as e:
                st.error(f"Fehler bei Anfrage: {e}")
                resp = None
                dur = 0.0

        if resp and resp.ok:
            try:
                data = resp.json()
                st.session_state.ss_last_result = data.get("result", data)
                st.session_state.ss_last_meta = {
                    "used_provider": data.get("used_provider", provider),
                    "provider_model": data.get("provider_model", "N/A"),
                    "duration_s": round(dur, 2),
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                }
                st.success("✅ Antwort von Rico erhalten")
            except:
                st.error("Fehler beim Parsen der Antwort")
        else:
            st.error(f"Fehler {resp.status_code if resp else 'Verbindung'}")

# Ergebnisse anzeigen
if st.session_state.ss_last_result:
    st.header("📊 Ergebnisse")
    
    result = st.session_state.ss_last_result
    meta = st.session_state.ss_last_meta or {}
    
    # Meta-Info
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🤖 Provider", meta.get('used_provider', 'N/A'))
    with col2:
        st.metric("🧠 Modell", meta.get('provider_model', 'N/A'))
    with col3:
        st.metric("⏱️ Dauer", f"{meta.get('duration_s', 0):.1f}s")
    with col4:
        st.metric("🕒 Zeit", meta.get('timestamp', 'N/A'))
    
    # Tabs
    tabs = st.tabs([
        "📋 Zusammenfassung",
        "🔍 Kernbefunde", 
        "📋 Action Plan",
        "⚠️ Risiken",
        "💰 Cashflow-Radar",
        "👥 Team-Rollen",
        "📄 Rohdaten"
    ])
    
    with tabs[0]:
        st.markdown(result.get('kurz_zusammenfassung', 'Keine Zusammenfassung verfügbar'))
    
    with tabs[1]:
        st.markdown(result.get('kernbefunde', 'Keine Kernbefunde verfügbar'))
    
    with tabs[2]:
        st.markdown(result.get('action_plan', 'Kein Action Plan verfügbar'))
    
    with tabs[3]:
        st.markdown(result.get('risiken', 'Keine Risiken identifiziert'))
    
    with tabs[4]:
        st.markdown(result.get('cashflow_radar', 'Keine Cashflow-Analyse verfügbar'))
    
    with tabs[5]:
        st.markdown(result.get('team_rolle', 'Keine Team-Informationen verfügbar'))
    
    with tabs[6]:
        st.json({
            'result': result,
            'meta': meta
        })

# Footer
st.markdown("---")
st.markdown("**Rico 4.0 UI-Redesign** - Modernes, modulares Frontend mit Dark Theme")
