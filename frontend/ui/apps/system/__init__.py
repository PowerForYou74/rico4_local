import streamlit as st
from ....app_registry import AppMeta, register
from . import agents, prompts, kb, runs, automations, settings

def render():
    st.markdown("## 🛠️ Rico System")
    tabs = st.tabs(["🤖 Agents","📚 Prompts","🧠 Knowledge Base","📈 Runs & Telemetry","🔗 Automations","⚙️ Settings"])
    with tabs[0]: agents.render()
    with tabs[1]: prompts.render()
    with tabs[2]: kb.render()
    with tabs[3]: runs.render()
    with tabs[4]: automations.render()
    with tabs[5]: settings.render()

register(AppMeta(
    key="system", name="System", icon="🛠️", render=render, category="Core"
))
