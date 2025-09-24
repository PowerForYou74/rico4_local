import streamlit as st

def metric_card(title:str, value, hint:str="", icon:str="📌", status:str="neutral"):
    color = {"ok":"var(--rico-ok)","warn":"var(--rico-warn)","err":"var(--rico-err)","neutral":"var(--rico-brand)"}\
            .get(status, "var(--rico-brand)")
    st.markdown(f"""
    <div class="rico-card" style="padding:16px">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
        <span style="font-size:1.1rem">{icon}</span>
        <strong style="font-size:1.05rem">{title}</strong>
      </div>
      <div style="font-size:1.8rem;font-weight:700;color:{color};line-height:1">{value}</div>
      <div class="muted" style="margin-top:6px">{hint}</div>
    </div>
    """, unsafe_allow_html=True)
