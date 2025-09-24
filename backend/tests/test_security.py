"""
Security Redaction Tests
"""
import pytest
from unittest.mock import patch
import logging

from utils.security import SecretRedactor, redact_secrets, SecretSafeFormatter, setup_secret_safe_logging


class TestSecretRedactor:
    """Test secret redaction functionality"""
    
    def test_redact_string_with_api_key(self):
        """Test redacting API keys from strings"""
        text = '{"api_key": "sk-1234567890abcdef", "data": "normal"}'
        redacted = SecretRedactor.redact_string(text)
        
        assert "sk-1234567890abcdef" not in redacted
        assert "***REDACTED***" in redacted
        assert "normal" in redacted
    
    def test_redact_string_with_token(self):
        """Test redacting tokens from strings"""
        text = 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'
        redacted = SecretRedactor.redact_string(text)
        
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in redacted
        assert "***REDACTED***" in redacted
    
    def test_redact_string_with_password(self):
        """Test redacting passwords from strings"""
        text = 'password=secret123&user=admin'
        redacted = SecretRedactor.redact_string(text)
        
        assert "secret123" not in redacted
        assert "***REDACTED***" in redacted
        assert "admin" in redacted
    
    def test_redact_string_no_secrets(self):
        """Test redacting string with no secrets"""
        text = 'This is a normal message with no secrets'
        redacted = SecretRedactor.redact_string(text)
        
        assert redacted == text
    
    def test_redact_dict_with_secrets(self):
        """Test redacting secrets from dictionary"""
        data = {
            "api_key": "sk-1234567890abcdef",
            "normal_data": "value",
            "token": "bearer-token-123",
            "nested": {
                "secret": "hidden-value",
                "public": "visible"
            }
        }
        
        redacted = SecretRedactor.redact_dict(data)
        
        assert redacted["api_key"] == "***REDACTED***"
        assert redacted["normal_data"] == "value"
        assert redacted["token"] == "***REDACTED***"
        assert redacted["nested"]["secret"] == "***REDACTED***"
        assert redacted["nested"]["public"] == "visible"
    
    def test_redact_dict_no_secrets(self):
        """Test redacting dictionary with no secrets"""
        data = {
            "name": "John Doe",
            "age": 30,
            "city": "New York"
        }
        
        redacted = SecretRedactor.redact_dict(data)
        
        assert redacted == data
    
    def test_redact_list_with_secrets(self):
        """Test redacting secrets from list"""
        data = [
            {"api_key": "sk-1234567890abcdef", "name": "test"},
            {"normal": "value", "public": "data"},
            {"token": "secret-token", "id": 123}
        ]
        
        redacted = SecretRedactor.redact_list(data)
        
        assert redacted[0]["api_key"] == "***REDACTED***"
        assert redacted[0]["name"] == "test"
        assert redacted[1]["normal"] == "value"
        assert redacted[2]["token"] == "***REDACTED***"
        assert redacted[2]["id"] == 123
    
    def test_redact_any_string(self):
        """Test redact_any with string"""
        text = 'api_key=sk-1234567890abcdef'
        redacted = SecretRedactor.redact_any(text)
        
        assert "sk-1234567890abcdef" not in redacted
        assert "***REDACTED***" in redacted
    
    def test_redact_any_dict(self):
        """Test redact_any with dictionary"""
        data = {"api_key": "sk-1234567890abcdef", "data": "normal"}
        redacted = SecretRedactor.redact_any(data)
        
        assert redacted["api_key"] == "***REDACTED***"
        assert redacted["data"] == "normal"
    
    def test_redact_any_list(self):
        """Test redact_any with list"""
        data = [{"api_key": "sk-1234567890abcdef"}, {"normal": "value"}]
        redacted = SecretRedactor.redact_any(data)
        
        assert redacted[0]["api_key"] == "***REDACTED***"
        assert redacted[1]["normal"] == "value"
    
    def test_redact_any_other_types(self):
        """Test redact_any with other types"""
        assert SecretRedactor.redact_any(123) == 123
        assert SecretRedactor.redact_any(True) == True
        assert SecretRedactor.redact_any(None) == None


class TestRedactSecretsDecorator:
    """Test redact_secrets decorator"""
    
    def test_decorator_success(self):
        """Test decorator with successful function"""
        @redact_secrets
        def test_function(data):
            return data
        
        result = test_function({"api_key": "sk-1234567890abcdef", "data": "normal"})
        
        assert result["api_key"] == "***REDACTED***"
        assert result["data"] == "normal"
    
    def test_decorator_exception(self):
        """Test decorator with exception"""
        @redact_secrets
        def test_function(data):
            raise ValueError("API key: sk-1234567890abcdef")
        
        with pytest.raises(ValueError) as exc_info:
            test_function({"data": "normal"})
        
        # Exception message should be redacted
        assert "sk-1234567890abcdef" not in str(exc_info.value)
        assert "***REDACTED***" in str(exc_info.value)
    
    def test_decorator_return_value_redaction(self):
        """Test decorator redacts return value"""
        @redact_secrets
        def test_function():
            return {"api_key": "sk-1234567890abcdef", "data": "normal"}
        
        result = test_function()
        
        assert result["api_key"] == "***REDACTED***"
        assert result["data"] == "normal"


