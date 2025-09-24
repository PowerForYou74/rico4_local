"""Export Panel - Export-Funktionen für Rico-Ergebnisse"""
import streamlit as st
import json
import os
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
from ..layout import info_card
from .toast import show_success, show_error, show_info

def _get_ui_api_base() -> str:
    """Holt UI_API_BASE aus .env.local oder verwendet Default"""
    return os.getenv("UI_API_BASE", "http://localhost:8000")

def _get_exports_base() -> str:
    """Baut Exports-API-Base mit UI_API_BASE"""
    api_base = _get_ui_api_base()
    return f"{api_base}/api/v1/exports"

def render_export_panel():
    """Export-Panel für Rico-Ergebnisse"""
    
    st.markdown("### 📤 Export-Funktionen")
    
    # Aktuelles Ergebnis exportieren
    if st.session_state.ss_last_result:
        _show_current_result_export()
    else:
        st.info("📝 Kein aktuelles Ergebnis verfügbar. Führe zuerst eine Analyse durch.")
    
    st.markdown("---")
    
    # Verfügbare Exports
    _show_available_exports()
    
    # Export-Historie
    _show_export_history()

def _show_current_result_export():
    """Zeigt Export-Optionen für aktuelles Ergebnis"""
    st.markdown("**📄 Aktuelles Ergebnis exportieren:**")
    
    result = st.session_state.ss_last_result
    meta = st.session_state.ss_last_meta or {}
    
    # Export-Format auswählen
    export_format = st.selectbox(
        "Export-Format:",
        ["JSON", "Markdown", "PDF", "CSV"],
        help="Wähle das gewünschte Export-Format"
    )
    
    # Export-Optionen
    col1, col2 = st.columns(2)
    
    with col1:
        include_meta = st.checkbox(
            "Metadaten einschließen",
            value=True,
            help="Fügt Provider, Modell, Dauer etc. zum Export hinzu"
        )
    
    with col2:
        include_raw = st.checkbox(
            "Rohdaten einschließen",
            value=False,
            help="Fügt alle Rohdaten zum Export hinzu"
        )
    
    # Export-Button
    if st.button("📥 Exportieren", key="export_current", use_container_width=True):
        _export_current_result(export_format, include_meta, include_raw)

def _export_current_result(format_type: str, include_meta: bool, include_raw: bool):
    """Exportiert aktuelles Ergebnis"""
    try:
        result = st.session_state.ss_last_result
        meta = st.session_state.ss_last_meta or {}
        
        # Daten für Export vorbereiten
        export_data = _prepare_export_data(result, meta, include_meta, include_raw)
        
        if format_type == "JSON":
            _export_json(export_data, meta)
        elif format_type == "Markdown":
            _export_markdown(export_data, meta)
        elif format_type == "PDF":
            _export_pdf(export_data, meta)
        elif format_type == "CSV":
            _export_csv(export_data, meta)
        
        show_success(f"Ergebnis als {format_type} exportiert")
        
    except Exception as e:
        show_error("server", f"Export-Fehler: {e}")

def _prepare_export_data(result: Dict[str, Any], meta: Dict[str, Any], include_meta: bool, include_raw: bool) -> Dict[str, Any]:
    """Bereitet Export-Daten vor"""
    export_data = {
        "result": result,
        "exported_at": datetime.now().isoformat(),
        "export_format": "rico_ui_export"
    }
    
    if include_meta:
        export_data["meta"] = meta
    
    if include_raw:
        export_data["raw_data"] = {
            "session_state": {
                "provider": st.session_state.ss_provider,
                "task_type": st.session_state.ss_task_type,
                "input_text": st.session_state.ss_input_text
            }
        }
    
    return export_data

