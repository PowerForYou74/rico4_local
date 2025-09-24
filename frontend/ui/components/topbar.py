# frontend/ui/components/topbar.py
import streamlit as st

def render_topbar(apps: dict, on_nav):
    c1,c2,c3 = st.columns([2,1,1])
    with c1:
        st.session_state.ss_search_query = st.text_input(
            "🔎 Globale Suche",
            value=st.session_state.ss_search_query,
            placeholder="Suchen …"
        )
    with c2:
        st.metric("Benachrichtigungen", len(st.session_state.ss_notifications))
    with c3:
        labels = [(k, f"{apps[k].name}") for k in apps] if apps else []
        if not labels:
            st.selectbox("Projekt", ["(keine Apps)"], index=0, disabled=True)
            return
        keys = [k for k,_ in labels]
        current = st.session_state.ss_current_app
        try:
            idx = keys.index(current)
        except ValueError:
            idx = 0
        new_label = st.selectbox("Projekt", [apps[k].name for k in keys], index=idx)
        # Map Label → Key
        for k in keys:
            if apps[k].name == new_label:
                if k != current:
                    on_nav(k)
                break
