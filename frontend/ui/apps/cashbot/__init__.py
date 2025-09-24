import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import app_registry
from ui.components.cards import metric_card

def render():
    st.markdown("## 💰 Cashbot – Liquidität & KPIs")
    g = st.columns(3)
    with g[0]: metric_card("Umsatz (Monat)", "€ 12.400", "Vorperiode +8%", "📈", "ok")
    with g[1]: metric_card("Liquidität (30d)", "€ 8.100", "Prognose", "💧", "info")
    with g[2]: metric_card("Außenstände", "€ 1.250", "überfällig 2", "⏳", "warn")
    st.markdown("### Verlauf")
    st.line_chart([3,4,2,5,4,6])

app_registry.register(app_registry.AppMeta(
    key="cashbot", name="Cashbot", icon="💰", render=render, category="Finance"
))
