import streamlit as st
from ...lib.api import get

PRICE = {  # grobe Schätzer pro 1k Tokens (EUR) – optional, anpassbar
    "openai": {"in": 0.0005, "out": 0.0015},
    "claude": {"in": 0.0008, "out": 0.0020},
    "perplexity": {"in": 0.0006, "out": 0.0012},
}

def estimate(row):
    p = row.get("provider", "auto")
    pin = PRICE.get(p, {}).get("in", 0)
    pout = PRICE.get(p, {}).get("out", 0)
    return round((row.get("input_tokens", 0)/1000.0)*pin + (row.get("output_tokens", 0)/1000.0)*pout, 4)

def render():
    st.subheader("📈 Runs & Telemetry")
    data = get("/v2/core/runs")
    if not isinstance(data, list): 
        st.info("Keine Daten")
        return
    prov = st.multiselect("Provider", sorted({r['provider'] for r in data if 'provider' in r}), default=None)
    rows = [r for r in data if not prov or r.get("provider") in prov]
    for r in rows[:200]:
        cost = estimate(r)
        st.write(f"• {r.get('provider')}/{r.get('model')} – {r.get('duration_s',0)}s – in:{r.get('input_tokens',0)} out:{r.get('output_tokens',0)} – €~{cost}")