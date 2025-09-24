"""
Security utilities for secret redaction in logs and exceptions
"""
import re
import logging
from typing import Any, Dict, List, Union
from functools import wraps


class SecretRedactor:
    """Utility class for redacting secrets from logs and data"""
    
    # Common secret patterns
    SECRET_PATTERNS = [
        r'(?i)(api[_-]?key)\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?',
        r'(?i)(token)\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?',
        r'(?i)(secret)\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?',
        r'(?i)(password)\s*[:=]\s*["\']?([a-zA-Z0-9_-]{8,})["\']?',
        r'(?i)(auth[_-]?token)\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?',
        r'(?i)(bearer[_-]?token)\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?',
    ]
    
    # Known secret keys to redact
    SECRET_KEYS = [
        'api_key', 'api-key', 'apikey',
        'token', 'access_token', 'auth_token',
        'secret', 'password', 'passwd',
        'bearer_token', 'bearer-token',
        'openai_api_key', 'anthropic_api_key', 'perplexity_api_key',
        'n8n_api_key', 'webhook_secret',
        'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'PERPLEXITY_API_KEY',
        'N8N_API_KEY', 'SLACK_WEBHOOK_URL'
    ]
    
    @classmethod
    def redact_string(cls, text: str) -> str:
        """Redact secrets from a string"""
        if not isinstance(text, str):
            return text
            
        redacted = text
        
        # Apply pattern-based redaction
        for pattern in cls.SECRET_PATTERNS:
            redacted = re.sub(pattern, r'\1=***REDACTED***', redacted, flags=re.IGNORECASE)
        
        return redacted
    
    @classmethod
    def redact_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact secrets from a dictionary"""
        if not isinstance(data, dict):
            return data
            
        redacted = {}
        for key, value in data.items():
            # Check if key contains secret indicators
            key_lower = key.lower()
            is_secret_key = any(secret in key_lower for secret in cls.SECRET_KEYS)
            
            if is_secret_key:
                redacted[key] = "***REDACTED***"
            elif isinstance(value, str):
                redacted[key] = cls.redact_string(value)
            elif isinstance(value, dict):
                redacted[key] = cls.redact_dict(value)
            elif isinstance(value, list):
                redacted[key] = cls.redact_list(value)
            else:
                redacted[key] = value
                
        return redacted
    
    @classmethod
    def redact_list(cls, data: List[Any]) -> List[Any]:
        """Redact secrets from a list"""
        if not isinstance(data, list):
            return data
            
        return [cls.redact_dict(item) if isinstance(item, dict) else 
                cls.redact_string(item) if isinstance(item, str) else item 
                for item in data]
    
    @classmethod
    def redact_any(cls, data: Any) -> Any:
        """Redact secrets from any data type"""
        if isinstance(data, str):
            return cls.redact_string(data)
        elif isinstance(data, dict):
            return cls.redact_dict(data)
        elif isinstance(data, list):
            return cls.redact_list(data)
        else:
            return data


def redact_secrets(func):
    """Decorator to automatically redact secrets from function arguments and return values"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Redact input arguments
        redacted_args = [SecretRedactor.redact_any(arg) for arg in args]
        redacted_kwargs = SecretRedactor.redact_dict(kwargs)
        
        try:
            result = func(*args, **kwargs)
            return SecretRedactor.redact_any(result)
        except Exception as e:
            # Redact exception message
            if hasattr(e, 'args') and e.args:
                redacted_args = [SecretRedactor.redact_any(arg) for arg in e.args]
                e.args = tuple(redacted_args)
            raise
    return wrapper


class SecretSafeFormatter(logging.Formatter):
    """Custom log formatter that redacts secrets"""
    
    def format(self, record):
        # Get the original formatted message
        msg = super().format(record)
        
        # Redact secrets from the message
        return SecretRedactor.redact_string(msg)


def setup_secret_safe_logging():
    """Setup logging with secret redaction"""
    # Get root logger
    root_logger = logging.getLogger()
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create new handler with secret-safe formatter
    handler = logging.StreamHandler()
    formatter = SecretSafeFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Add handler to root logger
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


# Exception handler for FastAPI
def create_secret_safe_exception_handler():
    """Create exception handler that redacts secrets"""
    def exception_handler(request, exc):
        # Redact the exception details
        redacted_exc = SecretRedactor.redact_any(str(exc))
        
        return {
            "error": "Internal server error",
            "details": redacted_exc,
            "type": type(exc).__name__
        }
    
    return exception_handler
