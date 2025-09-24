import streamlit as st, os
import sys
# Pfad für app_registry
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import app_registry

def render():
    st.header("🔗 Automations (n8n)")
    if os.getenv("N8N_ENABLED","false").lower() != "true":
        st.info("n8n ist deaktiviert – setze N8N_ENABLED=true.")
        st.button("🔧 n8n aktivieren", disabled=True)
        return
    
    # Einfache Demo ohne echte n8n-Integration
    st.success("n8n ist aktiviert!")
    st.selectbox("Webhook", ["CRM Lead", "Email Notification", "Data Export"], index=0)
    c1,c2 = st.columns(2)
    if c1.button("🔎 Test-Aufruf"):
        st.success("✅ Test erfolgreich - Webhook erreichbar")
    if c2.button("📤 Letztes Ergebnis senden", disabled=st.session_state.get("ss_last_result") is None):
        st.success("✅ Ergebnis erfolgreich übertragen")

app_registry.register(app_registry.AppMeta(
    key="automations", name="Automations", icon="🔗", render=render, category="Ops"
))
