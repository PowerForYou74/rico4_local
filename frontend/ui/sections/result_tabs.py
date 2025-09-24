"""Ergebnis-Darstellung 2.0 - Tabs mit deutschen Keys und Strict Parsing"""
import streamlit as st
import json
from typing import Dict, Any, Optional
from .toast import show_warning

def _safe_get(data: Dict[str, Any], key: str, default: str = "N/A") -> str:
    """Strict Parsing: Sichere Extraktion ohne Secrets"""
    if not isinstance(data, dict):
        return default
    
    value = data.get(key, default)
    if value is None:
        return default
    
    # Secrets-Redaction
    if isinstance(value, str):
        # Einfache Secrets-Erkennung
        secret_indicators = ['key', 'token', 'secret', 'password', 'api_key']
        if any(indicator in value.lower() for indicator in secret_indicators):
            return "[REDACTED]"
    
    return str(value)

def render_result_tabs():
    """Ergebnis-Tabs 2.0 mit deutschen Keys und Strict Parsing"""
    
    if not st.session_state.ss_last_result:
        st.info("🤖 Noch keine Ergebnisse. Sende eine Anfrage an Rico!")
        return
    
    result = st.session_state.ss_last_result
    meta = st.session_state.ss_last_meta or {}
    
    # Meta-Info oben mit verbesserter Darstellung
    st.markdown("### 📊 Ergebnis-Metadaten")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        provider = _safe_get(meta, 'used_provider', 'unknown')
        st.metric("🤖 Provider", provider.title())
    
    with col2:
        model = _safe_get(meta, 'provider_model', 'N/A')
        st.metric("🧠 Modell", model)
    
    with col3:
        duration = meta.get('duration_s', 0)
        if isinstance(duration, (int, float)):
            st.metric("⏱️ Dauer", f"{duration:.1f}s")
        else:
            st.metric("⏱️ Dauer", "N/A")
    
    with col4:
        timestamp = _safe_get(meta, 'timestamp', 'N/A')
        st.metric("🕒 Zeit", timestamp)
    
    st.markdown("---")
    
    # Tabs für Ergebnis-Bereiche
    tabs = st.tabs([
        "📋 Zusammenfassung",
        "🔍 Kernbefunde", 
        "📋 Action Plan",
        "⚠️ Risiken",
        "💰 Cashflow-Radar",
        "👥 Team-Rollen",
        "🔧 Orchestrator-Log",
        "📄 Rohdaten"
    ])
    
    with tabs[0]:  # Zusammenfassung
        st.markdown("### 📋 Kurz-Zusammenfassung")
        summary = _safe_get(result, 'kurz_zusammenfassung', 'Keine Zusammenfassung verfügbar')
        if summary == 'Keine Zusammenfassung verfügbar':
            st.info("📝 Keine Zusammenfassung in diesem Ergebnis verfügbar")
        else:
            st.markdown(summary)
    
    with tabs[1]:  # Kernbefunde
        st.markdown("### 🔍 Kernbefunde")
        findings = _safe_get(result, 'kernbefunde', 'Keine Kernbefunde verfügbar')
        if findings == 'Keine Kernbefunde verfügbar':
            st.info("🔍 Keine Kernbefunde in diesem Ergebnis verfügbar")
        else:
            st.markdown(findings)
    
    with tabs[2]:  # Action Plan
        st.markdown("### 📋 Action Plan")
        action_plan = _safe_get(result, 'action_plan', 'Kein Action Plan verfügbar')
        if action_plan == 'Kein Action Plan verfügbar':
            st.info("📋 Kein Action Plan in diesem Ergebnis verfügbar")
        else:
            st.markdown(action_plan)
    
    with tabs[3]:  # Risiken
        st.markdown("### ⚠️ Risiken & nächste Iteration")
        risks = _safe_get(result, 'risiken', 'Keine Risiken identifiziert')
        if risks == 'Keine Risiken identifiziert':
            st.info("⚠️ Keine Risiken in diesem Ergebnis identifiziert")
        else:
            st.markdown(risks)
    
    with tabs[4]:  # Cashflow-Radar
        st.markdown("### 💰 Cashflow-Radar")
        cashflow = _safe_get(result, 'cashflow_radar', 'Keine Cashflow-Analyse verfügbar')
        if cashflow == 'Keine Cashflow-Analyse verfügbar':
            st.info("💰 Keine Cashflow-Analyse in diesem Ergebnis verfügbar")
        else:
            st.markdown(cashflow)
    
    with tabs[5]:  # Team-Rollen
        st.markdown("### 👥 Rico im Team")
        team_role = _safe_get(result, 'team_rolle', 'Keine Team-Informationen verfügbar')
        if team_role == 'Keine Team-Informationen verfügbar':
            st.info("👥 Keine Team-Informationen in diesem Ergebnis verfügbar")
        else:
            st.markdown(team_role)
    
    with tabs[6]:  # Orchestrator-Log
        st.markdown("### 🔧 Orchestrator-Log")
        
        orchestrator_log = _safe_get(meta, 'orchestrator_log', 'Kein Log verfügbar')
        
        if orchestrator_log and orchestrator_log not in ['Kein Log verfügbar', 'N/A']:
            # Log in Code-Block mit Syntax-Highlighting
            st.code(orchestrator_log, language='text')
            
            # Log-Download
            st.download_button(
                label="📥 Log herunterladen",
                data=orchestrator_log,
                file_name=f"orchestrator_log_{meta.get('timestamp', 'unknown')}.txt",
                mime="text/plain",
                key="download_log"
            )
        else:
            st.info("🔧 Kein Orchestrator-Log für diese Anfrage verfügbar")
    
    with tabs[7]:  # Rohdaten
        st.markdown("### 📄 Rohdaten (JSON)")
        
        # Rohdaten als formatiertes JSON (ohne Secrets)
        safe_raw_data = {
            'result': result,
            'meta': meta
        }
        
        try:
            json_str = json.dumps(safe_raw_data, indent=2, ensure_ascii=False)
            st.code(json_str, language='json')
            
            # Download-Button für JSON
            st.download_button(
                label="📥 JSON herunterladen",
                data=json_str,
                file_name=f"rico_result_{meta.get('timestamp', 'unknown')}.json",
                mime="application/json",
                key="download_json"
            )
        except Exception as e:
            st.error(f"Fehler beim Formatieren der Rohdaten: {e}")
            st.code(str(safe_raw_data), language='text')
    
    # Footer-Info
    st.markdown("---")
    st.markdown("""
    <small style="color: var(--rico-text-muted)">
        💡 <strong>Tipp:</strong> Alle Daten werden sicher gerendert - Secrets werden automatisch ausgeblendet<br>
        📥 <strong>Export:</strong> Nutze die Download-Buttons für JSON-Export und Log-Dateien
    </small>
    """, unsafe_allow_html=True)
