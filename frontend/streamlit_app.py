# frontend/streamlit_app.py
import os
import json
from typing import Any, Dict, List, Optional, Tuple

import requests
import streamlit as st

# ─────────────────────────  Page Config  ─────────────────────────
st.set_page_config(
    page_title="Rico 4.0 – Starter UI",
    page_icon="🧠",
    layout="wide",
)
BASE = os.getenv("RICO_API_BASE", "http://127.0.0.1:8000/api/v1")

# ─────────────────────────  CSS  ─────────────────────────
st.markdown("""
<style>
/* Page padding reduzieren */
.block-container{padding-top:1.2rem; padding-bottom:2rem;}

/* Hero */
.hero{
  background: radial-gradient(1200px 600px at 10% -20%, #1e2a52 0%, transparent 60%),
              linear-gradient(135deg,#111631 0%,#0b1020 65%);
  border-radius: 18px; padding: 24px 28px; position: relative; overflow: hidden;
  box-shadow: 0 8px 40px rgba(0,0,0,.35);
}
.hero h1{margin:0; font-size: 1.6rem; letter-spacing:.2px}
.hero p{opacity:.9; margin:.25rem 0 0}
.hero .badge{display:inline-block; padding:2px 10px; border-radius:999px;
  background:#2b355f; color:#cdd3ff; font-size:.75rem; margin-left:.5rem}

/* Glass Card */
.card{
  background: rgba(255,255,255,.03);
  border: 1px solid rgba(255,255,255,.06);
  border-radius: 16px; padding: 16px 18px; margin-top: 8px;
  box-shadow: 0 6px 24px rgba(0,0,0,.25); backdrop-filter: blur(6px);
}

/* Section header */
.section-title{font-weight:700; letter-spacing:.2px; margin-bottom:.35rem}

/* Small status */
.badge-ok{color:#87f59b; background:#143224; border-radius:8px; padding:2px 8px; font-size:.78rem;}
.badge-fail{color:#ffb3b3; background:#3a1d1d; border-radius:8px; padding:2px 8px; font-size:.78rem;}

/* Inputs */
textarea{font-size:0.95rem}

/* Make expander nicer */
.stExpander{border-radius:12px; overflow:hidden; border:1px solid rgba(255,255,255,.07)}
/* Buttons full width in columns */
.stButton>button{border-radius:12px; padding:.6rem 1rem; font-weight:600}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────  Helpers  ─────────────────────────
def ping_backend() -> Tuple[bool, str]:
    try:
        r = requests.get(BASE.replace("/api/v1", "/"), timeout=3)
        if r.ok: return True, "Backend erreichbar"
        return False, f"Antwort {r.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"Keine Verbindung: {e}"

def post_task(prompt: str, task_type: str="analysis", timeout: int=30) -> requests.Response:
    target = f"{BASE}/task"
    payload = {"prompt": prompt, "task_type": task_type}
    return requests.post(target, headers={"accept":"application/json","Content-Type":"application/json"},
                         json=payload, timeout=timeout)

def list_block(items: Optional[List[Any]], icon: str="•"):
    if not items: st.markdown("<span style='opacity:.6'>keine Einträge</span>", unsafe_allow_html=True); return
    for it in items: st.markdown(f"{icon} {it}")

def render_result(data: Dict[str, Any]):
    ok = data.get("ok", False)
    result = data.get("result") or {}
    status = f"<span class='badge-ok'>✓ ok</span>" if ok else f"<span class='badge-fail'>x failed</span>"
    st.markdown(f"<div class='card'><div class='section-title'>Status</div>{status}</div>", unsafe_allow_html=True)

    # Tabs
    tab_ans, tab_raw, tab_hdr, tab_curl, tab_hist = st.tabs(
        ["Antwort", "Rohdaten", "Header", "cURL", "Verlauf"]
    )

    with tab_ans:
        c1, c2 = st.columns([2,2])
        with c1:
            st.markdown("<div class='card'><div class='section-title'>📝 Kurz­zusammenfassung</div>", unsafe_allow_html=True)
            st.write(result.get("kurz_zusammenfassung") or "_(leer)_")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='card'><div class='section-title'>🛠️ Action Plan</div>", unsafe_allow_html=True)
            list_block(result.get("action_plan"), "◽️")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='card'><div class='section-title'>⚠️ Risiken & Annahmen</div>", unsafe_allow_html=True)
            list_block(result.get("risiken"), "⚠️")
            st.markdown("</div>", unsafe_allow_html=True)

        with c2:
            st.markdown("<div class='card'><div class='section-title'>🔎 Kernergebnisse</div>", unsafe_allow_html=True)
            list_block(result.get("kernergebnisse"), "▪️")
            st.markdown("</div>", unsafe_allow_html=True)

            radar = (result.get("cashflow_radar") or {}).get("idee") or "_(keine Idee)_"
            st.markdown("<div class='card'><div class='section-title'>💰 Cashflow-Radar</div>", unsafe_allow_html=True)
            st.write(radar)
            st.markdown("</div>", unsafe_allow_html=True)

            roles = result.get("team_rollen") or {}
            st.markdown("<div class='card'><div class='section-title'>👥 Team-Rollen</div>", unsafe_allow_html=True)
            colr1, colr2 = st.columns(2)
            colr1.metric("OpenAI", "aktiv" if roles.get("openai") else "aus")
            colr2.metric("Claude", "aktiv" if roles.get("claude") else "aus")
            st.markdown("</div>", unsafe_allow_html=True)

    with tab_raw:
        st.json(data)

    with tab_hdr:
        st.caption("Response-Header (vom letzten Request)")
        st.json(st.session_state.get("last_headers") or {})

    with tab_curl:
        # Backslash-sicher bauen (keine Backslashes innerhalb f-Ausdrücken)
        prompt = st.session_state.get("last_prompt","")
        safe = (prompt or "").replace('"','\\"')
        target = f"{BASE}/task"
        lines = [
            "curl -X POST \\",
            f"  '{target}' \\",
            "  -H 'accept: application/json' \\",
            "  -H 'Content-Type: application/json' \\",
            f"  -d '{{\"prompt\": \"{safe}\", \"task_type\": \"analysis\"}}'"
        ]
        st.code("\n".join(lines), language="bash")

    with tab_hist:
        hist = st.session_state.get("history", [])
        if not hist:
            st.caption("Noch keine Einträge.")
        else:
            for i, item in enumerate(hist[::-1][:5], start=1):
                st.markdown(f"**#{i} – Prompt**")
                st.write(item["prompt"])
                with st.expander("Antwort (JSON)"):
                    st.json(item["response"])

# ─────────────────────────  Sidebar / Hero  ─────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Einstellungen")
    ok, msg = ping_backend()
    st.markdown(f"**Backend**: {'✅' if ok else '❌'} {msg}")
    st.caption(BASE)
    st.divider()
    st.markdown("**Beispiele**")
    if st.button("🧪 Cashflow-Idee analysieren", use_container_width=True):
        st.session_state["prefill"] = "Bitte analysiere meine erste Cashflow-Idee."
    if st.button("🧭 Quartalsfokus vorschlagen", use_container_width=True):
        st.session_state["prefill"] = "Was sollte im nächsten Quartal Priorität haben? Bitte Fokusvorschlag."
    if st.button("🧱 Risiken & Maßnahmen", use_container_width=True):
        st.session_state["prefill"] = "Identifiziere Top-Risiken und schlage Gegenmaßnahmen vor."

# Hero
st.markdown("""
<div class="hero">
  <h1>🧠 Rico 4.0 <span class="badge">Starter UI</span></h1>
  <p>Schicke Ziele, Texte oder Ideen an Rico – und erhalte eine klare, strukturierte Auswertung.</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────  Main Input  ─────────────────────────
prefill = st.session_state.pop("prefill", "")
user_prompt = st.text_area(
    "Dein Input an Rico",
    value=prefill,
    height=140,
    placeholder="Beschreibe dein Ziel oder füge Text/Ideen ein…",
)

cols = st.columns([1.2, 3])
send = cols[0].button("📤 An Rico senden", type="primary", use_container_width=True)
with cols[1]:
    st.caption(f"Request-Ziel: {BASE}/task")

# ─────────────────────────  Request  ─────────────────────────
if "history" not in st.session_state: st.session_state["history"] = []

if send:
    if not (user_prompt or "").strip():
        st.warning("Bitte gib zuerst einen Text ein.")
    else:
        with st.spinner("Sende Anfrage …"):
            try:
                r = post_task(user_prompt, "analysis", timeout=30)
                st.session_state["last_headers"] = dict(r.headers)
                st.session_state["last_prompt"]  = user_prompt
            except requests.exceptions.ConnectionError:
                st.error("Keine Verbindung zum Backend. Läuft Uvicorn auf Port 8000?")
                r = None
            except requests.exceptions.Timeout:
                st.error("Timeout – Backend hat zu lange benötigt.")
                r = None
            except Exception as e:
                st.error(f"Unerwarteter Fehler: {e}")
                r = None

        if r is not None:
            if r.ok:
                try:
                    data = r.json()
                except Exception:
                    st.error("Antwort ist kein gültiges JSON.")
                    st.text(r.text)
                else:
                    st.markdown("<div class='card'><span class='section-title'>Antwort von Rico</span></div>",
                                unsafe_allow_html=True)
                    render_result(data)
                    st.session_state["history"].append({"prompt": user_prompt, "response": data})
            else:
                st.error(f"Fehler {r.status_code}")
                st.code(r.text)