import streamlit as st
import time
import json
from ...lib.api import post, get

def _fetch_prompts():
    try: 
        return get("/v2/core/prompts")
    except Exception: 
        return []

def _fetch_versions(pid: int):
    try: 
        return get(f"/v2/core/prompts/{pid}/versions")
    except Exception: 
        return []

def _kb_search(q: str, top: int = 5):
    try: 
        return get("/v2/core/kb/search", params={"q": q, "top": top})
    except Exception: 
        return []

def render():
    st.subheader("🤖 Multi-Provider Konsole")

    with st.expander("Kontext & Optionen", expanded=True):
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            prompts = _fetch_prompts()
            pmap = {f"{p['name']} ({p['role']})": p["id"] for p in prompts} if isinstance(prompts, list) else {}
            psel = st.selectbox("Prompt-Vorlage", ["(keine)"] + list(pmap.keys()))
            vsel = None
            if psel != "(keine)":
                vids = _fetch_versions(pmap[psel]) or []
                vlabels = [f"v{v['id']}" for v in vids]
                vsel = st.selectbox("Version", vlabels, index=0 if vlabels else None) if vlabels else None
        with c2:
            use_kb = st.checkbox("KB-Kontext verwenden", value=False, help="Top-Treffer als Kontext injizieren")
            kb_query = st.text_input("KB-Suche (bei aktiviertem Kontext)", value="", placeholder="Suchbegriff …", disabled=not use_kb)
            kb_top = st.slider("KB-Top-Chunks", 1, 10, 3, disabled=not use_kb)
        with c3:
            provider = st.selectbox("Provider", ["auto", "openai", "claude", "perplexity"])
            stream = st.checkbox("Streaming", value=False)

    txt = st.text_area("Eingabe", key="sys_agents_input", height=180, placeholder="Deine Aufgabe…")

    if st.button("🚀 Start", type="primary", disabled=not txt.strip()):
        # 1) System-Kontext bauen
        system_ctx = ""
        if psel != "(keine)":
            pid = pmap[psel]
            vers = _fetch_versions(pid)
            body = (vers[0]["body"] if vers else "")
            system_ctx += body or ""
        kb_ctx = []
        if use_kb and kb_query.strip():
            kb_hits = _kb_search(kb_query, kb_top)
            for h in kb_hits:
                kb_ctx.append(f"[{h['file']} / chunk {h['chunk_id']}]: {h['snippet']}")
        if kb_ctx:
            system_ctx += ("\n\n---\n# KB-Kontext\n" + "\n\n".join(kb_ctx))

        # 2) v1-Agent call
        t0 = time.time()
        payload = {"input": txt, "provider": provider, "stream": stream}
        if system_ctx.strip():
            payload["system"] = system_ctx[:12000]  # streamlit safety
        res = post("/rico-agent", payload)
        meta = res.get("meta", {}) or {}
        dur = meta.get("duration_s", round(time.time()-t0, 3))

        # 3) Run-Logging (/v2/core/runs)
        try:
            run_body = {
                "provider": meta.get("used_provider", "auto"),
                "model": meta.get("provider_model", "n/a"),
                "input_tokens": int(meta.get("input_tokens") or 0),
                "output_tokens": int(meta.get("output_tokens") or 0),
                "duration_s": float(dur),
                "status": "success" if "error_type" not in res else "error"
            }
            post("/v2/core/runs", run_body)
        except Exception: 
            pass

        # 4) Anzeige + n8n
        st.success(f"Fertig in {dur:0.1f}s – {meta.get('used_provider','?')} / {meta.get('provider_model','?')}")
        st.session_state.ss_last_result = res
        st.session_state.ss_last_meta = meta
        st.json(res)

        # n8n Integration
        try:
            from integrations import n8n_client
            if n8n_client._enabled() and st.button("🔗 Letzten Run an n8n senden"):
                st.write(n8n_client.send("CRM Lead", {"result": res, "meta": meta}))
        except ImportError:
            st.info("n8n-Integration nicht verfügbar")