class TestSecretSafeFormatter:
    """Test secret-safe log formatter"""
    
    def test_formatter_redacts_secrets(self):
        """Test formatter redacts secrets from log messages"""
        formatter = SecretSafeFormatter('%(message)s')
        
        # Create a log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg='API key: sk-1234567890abcdef',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        
        assert "sk-1234567890abcdef" not in formatted
        assert "***REDACTED***" in formatted
    
    def test_formatter_normal_message(self):
        """Test formatter with normal message"""
        formatter = SecretSafeFormatter('%(message)s')
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg='Normal log message',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        
        assert formatted == "Normal log message"
    
    def test_formatter_with_exception(self):
        """Test formatter with exception"""
        formatter = SecretSafeFormatter('%(message)s')
        
        try:
            raise ValueError("API key: sk-1234567890abcdef")
        except ValueError:
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="",
                lineno=0,
                msg="Error occurred",
                args=(),
                exc_info=True
            )
            
            formatted = formatter.format(record)
            
            assert "sk-1234567890abcdef" not in formatted
            assert "***REDACTED***" in formatted


class TestSetupSecretSafeLogging:
    """Test setup_secret_safe_logging function"""
    
    def test_setup_logging(self):
        """Test setting up secret-safe logging"""
        # Clear existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Setup secret-safe logging
        setup_secret_safe_logging()
        
        # Check that handler was added
        assert len(root_logger.handlers) == 1
        handler = root_logger.handlers[0]
        assert isinstance(handler.formatter, SecretSafeFormatter)
    
    def test_logging_redaction_integration(self):
        """Test logging redaction integration"""
        # Setup secret-safe logging
        setup_secret_safe_logging()
        
        # Create logger
        logger = logging.getLogger("test")
        logger.setLevel(logging.INFO)
        
        # Log message with secret
        with patch('sys.stderr') as mock_stderr:
            logger.info("API key: sk-1234567890abcdef")
            
            # Check that secret was redacted
            call_args = mock_stderr.write.call_args[0][0]
            assert "sk-1234567890abcdef" not in call_args
            assert "***REDACTED***" in call_args


class TestSecretPatterns:
    """Test secret patterns"""
    
    def test_api_key_patterns(self):
        """Test various API key patterns"""
        patterns = [
            'api_key=sk-1234567890abcdef',
            'API_KEY: sk-1234567890abcdef',
            'apikey="sk-1234567890abcdef"',
            'api-key: sk-1234567890abcdef'
        ]
        
        for pattern in patterns:
            redacted = SecretRedactor.redact_string(pattern)
            assert "sk-1234567890abcdef" not in redacted
            assert "***REDACTED***" in redacted
    
    def test_token_patterns(self):
        """Test various token patterns"""
        patterns = [
            'token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9',
            'TOKEN: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9',
            'auth_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"',
            'bearer-token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'
        ]
        
        for pattern in patterns:
            redacted = SecretRedactor.redact_string(pattern)
            assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in redacted
            assert "***REDACTED***" in redacted
    
    def test_password_patterns(self):
        """Test various password patterns"""
        patterns = [
            'password=secret123',
            'PASSWORD: secret123',
            'passwd="secret123"',
            'pass: secret123'
        ]
        
        for pattern in patterns:
            redacted = SecretRedactor.redact_string(pattern)
            assert "secret123" not in redacted
            assert "***REDACTED***" in redacted


class TestSecretKeys:
    """Test secret key detection"""
    
    def test_secret_keys_detection(self):
        """Test detection of secret keys"""
        data = {
            "openai_api_key": "sk-1234567890abcdef",
            "anthropic_api_key": "sk-ant-1234567890abcdef",
            "perplexity_api_key": "pplx-1234567890abcdef",
            "n8n_api_key": "n8n-1234567890abcdef",
            "webhook_secret": "webhook-secret-123",
            "normal_data": "value"
        }
        
        redacted = SecretRedactor.redact_dict(data)
        
        # All secret keys should be redacted
        for key in ["openai_api_key", "anthropic_api_key", "perplexity_api_key", 
                   "n8n_api_key", "webhook_secret"]:
            assert redacted[key] == "***REDACTED***"
        
        # Normal data should remain
        assert redacted["normal_data"] == "value"
    
    def test_case_insensitive_keys(self):
        """Test case insensitive key detection"""
        data = {
            "API_KEY": "sk-1234567890abcdef",
            "Token": "bearer-token-123",
            "Secret": "hidden-value"
        }
        
        redacted = SecretRedactor.redact_dict(data)
        
        assert redacted["API_KEY"] == "***REDACTED***"
        assert redacted["Token"] == "***REDACTED***"
        assert redacted["Secret"] == "***REDACTED***"
