"""n8n Integration Panel 2.0 - Optionales UI-Panel"""
import streamlit as st
import json
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

try:
    from integrations.n8n_client import is_enabled, get_available_webhooks, send, test_webhook
    N8N_AVAILABLE = True
except ImportError:
    N8N_AVAILABLE = False
    def is_enabled(): return False
    def get_available_webhooks(): return []
    def send(name, payload): return {'status': 'error', 'message_safe': 'n8n nicht verfügbar'}
    def test_webhook(name): return {'status': 'error', 'message_safe': 'n8n nicht verfügbar'}

from .toast import show_error, show_success

def render_n8n_panel():
    """n8n-Webhook Panel (nur bei N8N_ENABLED=true)"""
    if not N8N_AVAILABLE or not is_enabled():
        st.info("🔗 n8n ist deaktiviert (N8N_ENABLED=false).")
        return

    st.markdown("### 🔗 n8n-Workflows")
    
    # Webhook-Auswahl
    webhooks = get_available_webhooks()
    if not webhooks:
        st.warning("""
        **Keine Webhooks konfiguriert**
        
        Konfiguriere n8n-Webhooks über:
        - `N8N_WEBHOOKS_JSON` (JSON-String in .env.local)
        - `N8N_WEBHOOKS_FILE` (Pfad zu JSON-Datei)
        """)
        return
    
    webhook_names = [h["name"] for h in webhooks if "name" in h and "url" in h]
    if not webhook_names:
        st.error("Keine gültigen Webhooks gefunden (name + url erforderlich)")
        return
    
    selected_webhook = st.selectbox(
        "Webhook auswählen:", 
        webhook_names,
        help="Wähle den n8n-Webhook für die Integration"
    )
    
    # Action-Buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔎 Test-Aufruf", key="n8n_test", use_container_width=True):
            with st.spinner("Teste Webhook..."):
                result = test_webhook(selected_webhook)
                
                if result["status"] == "ok":
                    show_success(f"Test erfolgreich ({result['latency_ms']}ms)")
                elif result["status"] == "N/A":
                    show_success("n8n deaktiviert")
                else:
                    show_error("server", result["message_safe"])
    
    with col2:
        has_result = st.session_state.ss_last_result is not None
        if st.button(
            "📤 Letztes Ergebnis senden", 
            key="n8n_send_result", 
            disabled=not has_result,
            use_container_width=True,
            help="Sendet das letzte Rico-Ergebnis an n8n"
        ):
            if has_result:
                with st.spinner("Sende Ergebnis..."):
                    payload = {
                        "result": st.session_state.ss_last_result,
                        "meta": st.session_state.ss_last_meta,
                        "timestamp": st.session_state.ss_last_meta.get("timestamp", "N/A"),
                        "provider": st.session_state.ss_last_meta.get("used_provider", "N/A")
                    }
                    
                    result = send(selected_webhook, payload)
                    
                    if result["status"] == "ok":
                        show_success(f"Ergebnis gesendet ({result['latency_ms']}ms)")
                    else:
                        show_error("server", result["message_safe"])
    
    # Webhook-Details (erweitert)
    st.markdown("---")
    st.markdown("**📋 Webhook-Konfiguration:**")
    
    for webhook in webhooks:
        if webhook.get("name") == selected_webhook:
            st.markdown(f"""
            <div style="
                background-color: var(--rico-surface);
                padding: var(--rico-space-md);
                border-radius: var(--rico-radius-sm);
                border: 1px solid var(--rico-border);
                margin: var(--rico-space-sm) 0;
            ">
                <strong>Name:</strong> {webhook.get('name', 'N/A')}<br>
                <strong>URL:</strong> <code>{webhook.get('url', 'N/A')}</code><br>
                <strong>Timeout:</strong> {os.getenv('N8N_TIMEOUT_SECONDS', '20')}s
            </div>
            """, unsafe_allow_html=True)
            break
    
    # Footer-Info
    st.markdown("""
    <small style="color: var(--rico-text-muted)">
        💡 <strong>Tipp:</strong> n8n-Webhooks ermöglichen die Integration in externe Workflows<br>
        🔧 <strong>Konfiguration:</strong> Über .env.local oder n8n_webhooks.local.json
    </small>
    """, unsafe_allow_html=True)
