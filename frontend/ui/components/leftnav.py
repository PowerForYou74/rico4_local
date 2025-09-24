# frontend/ui/components/leftnav.py
import streamlit as st

def render_left_nav(apps: dict, current: str, on_nav):
    st.markdown("## 🧭 Zentrale")
    if not apps:
        st.info("Keine Apps registriert.")
        return
    keys = list(apps.keys())
    # Fallback-Index
    try:
        idx = keys.index(current)
    except ValueError:
        idx = 0
    sel = st.radio(
        "Projekte",
        options=keys,
        index=idx,
        format_func=lambda k: f"{apps[k].icon} {apps[k].name}",
        label_visibility="collapsed",
    )
    if sel != current:
        on_nav(sel)
