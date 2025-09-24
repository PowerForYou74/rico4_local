import streamlit as st
import os
import requests

# Set API base
os.environ['UI_API_BASE'] = 'http://localhost:8000'

def test_api():
    try:
        response = requests.get("http://localhost:8000/v2/core/prompts", timeout=5)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def render():
    st.markdown("## 🛠️ Rico System - Test")
    
    # Test API connection
    st.subheader("API Test")
    if st.button("Test Backend Connection"):
        result = test_api()
        st.json(result)
    
    # Simple tabs
    tabs = st.tabs(["🤖 Agents", "📚 Prompts", "🧠 KB", "📈 Runs", "🔗 Automations", "⚙️ Settings"])
    
    with tabs[0]:
        st.subheader("🤖 Multi-Provider Konsole")
        st.text_area("Eingabe", key="test_input", placeholder="Deine Aufgabe…")
        if st.button("Start", type="primary"):
            st.success("Test erfolgreich!")
    
    with tabs[1]:
        st.subheader("📚 Prompt-Library")
        st.write("Hier werden Prompts verwaltet")
    
    with tabs[2]:
        st.subheader("🧠 Knowledge Base")
        st.write("Hier werden Dateien hochgeladen")
    
    with tabs[3]:
        st.subheader("📈 Runs & Telemetry")
        st.write("Hier werden API-Aufrufe angezeigt")
    
    with tabs[4]:
        st.subheader("🔗 Automations")
        st.write("Hier werden n8n Events ausgelöst")
    
    with tabs[5]:
        st.subheader("⚙️ Settings")
        st.write("Hier werden Einstellungen verwaltet")

if __name__ == "__main__":
    render()
