# frontend/ui/theme.py
import streamlit as st

TOKENS = {
    "colors": {
        "bg": "#0f1216", "surface": "#151a21", "panel": "#1a2028",
        "border": "#2d3748",
        "text": "#e6edf3", "text_muted": "#9fb0c3",
        "brand": "#87b0ff", "brand_light": "#a9c3ff",
        "ok": "#36d399", "warn": "#fbbf24", "err": "#f87171", "info": "#60a5fa",
    },
    "radius": {"sm":"6px","md":"10px","lg":"14px","xl":"20px"},
    "space": {"xs":"4px","sm":"8px","md":"12px","lg":"20px","xl":"32px"},
    "shadow": {"sm":"0 1px 3px rgba(0,0,0,0.3)","md":"0 4px 6px rgba(0,0,0,0.4)","lg":"0 10px 15px rgba(0,0,0,0.5)"},
    "font": {"sans": '-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif'}
}

def inject_theme():
    st.set_page_config(layout="wide", page_title="Rico Control Center", page_icon="🧭", initial_sidebar_state="expanded")
    css = f"""
    <style>
    :root {{
      --rico-bg:#0f1216; --rico-surface:#151a21; --rico-panel:#1a2028; --rico-border:#2d3748;
      --rico-text:#e9eef5; --rico-text-muted:#b4c2d3; /* etwas heller */
      --rico-brand:#87b0ff; --rico-brand-light:#a9c3ff;
      --rico-ok:#36d399; --rico-warn:#fbbf24; --rico-err:#f87171; --rico-info:#60a5fa;
      --rico-radius-sm:6px; --rico-radius-md:12px; --rico-radius-lg:18px;
      --rico-space-xs:4px; --rico-space-sm:8px; --rico-space-md:12px; --rico-space-lg:20px; --rico-space-xl:32px;
      --rico-shadow-md:0 6px 16px rgba(0,0,0,.35);
      --rico-container:1240px; /* NEU: feste Content-Breite */
    }}
    .stApp {{ background:var(--rico-bg); color:var(--rico-text); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }}
    .stSidebar {{ background:var(--rico-panel); }}
    .rico-container {{ max-width:var(--rico-container); margin:0 auto; }}
    .rico-card {{
      background:var(--rico-surface); border:1px solid var(--rico-border);
      border-radius:var(--rico-radius-lg); padding:var(--rico-space-lg); box-shadow:var(--rico-shadow-md);
    }}
    .rico-active {{ outline:2px solid var(--rico-brand); }}
    .stButton>button {{
      background:var(--rico-brand); color:#fff; border:0; border-radius:var(--rico-radius-md);
      box-shadow:var(--rico-shadow-md); transition:.15s; font-weight:600;
    }}
    .stButton>button:hover {{ background:var(--rico-brand-light); transform:translateY(-1px); }}
    input, textarea, select {{ outline-color:var(--rico-brand) !important; }}
    h1,h2,h3 {{ color:#f3f6fb; }}
    small, .muted {{ color:var(--rico-text-muted); }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)