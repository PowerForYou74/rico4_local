# frontend/app_shell.py
import streamlit as st
from ui.theme import inject_theme
from ui.components.leftnav import render_left_nav
from ui.components.topbar import render_topbar
import app_registry

def _init_state():
    defaults = {
        "ss_current_app": "tierheilpraxis",
        "ss_search_query": "",
        "ss_notifications": [],
        "ss_backend_reachable": True,
        "ss_last_result": None,
        "ss_last_meta": None,
    }
    for k,v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def _navigate(app_key: str):
    st.session_state.ss_current_app = app_key

def run_shell():
    inject_theme()
    _init_state()

    # 🔸 Apps laden (vor jeglicher UI!)
    registry = app_registry.autoload()

    # Fallback, wenn leer
    if not registry:
        with st.sidebar:
            st.header("Zentrale")
            st.error("Keine Apps verfügbar – Registry ist leer.")
            if app_registry.LOAD_ERRORS:
                st.caption("Ladefehler:")
                for mod, err in app_registry.LOAD_ERRORS[:5]:
                    st.caption(f"• {mod}: {err}")
        st.warning("Bitte prüfen: Pfade/Namen der App-Module & __init__.py Dateien.")
        return

    # Sicherstellen, dass current_app existiert
    if st.session_state.ss_current_app not in registry:
        st.session_state.ss_current_app = next(iter(registry.keys()))

    # Sidebar / Topbar (dynamisch aus Registry)
    with st.sidebar:
        render_left_nav(registry, current=st.session_state.ss_current_app, on_nav=_navigate)

    render_topbar(registry, on_nav=_navigate)

    # Content-Container
    st.markdown('<div class="rico-container">', unsafe_allow_html=True)
    meta = registry.get(st.session_state.ss_current_app)
    try:
        meta.render()
    except Exception as e:
        st.error("Modulfehler – App isoliert. Die Zentrale läuft weiter.")
        st.caption(str(e))
    st.markdown('</div>', unsafe_allow_html=True)
