import streamlit as st
from ...lib.api import get, post_form

def render():
    st.subheader("🧠 Knowledge Base")
    files = get("/v2/core/kb/files")
    st.dataframe(files, use_container_width=True)

    up = st.file_uploader("Datei hochladen (PDF/TXT)", type=["pdf", "txt"])
    if up and st.button("Hochladen"):
        post_form("/v2/core/kb/upload", files={"f": (up.name, up.getvalue())})
        st.success("Upload gestartet")
        st.experimental_rerun()

    st.markdown("### 🔎 Suche")
    q = st.text_input("Begriff")
    top = st.slider("Top", 1, 10, 5)
    if q.strip():
        hits = get("/v2/core/kb/search", params={"q": q, "top": top})
        for h in hits:
            st.markdown(f"**{h['file']}** · Chunk {h['chunk_id']}")
            st.code(h['snippet'])