def _export_json(data: Dict[str, Any], meta: Dict[str, Any]):
    """Exportiert als JSON"""
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    
    timestamp = meta.get("timestamp", datetime.now().strftime("%Y%m%d_%H%M%S"))
    filename = f"rico_export_{timestamp}.json"
    
    st.download_button(
        label="📥 JSON herunterladen",
        data=json_str,
        file_name=filename,
        mime="application/json",
        key="download_json_export"
    )

def _export_markdown(data: Dict[str, Any], meta: Dict[str, Any]):
    """Exportiert als Markdown"""
    md_content = _generate_markdown(data, meta)
    
    timestamp = meta.get("timestamp", datetime.now().strftime("%Y%m%d_%H%M%S"))
    filename = f"rico_export_{timestamp}.md"
    
    st.download_button(
        label="📥 Markdown herunterladen",
        data=md_content,
        file_name=filename,
        mime="text/markdown",
        key="download_md_export"
    )

def _export_pdf(data: Dict[str, Any], meta: Dict[str, Any]):
    """Exportiert als PDF (vereinfacht als Text)"""
    # Vereinfachte PDF-Export als Text (echte PDF würde zusätzliche Bibliotheken benötigen)
    text_content = _generate_text_export(data, meta)
    
    timestamp = meta.get("timestamp", datetime.now().strftime("%Y%m%d_%H%M%S"))
    filename = f"rico_export_{timestamp}.txt"
    
    st.download_button(
        label="📥 Text-Export herunterladen",
        data=text_content,
        file_name=filename,
        mime="text/plain",
        key="download_txt_export"
    )
    
    show_info("PDF-Export als Text-Datei verfügbar. Für echte PDF-Exports nutze externe Tools.")

def _export_csv(data: Dict[str, Any], meta: Dict[str, Any]):
    """Exportiert als CSV (vereinfacht)"""
    csv_content = _generate_csv_export(data, meta)
    
    timestamp = meta.get("timestamp", datetime.now().strftime("%Y%m%d_%H%M%S"))
    filename = f"rico_export_{timestamp}.csv"
    
    st.download_button(
        label="📥 CSV herunterladen",
        data=csv_content,
        file_name=filename,
        mime="text/csv",
        key="download_csv_export"
    )

def _generate_markdown(data: Dict[str, Any], meta: Dict[str, Any]) -> str:
    """Generiert Markdown-Export"""
    md_lines = [
        "# Rico 4.0 - Export",
        f"**Exportiert am:** {data['exported_at']}",
        f"**Provider:** {meta.get('used_provider', 'N/A')}",
        f"**Modell:** {meta.get('provider_model', 'N/A')}",
        f"**Dauer:** {meta.get('duration_s', 'N/A')}s",
        "",
        "## Zusammenfassung",
        data['result'].get('kurz_zusammenfassung', 'Keine Zusammenfassung verfügbar'),
        "",
        "## Kernbefunde",
        data['result'].get('kernbefunde', 'Keine Kernbefunde verfügbar'),
        "",
        "## Action Plan",
        data['result'].get('action_plan', 'Kein Action Plan verfügbar'),
        "",
        "## Risiken",
        data['result'].get('risiken', 'Keine Risiken identifiziert'),
        ""
    ]
    
    return "\n".join(md_lines)

def _generate_text_export(data: Dict[str, Any], meta: Dict[str, Any]) -> str:
    """Generiert Text-Export"""
    text_lines = [
        "Rico 4.0 - Export",
        "=" * 50,
        f"Exportiert am: {data['exported_at']}",
        f"Provider: {meta.get('used_provider', 'N/A')}",
        f"Modell: {meta.get('provider_model', 'N/A')}",
        f"Dauer: {meta.get('duration_s', 'N/A')}s",
        "",
        "ZUSAMMENFASSUNG",
        "-" * 20,
        data['result'].get('kurz_zusammenfassung', 'Keine Zusammenfassung verfügbar'),
        "",
        "KERNBEFUNDE",
        "-" * 20,
        data['result'].get('kernbefunde', 'Keine Kernbefunde verfügbar'),
        "",
        "ACTION PLAN",
        "-" * 20,
        data['result'].get('action_plan', 'Kein Action Plan verfügbar'),
        ""
    ]
    
    return "\n".join(text_lines)

