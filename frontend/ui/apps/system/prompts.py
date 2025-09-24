import streamlit as st
from ...lib.api import get, post

def render():
    st.subheader("📚 Prompt-Library")
    data = get("/v2/core/prompts")
    st.dataframe(data, use_container_width=True)
    with st.expander("Neu"):
        name = st.text_input("Name")
        role = st.selectbox("Rolle", ["system", "user"])
        tags = st.text_input("Tags (csv)")
        body = st.text_area("Prompt-Text", height=180)
        if st.button("Speichern", disabled=not name or not body):
            from ...lib.api import post_form
            post_form("/v2/core/prompts", files={"name": (None, name), "role": (None, role), "tags": (None, tags), "body": (None, body)})
            st.experimental_rerun()
    
    st.markdown("#### Versionen")
    if data and isinstance(data, list):
        for p in data:
            vids = get(f"/v2/core/prompts/{p['id']}/versions")
            with st.expander(f"{p['name']} ({p['role']}) – {len(vids)} Version(en)"):
                for v in vids:
                    st.code(v.get("body", "")[:2000])
