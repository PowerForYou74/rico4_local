import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import app_registry
from ui.components.cards import metric_card

def render():
    st.markdown("## 🐴 Mobile Tierheilpraxis – Übersicht")
    g1 = st.columns(3)
    with g1[0]: metric_card("Aktive Fälle", 12, "laufende Behandlungen", "📁", "ok")
    with g1[1]: metric_card("Termine heute", 5, "nächste 24h", "📅", "info")
    with g1[2]: metric_card("Offene Rechnungen", 3, "fällig < 14 Tage", "🧾", "warn")

    st.markdown("### 🔧 Schnellstart")
    c = st.columns(3)
    with c[0]: st.button("📅 Termin anlegen", use_container_width=True)
    with c[1]: st.button("🧾 Rechnung erstellen", use_container_width=True)
    with c[2]: st.button("💡 Therapieprotokoll", use_container_width=True)

app_registry.register(app_registry.AppMeta(
    key="tierheilpraxis", name="Tierheilpraxis", icon="🐴", render=render, category="Business"
))
