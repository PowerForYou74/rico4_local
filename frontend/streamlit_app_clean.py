# Rico 4.0 - Saubere, einfache Version
import streamlit as st
import requests
import json
import time
import os
from datetime import datetime

# Page Config
st.set_page_config(
    page_title="Rico 4.0",
    page_icon="🐾",
    layout="wide"
)

# Session State
if 'input_text' not in st.session_state:
    st.session_state.input_text = ''
if 'provider' not in st.session_state:
    st.session_state.provider = 'auto'
if 'task_type' not in st.session_state:
    st.session_state.task_type = 'analyse'
if 'last_result' not in st.session_state:
    st.session_state.last_result = None

# API Config
API_BASE = "http://localhost:8000"
TASK_URL = f"{API_BASE}/api/v1/task"
CHECK_URL = f"{API_BASE}/check-keys"

# Header
st.title("🐾 Rico 4.0")
st.markdown("**Das modulare Regenerationssystem für Pferd · Hund · Exoten**")

# Backend Status
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("### Status")
with col2:
    try:
        response = requests.get(CHECK_URL, timeout=3)
        if response.ok:
            st.success("🟢 Backend OK")
        else:
            st.error("🔴 Backend Error")
    except:
        st.error("🔴 Backend Offline")

# Main Form
with st.form("rico_form"):
    st.subheader("📝 Anfrage an Rico")
    
    # Text Input
    text = st.text_area(
        "Deine Anfrage:",
        value=st.session_state.input_text,
        height=100,
        placeholder="Beschreibe deine Aufgabe..."
    )
    
    # Controls
    col1, col2 = st.columns(2)
    with col1:
        provider = st.selectbox(
            "Provider:",
            ["auto", "openai", "claude", "perplexity"],
            index=["auto", "openai", "claude", "perplexity"].index(st.session_state.provider)
        )
    
    with col2:
        task_type = st.selectbox(
            "Task-Typ:",
            ["analyse", "recherche", "strategie", "code"],
            index=["analyse", "recherche", "strategie", "code"].index(st.session_state.task_type)
        )
    
    # Submit Button
    submitted = st.form_submit_button("🚀 An Rico senden")
    
    if submitted and text.strip():
        # Update Session State
        st.session_state.input_text = text
        st.session_state.provider = provider
        st.session_state.task_type = task_type
        
        # Send Request
        payload = {
            "prompt": text.strip(),
            "task_type": task_type,
            "provider": provider
        }
        
        with st.spinner("Rico denkt..."):
            start_time = time.time()
            try:
                response = requests.post(TASK_URL, json=payload, timeout=120)
                duration = time.time() - start_time
                
                if response.ok:
                    data = response.json()
                    st.session_state.last_result = data.get("result", data)
                    
                    st.success(f"✅ Antwort erhalten ({duration:.1f}s)")
                    
                    # Show Result
                    result = st.session_state.last_result
                    if result:
                        st.subheader("📊 Ergebnis")
                        
                        # Tabs
                        tabs = st.tabs(["Zusammenfassung", "Kernbefunde", "Action Plan", "Risiken"])
                        
                        with tabs[0]:
                            st.markdown(result.get('kurz_zusammenfassung', 'Keine Zusammenfassung'))
                        
                        with tabs[1]:
                            st.markdown(result.get('kernbefunde', 'Keine Kernbefunde'))
                        
                        with tabs[2]:
                            st.markdown(result.get('action_plan', 'Kein Action Plan'))
                        
                        with tabs[3]:
                            st.markdown(result.get('risiken', 'Keine Risiken'))
                        
                        # Meta Info
                        st.markdown("---")
                        st.markdown(f"**Provider:** {data.get('used_provider', 'N/A')} | **Dauer:** {duration:.1f}s | **Zeit:** {datetime.now().strftime('%H:%M:%S')}")
                
                else:
                    st.error(f"❌ Fehler {response.status_code}")
                    
            except Exception as e:
                st.error(f"❌ Fehler: {e}")
    
    elif submitted and not text.strip():
        st.warning("⚠️ Bitte gib einen Text ein!")

# Sidebar
with st.sidebar:
    st.header("🔧 System")
    
    # Health Check
    try:
        response = requests.get(CHECK_URL, timeout=3)
        if response.ok:
            health_data = response.json()
            
            # Show Provider Status
            if 'providers' in health_data:
                providers = health_data['providers']
            else:
                # Fallback for different API format
                providers = {k: v for k, v in health_data.items() if isinstance(v, dict) and 'status' in v}
            
            for provider_name, provider_data in providers.items():
                status = provider_data.get('status', 'unknown')
                if status == 'ok':
                    st.success(f"✅ {provider_name}")
                else:
                    st.error(f"❌ {provider_name}")
            
            st.markdown(f"**API:** {API_BASE}")
        
    except Exception as e:
        st.error(f"Health-Check fehlgeschlagen: {e}")
    
    # Quick Examples
    st.header("💡 Beispiele")
    
    if st.button("Cashflow-Idee"):
        st.session_state.input_text = """
        Analysiere diese Cashflow-Idee:
        - Monatliche Abo-Modelle
        - Premium-Beratung
        - Online-Kurse
        """
        st.rerun()
    
    if st.button("Quartalsfokus"):
        st.session_state.input_text = """
        Erstelle Quartalsfokus:
        - Q1: Markteinführung
        - Q2: Kundenakquise
        - Q3: Skalierung
        - Q4: Optimierung
        """
        st.rerun()

# Footer
st.markdown("---")
st.markdown("*Rico 4.0 - Einfache, saubere UI*")
