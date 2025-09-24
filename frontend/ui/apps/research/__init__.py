import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import app_registry

def render():
    st.header("🧠 Research & Assist")
    st.text_area("Prompt", key="research_prompt", height=120, placeholder="Frage an Rico …")
    st.button("Frage stellen (Auto)")

app_registry.register(app_registry.AppMeta(
    key="research", name="Research", icon="🧠", render=render, category="Intelligence"
))
