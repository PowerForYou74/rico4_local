import streamlit as st

st.set_page_config(
    page_title="Rico Control Center Test",
    page_icon="🧭",
    layout="wide"
)

st.title("🧭 Rico Control Center")
st.header("Test der App-Funktionalität")

# Test der Registry
try:
    import sys
    sys.path.append('.')
    from app_registry import apps
    
    apps_dict = apps()
    st.success(f"✅ {len(apps_dict)} Apps registriert")
    
    for key, meta in apps_dict.items():
        st.write(f"- {meta.icon} {meta.name} ({meta.category})")
        
except Exception as e:
    st.error(f"❌ Registry-Fehler: {e}")

# Test der UI-Komponenten
st.subheader("UI-Komponenten Test")
try:
    from ui.theme import TOKENS
    st.success("✅ Theme-Tokens geladen")
    st.write(f"Farben: {len(TOKENS['colors'])} definiert")
except Exception as e:
    st.error(f"❌ Theme-Fehler: {e}")

st.subheader("Navigation Test")
col1, col2, col3 = st.columns(3)
with col1:
    st.button("🐴 Tierheilpraxis")
with col2:
    st.button("💰 Cashbot") 
with col3:
    st.button("🧠 Research")

st.info("Wenn du diese Seite siehst, funktioniert die Basis-App!")
