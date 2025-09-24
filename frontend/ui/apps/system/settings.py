import streamlit as st
from ...lib.api import get

def render():
    st.subheader("⚙️ Settings (Flags, keine Secrets)")
    st.write(get("/v2/core/settings"))
    st.info("Provider-Keys bleiben in .env.local – werden hier **nicht** angezeigt.")
