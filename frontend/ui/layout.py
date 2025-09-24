"""Rico 4.0 Layout Components - Header, Sidebar, Grid-System"""
import streamlit as st
from typing import Optional, Any, Callable

def app_header(title: str = "Rico 4.0", subtitle: str = "Das modulare Regenerationssystem für Pferd · Hund · Exoten", reachable: bool = True):
    """Haupt-Header mit Backend-Status Badge"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"""
        <h1 style="
            color: var(--rico-brand); 
            margin: 0; 
            font-size: 2.2rem;
            font-weight: 700;
            line-height: 1.2;
        ">
            🐾 {title}
        </h1>
        <p style="
            color: var(--rico-text-muted); 
            margin: var(--rico-space-sm) 0 0 0; 
            font-style: italic;
            font-size: 1.1rem;
            line-height: 1.4;
        ">
            {subtitle}
        </p>
        """, unsafe_allow_html=True)
    
    with col2:
        status_color = "var(--rico-status-ok)" if reachable else "var(--rico-status-error)"
        status_text = "Backend erreichbar" if reachable else "Backend offline"
        status_icon = "🟢" if reachable else "🔴"
        
        st.markdown(f"""
        <div style="text-align: right; padding-top: var(--rico-space-lg);">
            <span style="
                background-color: {status_color}; 
                color: white; 
                padding: var(--rico-space-sm) var(--rico-space-lg); 
                border-radius: 20px; 
                font-size: 0.8rem;
                font-weight: 600;
                box-shadow: var(--rico-shadow-sm);
                display: inline-block;
            ">
                {status_icon} {status_text}
            </span>
        </div>
        """, unsafe_allow_html=True)

def sidebar_panel(title: str, content_func: Callable, expanded: bool = True, help_text: Optional[str] = None, icon: str = "⚙️"):
    """Akkordeon-Panel für Sidebar mit verbesserter Gestaltung"""
    with st.expander(f"{icon} {title}", expanded=expanded):
        if help_text:
            st.caption(help_text)
        content_func()

def status_chip(text: str, status: str = "neutral", show_icon: bool = True):
    """Status-Chip mit Farbe und verbesserter Gestaltung"""
    from .theme import get_status_color
    
    color = get_status_color(status)
    icon_map = {
        'ok': '✅', 'success': '✅',
        'warning': '⚠️', 'warn': '⚠️', 
        'error': '❌', 'danger': '❌',
        'info': 'ℹ️', 'neutral': '⚪'
    }
    
    icon = icon_map.get(status, '⚪') if show_icon else ''
    
    st.markdown(f"""
    <span style="
        background-color: {color}; 
        color: white; 
        padding: var(--rico-space-xs) var(--rico-space-sm); 
        border-radius: var(--rico-radius-sm); 
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        margin: var(--rico-space-xs);
        box-shadow: var(--rico-shadow-sm);
    ">
        {icon} {text}
    </span>
    """, unsafe_allow_html=True)

def info_card(title: str, content: Any, status: str = "neutral"):
    """Info-Karte mit Status-Farbe und verbesserter Gestaltung"""
    from .theme import get_status_color
    
    border_color = get_status_color(status)
    
    st.markdown(f"""
    <div style="
        border-left: 4px solid {border_color};
        background-color: var(--rico-surface);
        padding: var(--rico-space-lg);
        border-radius: var(--rico-radius-md);
        margin: var(--rico-space-sm) 0;
        box-shadow: var(--rico-shadow-sm);
        border: 1px solid var(--rico-border);
    ">
        <h4 style="
            margin: 0 0 var(--rico-space-sm) 0; 
            color: var(--rico-text);
            font-size: 1rem;
            font-weight: 600;
        ">{title}</h4>
        <div style="color: var(--rico-text-muted); line-height: 1.5;">{content}</div>
    </div>
    """, unsafe_allow_html=True)

def create_sidebar_layout():
    """Erstellt die komplette Sidebar-Struktur mit Akkordeon-Panels"""
    with st.sidebar:
        st.markdown("---")
        
        # Health Panel
        sidebar_panel(
            title="System-Status", 
            content_func=lambda: st.write("Health-Check wird geladen..."),
            expanded=True,
            icon="🚦"
        )
        
        st.markdown("---")
        
        # Autopilot Panel
        sidebar_panel(
            title="Autopilot", 
            content_func=lambda: st.write("Autopilot-Funktionen..."),
            expanded=False,
            icon="🤖"
        )
        
        st.markdown("---")
        
        # Task Monitor Panel
        sidebar_panel(
            title="Task-Monitor", 
            content_func=lambda: st.write("Task-Monitoring..."),
            expanded=False,
            icon="📊"
        )
        
        st.markdown("---")
        
        # Export Panel
        sidebar_panel(
            title="Exporte", 
            content_func=lambda: st.write("Export-Funktionen..."),
            expanded=False,
            icon="📤"
        )
        
        st.markdown("---")
        
        # n8n Panel (optional)
        import os
        if os.getenv("N8N_ENABLED", "false").lower() == "true":
            sidebar_panel(
                title="n8n Integration", 
                content_func=lambda: st.write("n8n-Webhooks..."),
                expanded=False,
                icon="🔗"
            )
            st.markdown("---")

def grid_container(columns: int = 2, gap: str = "var(--rico-space-lg)"):
    """Erstellt ein Grid-Container mit CSS Grid"""
    return st.columns(columns)
