"""Provider Controls 2.0 - Request Composer mit UI_API_BASE"""
import streamlit as st
import os
from typing import Optional
from .toast import show_error, show_success

def _get_ui_api_base() -> str:
    """Holt UI_API_BASE aus .env.local oder verwendet Default"""
    return os.getenv("UI_API_BASE", "http://localhost:8000")

def _get_task_url() -> str:
    """Baut Task-URL mit UI_API_BASE"""
    api_base = _get_ui_api_base()
    return f"{api_base}/api/v1/task"

def render_provider_controls() -> Optional[bool]:
    """Request-Composer 2.0 mit Provider-Dropdown und UI_API_BASE"""
    
    st.markdown("### 📝 Request-Composer")
    
    # Input-Text mit verbesserter Gestaltung
    input_text = st.text_area(
        "Deine Anfrage an Rico:",
        value=st.session_state.ss_input_text,
        key="input_area",
        height=120,
        placeholder="Beschreibe deine Aufgabe für Rico...",
        help="Beschreibe klar und konkret, was Rico für dich tun soll."
    )
    st.session_state.ss_input_text = input_text
    
    # Control-Grid
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Provider-Auswahl mit allen Optionen
        provider_options = ["auto", "openai", "claude", "perplexity"]
        current_provider = st.session_state.ss_provider
        
        provider = st.selectbox(
            "Provider:",
            options=provider_options,
            index=provider_options.index(current_provider) if current_provider in provider_options else 0,
            key="provider_select",
            help="auto = Rico wählt besten Provider automatisch"
        )
        st.session_state.ss_provider = provider
    
    with col2:
        # Task-Typ mit erweiterten Optionen
        task_options = ["analyse", "recherche", "strategie", "code", "beratung", "optimierung"]
        current_task_type = st.session_state.ss_task_type
        
        task_type = st.selectbox(
            "Task-Typ:",
            options=task_options,
            index=task_options.index(current_task_type) if current_task_type in task_options else 0,
            key="task_type_select",
            help="Art der gewünschten Analyse"
        )
        st.session_state.ss_task_type = task_type
    
    with col3:
        # Auto-Send Toggle
        auto_send = st.checkbox(
            "Auto-Send",
            value=st.session_state.ss_auto_send_triggered,
            key="auto_send_toggle",
            help="Sendet Request automatisch bei Eingabe"
        )
        st.session_state.ss_auto_send_triggered = auto_send
    
    # Request-URL Anzeige (kompakt)
    api_base = _get_ui_api_base()
    request_url = f"POST {api_base}/api/v1/task?provider={provider}&task_type={task_type}"
    st.markdown(f"""
    <div style="
        background-color: var(--rico-surface);
        padding: var(--rico-space-sm);
        border-radius: var(--rico-radius-sm);
        border: 1px solid var(--rico-border);
        margin: var(--rico-space-sm) 0;
    ">
        <small style='color: var(--rico-text-muted)'>📡 {request_url}</small>
    </div>
    """, unsafe_allow_html=True)
    
    # Send-Button mit verbesserter Logik
    send_disabled = (
        not input_text.strip() or 
        not st.session_state.ss_backend_reachable
    )
    
    disabled_reason = ""
    if not input_text.strip():
        disabled_reason = "Eingabe erforderlich"
    elif not st.session_state.ss_backend_reachable:
        disabled_reason = "Backend offline"
    
    button_text = "🚀 An Rico senden"
    if send_disabled:
        button_text = f"🚀 An Rico senden ({disabled_reason})"
    
    if st.button(
        button_text, 
        key="send_request", 
        disabled=send_disabled,
        use_container_width=True,
        help="Cmd/Ctrl + Enter für schnelles Senden" if not send_disabled else f"Nicht verfügbar: {disabled_reason}"
    ):
        return True  # Trigger für Request senden
    
    # Footer-Info
    if not send_disabled:
        st.markdown("""
        <div style="
            background-color: var(--rico-surface);
            padding: var(--rico-space-sm);
            border-radius: var(--rico-radius-sm);
            border-left: 3px solid var(--rico-brand);
            margin: var(--rico-space-sm) 0;
        ">
            <small style='color: var(--rico-text-muted)'>
                💡 Tipp: Cmd/Ctrl + Enter für schnelles Senden<br>
                🔄 Auto-Send aktiviert automatisches Senden bei Eingabe
            </small>
        </div>
        """, unsafe_allow_html=True)
    
    return False

def get_request_payload() -> dict:
    """Erstellt Request-Payload aus Session State"""
    return {
        "prompt": st.session_state.ss_input_text.strip(),
        "task_type": st.session_state.ss_task_type,
        "provider": st.session_state.ss_provider,
    }