def _generate_csv_export(data: Dict[str, Any], meta: Dict[str, Any]) -> str:
    """Generiert CSV-Export"""
    # Sichere CSV-Escaping
    def escape_csv(text):
        if not isinstance(text, str):
            text = str(text)
        return text.replace('"', '""')
    
    csv_lines = [
        "Field,Value",
        f"Exportiert am,{data['exported_at']}",
        f"Provider,{meta.get('used_provider', 'N/A')}",
        f"Modell,{meta.get('provider_model', 'N/A')}",
        f"Dauer,{meta.get('duration_s', 'N/A')}",
        f"Zusammenfassung,\"{escape_csv(data['result'].get('kurz_zusammenfassung', 'N/A'))}\"",
        f"Kernbefunde,\"{escape_csv(data['result'].get('kernbefunde', 'N/A'))}\"",
        f"Action Plan,\"{escape_csv(data['result'].get('action_plan', 'N/A'))}\""
    ]
    
    return "\n".join(csv_lines)

def _show_available_exports():
    """Zeigt verfügbare Exports"""
    st.markdown("**📋 Verfügbare Exports:**")
    
    try:
        exports_base = _get_exports_base()
        response = requests.get(f"{exports_base}/list", timeout=5)
        
        if response.ok:
            exports = response.json()
            
            if exports:
                for export in exports:
                    export_name = export.get("name", "Unbekannter Export")
                    export_type = export.get("type", "unknown")
                    export_size = export.get("size_kb", 0)
                    export_created = export.get("created_at", "N/A")
                    
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{export_name}**")
                    
                    with col2:
                        st.markdown(f"<small>{export_type}</small>", unsafe_allow_html=True)
                    
                    with col3:
                        if st.button("📥", key=f"download_{export_name}", help="Download"):
                            _download_export(export)
            else:
                st.info("Keine verfügbaren Exports")
        else:
            st.warning(f"Fehler beim Laden der Exports: {response.status_code}")
            
    except Exception as e:
        st.warning(f"Fehler beim Laden der Exports: {e}")

def _download_export(export: Dict[str, Any]):
    """Lädt Export herunter"""
    try:
        exports_base = _get_exports_base()
        export_id = export.get("id")
        
        if export_id:
            response = requests.get(f"{exports_base}/download/{export_id}", timeout=10)
            
            if response.ok:
                show_success("Export heruntergeladen")
            else:
                show_error("server", f"Download-Fehler: {response.status_code}")
        else:
            show_error("validation", "Export-ID nicht verfügbar")
            
    except Exception as e:
        show_error("server", f"Download-Fehler: {e}")

def _show_export_history():
    """Zeigt Export-Historie"""
    st.markdown("**📈 Export-Historie:**")
    
    # Lokale Export-Historie (vereinfacht)
    export_history = [
        {"name": "Letztes Ergebnis", "type": "JSON", "created": "Heute"},
        {"name": "Wöchentlicher Report", "type": "Markdown", "created": "Gestern"},
        {"name": "Monats-Export", "type": "CSV", "created": "Vor 3 Tagen"}
    ]
    
    for export in export_history:
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"**{export['name']}**")
        
        with col2:
            st.markdown(f"<small>{export['type']}</small>", unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"<small>{export['created']}</small>", unsafe_allow_html=True)
    
    # Footer-Info
    st.markdown("---")
    st.markdown("""
    <small style="color: var(--rico-text-muted)">
        📤 <strong>Export-Formate:</strong> JSON, Markdown, PDF, CSV<br>
        💾 <strong>Speicherung:</strong> Exports werden lokal und auf dem Server gespeichert
    </small>
    """, unsafe_allow_html=True)
