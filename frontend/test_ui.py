#!/usr/bin/env python3
"""
Rico 4.0 UI Test - Schneller Test der neuen modularen Architektur
"""

def test_imports():
    """Teste alle UI-Module"""
    try:
        print("🧪 Teste UI-Imports...")
        
        # Theme
        from ui.theme import inject_theme, get_status_color
        print("✅ Theme-Module OK")
        
        # Layout
        from ui.layout import app_header, sidebar_panel, status_chip
        print("✅ Layout-Module OK")
        
        # Sections
        from ui.sections.health_panel import render_health_panel
        from ui.sections.provider_controls import render_provider_controls
        from ui.sections.result_tabs import render_result_tabs
        from ui.sections.toast import show_success, show_error
        print("✅ Section-Module OK")
        
        # n8n (optional)
        try:
            from ui.sections.n8n_panel import render_n8n_panel
            print("✅ n8n-Module OK")
        except ImportError as e:
            print(f"⚠️ n8n-Module optional: {e}")
        
        # Haupt-App
        import streamlit_app
        print("✅ Streamlit-App OK")
        
        print("\n🎉 Alle Tests erfolgreich!")
        return True
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False

def test_theme():
    """Teste Theme-Funktionen"""
    try:
        from ui.theme import get_status_color
        
        # Teste Status-Farben
        colors = {
            'ok': get_status_color('ok'),
            'error': get_status_color('error'),
            'warning': get_status_color('warning'),
            'neutral': get_status_color('neutral')
        }
        
        print(f"🎨 Theme-Farben: {colors}")
        return True
        
    except Exception as e:
        print(f"❌ Theme-Fehler: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Rico 4.0 UI Test")
    print("=" * 40)
    
    success = True
    success &= test_imports()
    success &= test_theme()
    
    if success:
        print("\n✅ Alle Tests bestanden!")
        print("🎯 Die neue modulare UI ist einsatzbereit!")
    else:
        print("\n❌ Einige Tests fehlgeschlagen!")
        print("🔧 Bitte prüfe die Fehlermeldungen oben.")
