"""Toast Notification System 2.0 - Deutsche Fehlermeldungen mit Redaction"""
import streamlit as st
from typing import Optional, Any

# Erweiterte Fehler-Mappings mit deutschen Kurztexten
ERROR_MAPPING = {
    'auth': 'Authentifizierung fehlgeschlagen 🔐',
    'rate_limit': 'Rate-Limit erreicht, versuche in wenigen Minuten erneut ⏰',
    'server': 'Server nicht erreichbar, prüfe Backend-Status 🚨', 
    'timeout': 'Zeitüberschreitung - Request dauerte zu lange ⏳',
    'validation': 'Eingabe-Validierung fehlgeschlagen ❌',
    'unknown': 'Unbekannter Fehler aufgetreten 🤔',
    'network': 'Netzwerkfehler - Verbindung unterbrochen 🌐',
    'api_error': 'API-Fehler - Provider antwortet nicht korrekt 🔌',
    'quota_exceeded': 'Quota überschritten - Limit erreicht 📊',
    'model_unavailable': 'Model nicht verfügbar - Provider überlastet 🤖'
}

def _redact_secrets(text: str) -> str:
    """Redaktion: Entfernt Secrets aus Text"""
    import re
    
    # Pattern für häufige Secret-Formate
    patterns = [
        r'(?i)(api[_-]?key|token|secret|password|webhook)[\s=:]+[^\s\n]+',
        r'(?i)(sk-|pk_|ghp_|gho_)[a-zA-Z0-9]{20,}',
        r'(?i)https?://[^\s]+webhook[^\s]+',
        r'(?i)Bearer\s+[a-zA-Z0-9._-]+',
    ]
    
    for pattern in patterns:
        text = re.sub(pattern, r'\1 [REDACTED]', text)
    
    return text

def _contains_secrets(text: str) -> bool:
    """Prüft ob Text Secrets enthält"""
    secret_indicators = [
        'key', 'token', 'secret', 'password', 'api_key', 'webhook',
        'bearer', 'authorization', 'sk-', 'pk_', 'ghp_', 'gho_'
    ]
    text_lower = text.lower()
    return any(indicator in text_lower for indicator in secret_indicators)

def _create_message_safe(message: Any) -> str:
    """Erstellt sichere Nachricht ohne Secrets"""
    if isinstance(message, str):
        if _contains_secrets(message):
            return _redact_secrets(message)
        return message
    elif isinstance(message, dict):
        # Dict zu String konvertieren, aber Secrets redactieren
        import json
        try:
            json_str = json.dumps(message, ensure_ascii=False)
            if _contains_secrets(json_str):
                return _redact_secrets(json_str)
            return json_str
        except:
            return "[Komplexe Daten - Details ausgeblendet]"
    else:
        return str(message)

def show_success(message: str, icon: str = "✅"):
    """Erfolg-Toast mit verbesserter Gestaltung"""
    safe_message = _create_message_safe(message)
    st.success(f"{icon} {safe_message}")

def show_error(error_type: str, details: Optional[str] = None, show_details: bool = False):
    """Fehler-Toast mit Mapping und Redaction"""
    base_message = ERROR_MAPPING.get(error_type, ERROR_MAPPING['unknown'])
    
    if show_details and details:
        safe_details = _create_message_safe(details)
        full_message = f"{base_message}\n\nDetails: {safe_details}"
    else:
        full_message = base_message
    
    st.error(full_message)

def show_warning(message: str, icon: str = "⚠️"):
    """Warnung-Toast mit verbesserter Gestaltung"""
    safe_message = _create_message_safe(message)
    st.warning(f"{icon} {safe_message}")

def show_info(message: str, icon: str = "ℹ️"):
    """Info-Toast mit verbesserter Gestaltung"""
    safe_message = _create_message_safe(message)
    st.info(f"{icon} {safe_message}")

def show_toast(message_type: str, message: str, error_type: Optional[str] = None, show_details: bool = False):
    """Universal-Toast-Funktion"""
    if message_type == "success":
        show_success(message)
    elif message_type == "error":
        show_error(error_type or "unknown", message, show_details)
    elif message_type == "warning":
        show_warning(message)
    elif message_type == "info":
        show_info(message)
    else:
        show_info(message)  # Fallback

def get_error_message(error_type: str) -> str:
    """Gibt deutsche Fehlermeldung für Typ zurück"""
    return ERROR_MAPPING.get(error_type, ERROR_MAPPING['unknown'])
