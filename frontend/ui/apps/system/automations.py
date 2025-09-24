import streamlit as st
from ...lib.api import post

def render():
    st.subheader("🔗 Automations (n8n)")
    ev = st.selectbox("Event", ["daily_summary", "appointment_to_invoice", "export_cashflow"])
    if st.button("Event auslösen"):
        st.json(post("/v2/core/events", {"type": ev}))
