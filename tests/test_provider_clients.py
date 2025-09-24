from backend.app.services.provider_clients import build_provider_client
from backend.app.config import CLAUDE_API_KEY, PPLX_API_KEY

class MockClaudeClient:
    def __init__(self, api_key, model, timeout, retries):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.retries = retries

class MockPerplexityClient:
    def __init__(self, api_key, model, timeout, retries):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.retries = retries

def test_build_claude_client(monkeypatch):
    """Test dass Claude-Client korrekt erstellt wird"""
    monkeypatch.setattr("backend.app.services.provider_clients.ClaudeClient", MockClaudeClient)
    
    client = build_provider_client("claude")
    assert isinstance(client, MockClaudeClient)
    assert client.api_key == CLAUDE_API_KEY
    assert client.model == "claude-3-7-sonnet-20250219"

def test_build_perplexity_client(monkeypatch):
    """Test dass Perplexity-Client korrekt erstellt wird"""
    monkeypatch.setattr("backend.app.services.provider_clients.PerplexityClient", MockPerplexityClient)
    
    client = build_provider_client("perplexity")
    assert isinstance(client, MockPerplexityClient)
    assert client.api_key == PPLX_API_KEY
    assert client.model == "sonar"

def test_build_unknown_provider_raises_error():
    """Test dass unbekannte Provider einen Fehler werfen"""
    try:
        build_provider_client("unknown")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unknown provider: unknown" in str(e)

def test_claude_client_headers_are_isolated():
    """Test dass Claude-Client Header isoliert sind (keine globalen Authorization-Header)"""
    from backend.app.services.providers.claude_client import ClaudeClient
    
    client = ClaudeClient("test-key", "claude-3-7-sonnet-20250219", 30, 1)
    headers = client._headers()
    
    # Claude sollte nur diese Header haben
    assert "x-api-key" in headers
    assert "anthropic-version" in headers
    assert "Content-Type" in headers
    assert "Authorization" not in headers
    assert headers["x-api-key"] == "test-key"
    assert headers["anthropic-version"] == "2023-06-01"

def test_perplexity_client_headers_are_isolated():
    """Test dass Perplexity-Client Header isoliert sind"""
    from backend.app.services.providers.pplx_client import PerplexityClient
    
    client = PerplexityClient("test-key", "sonar", 30, 1)
    headers = client._headers()
    
    # Perplexity sollte nur diese Header haben
    assert "Authorization" in headers
    assert "Content-Type" in headers
    assert "x-api-key" not in headers
    assert "anthropic-version" not in headers
    assert headers["Authorization"] == "Bearer test-key"
