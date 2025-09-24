"""Health Check Panel 2.0 mit UI_API_BASE und Adapter-Support"""
import streamlit as st
import requests
import os
from datetime import datetime
from typing import Dict, Any, List
from ..layout import status_chip, info_card
from .toast import show_error

def _get_ui_api_base() -> str:
    """Holt UI_API_BASE aus .env.local oder verwendet Default"""
    return os.getenv("UI_API_BASE", "http://localhost:8000")

def _normalize_health_data(health_data: Dict[str, Any]) -> Dict[str, Any]:
    """Adapter: Unterstützt beide API-Response-Formen"""
    # Form A: {"openai": {...}, "claude": {...}, "perplexity": {...}}
    if "providers" not in health_data:
        # Direkte Provider-Keys vorhanden
        providers = {}
        for key, value in health_data.items():
            if isinstance(value, dict) and "status" in value:
                providers[key] = value
        if providers:
            return {"providers": providers}
    
    # Form B: {"providers": {"openai": {...}, ...}}
    return health_data

def _get_provider_info(provider_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extrahiert Provider-Informationen sicher"""
    return {
        "status": provider_data.get("status", "unknown"),
        "latency_ms": provider_data.get("latency_ms", 0),
        "model": provider_data.get("model", "N/A"),
        "env_source": provider_data.get("env_source", "N/A")
    }

def _get_n8n_status(api_base: str) -> Dict[str, Any]:
    """Holt n8n Status von der Integrations-API"""
    try:
        n8n_url = f"{api_base}/v2/integrations/n8n/status"
        response = requests.get(n8n_url, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {"enabled": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"enabled": False, "error": str(e)}


def render_health_panel():
    """Health-Check Panel 2.0 mit UI_API_BASE und verbesserter Darstellung"""
    try:
        # Health-Check mit UI_API_BASE
        api_base = _get_ui_api_base()
        check_url = f"{api_base}/check-keys"
        
        response = requests.get(check_url, timeout=5)
        raw_data = response.json()
        
        # Adapter: Normalisiere beide API-Formen
        health_data = _normalize_health_data(raw_data)
        
        # Backend erreichbar in Session State speichern
        st.session_state.ss_backend_reachable = True
        
        # n8n Status holen
        n8n_status = _get_n8n_status(api_base)
        
        # Ampel-Übersicht
        providers = health_data.get('providers', {})
        total_services = len(providers)
        ok_services = sum(1 for data in providers.values() if data.get('status') == 'ok')
        
        # n8n zu Services hinzufügen
        if n8n_status.get('enabled', False):
            total_services += 1
            if n8n_status.get('reachable', False) and n8n_status.get('api_key_present', False):
                ok_services += 1
        
        # Gesamt-Status
        if ok_services == total_services and total_services > 0:
            overall_status = 'ok'
            overall_text = f"Alle Services OK ({ok_services}/{total_services})"
        elif ok_services > 0:
            overall_status = 'warning' 
            overall_text = f"Teilweise OK ({ok_services}/{total_services})"
        else:
            overall_status = 'error'
            overall_text = f"Alle Services offline ({ok_services}/{total_services})"
            
        status_chip(overall_text, overall_status)
        
        if total_services > 0:
            st.markdown("---")
            
            # Provider-Details mit verbesserter Darstellung
            for provider, data in providers.items():
                info = _get_provider_info(data)
                status = info["status"]
                latency = info["latency_ms"]
                model = info["model"]
                env_source = info["env_source"]
                
                # Provider-Header
                provider_display = provider.replace('_', ' ').title()
                if status == 'ok':
                    st.markdown(f"✅ **{provider_display}**")
                elif status == 'error':
                    st.markdown(f"❌ **{provider_display}**")
                else:
                    st.markdown(f"⚠️ **{provider_display}**")
                
                # Provider-Details in Grid
                col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
                
                with col1:
                    if latency > 0:
                        if latency < 1000:
                            latency_color = 'ok'
                        elif latency < 3000:
                            latency_color = 'warning'
                        else:
                            latency_color = 'error'
                        
                        status_chip(f"{latency}ms", latency_color, show_icon=False)
                    else:
                        status_chip("N/A", "neutral", show_icon=False)
                
                with col2:
                    st.markdown(f"<small style='color: var(--rico-text-muted)'>{model}</small>", unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"<small style='color: var(--rico-text-muted)'>{env_source}</small>", unsafe_allow_html=True)
                
                with col4:
                    status_chip(status.upper(), status, show_icon=False)
                
                st.markdown("---")
            
            # n8n Status anzeigen
            if n8n_status.get('enabled', False):
                st.markdown("**🔗 n8n Integration**")
                
                col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
                
                with col1:
                    if n8n_status.get('reachable', False):
                        if n8n_status.get('api_key_present', False):
                            status_chip("OK", "ok", show_icon=False)
                        else:
                            status_chip("WARN", "warning", show_icon=False)
                    else:
                        status_chip("ERR", "error", show_icon=False)
                
                with col2:
                    host = n8n_status.get('host', 'N/A')
                    st.markdown(f"<small style='color: var(--rico-text-muted)'>{host}</small>", unsafe_allow_html=True)
                
                with col3:
                    api_key = "✓" if n8n_status.get('api_key_present', False) else "✗"
                    st.markdown(f"<small style='color: var(--rico-text-muted)'>API: {api_key}</small>", unsafe_allow_html=True)
                
                with col4:
                    if n8n_status.get('error_message'):
                        error_msg = n8n_status['error_message'][:20] + "..." if len(n8n_status['error_message']) > 20 else n8n_status['error_message']
                        st.markdown(f"<small style='color: var(--rico-text-muted)'>{error_msg}</small>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<small style='color: var(--rico-text-muted)'>Healthy</small>", unsafe_allow_html=True)
                
                st.markdown("---")
        
        # Footer-Info
        last_check = datetime.now().strftime("%H:%M:%S")
        st.markdown(f"<small style='color: var(--rico-text-muted)'>🕒 Letzter Check: {last_check}</small>", unsafe_allow_html=True)
        st.markdown(f"<small style='color: var(--rico-text-muted)'>🔗 API: {api_base}</small>", unsafe_allow_html=True)
        
        # Refresh Button
        if st.button("🔄 Aktualisieren", key="health_refresh", use_container_width=True):
            st.rerun()
            
    except requests.exceptions.RequestException as e:
        st.session_state.ss_backend_reachable = False
        show_error('server', f"Health-Check fehlgeschlagen: {str(e)}")
        
        # Offline-Status anzeigen
        status_chip("Backend offline", "error")
        info_card(
            title="❌ Verbindungsfehler",
            content="""
            Das Backend ist nicht erreichbar. Bitte prüfe:
            - Ist der Backend-Server gestartet?
            - Läuft er auf Port 8000?
            - Sind die API-Routen verfügbar?
            - Ist UI_API_BASE korrekt gesetzt?
            """,
            status="error"
        )
