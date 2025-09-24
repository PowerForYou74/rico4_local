import json
from backend.app.services.providers.claude_client import ClaudeClient

class FakeResp:
    def __init__(self, code, data): 
        self.status_code = code
        self._data = data
    def json(self): 
        return self._data

def test_claude_uses_x_api_key_and_version(monkeypatch):
    """Test dass Claude nur x-api-key und anthropic-version nutzt, nicht Authorization: Bearer"""
    captured = {}
    
    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers or {}
        return FakeResp(200, {
            "content": [{"text": "ok"}], 
            "usage": {"input_tokens": 5, "output_tokens": 3}, 
            "stop_reason": "stop"
        })
    
    monkeypatch.setattr("requests.post", fake_post)

    c = ClaudeClient("KEY-123", "claude-3-7-sonnet-20250219", 2, 0)
    r = c.generate([{"role": "user", "content": "hi"}])
    
    h = captured["headers"]
    assert captured["url"].endswith("/v1/messages")
    assert "x-api-key" in h and h["x-api-key"] == "KEY-123"
    assert "anthropic-version" in h and h["anthropic-version"] == "2023-06-01"
    assert "Authorization" not in h
    assert r["content"] == "ok"
    assert r["provider"] == "claude"

def test_claude_auth_401_error_mapping(monkeypatch):
    """Test dass 401-Fehler korrekt als auth-Fehler gemappt werden"""
    monkeypatch.setattr("requests.post", lambda *a, **k: FakeResp(401, {}))
    c = ClaudeClient("K", "claude-3-7-sonnet-20250219", 2, 0)
    r = c.generate([{"role": "user", "content": "x"}])
    assert r["error_type"] == "auth"
    assert r["http_status"] == 401
    assert r["provider"] == "claude"

def test_claude_rate_limit_429_error_mapping(monkeypatch):
    """Test dass 429-Fehler korrekt als rate_limit-Fehler gemappt werden"""
    monkeypatch.setattr("requests.post", lambda *a, **k: FakeResp(429, {}))
    c = ClaudeClient("K", "claude-3-7-sonnet-20250219", 2, 0)
    r = c.generate([{"role": "user", "content": "x"}])
    assert r["error_type"] == "rate_limit"
    assert r["http_status"] == 429
    assert r["provider"] == "claude"

def test_claude_server_500_error_mapping(monkeypatch):
    """Test dass 5xx-Fehler korrekt als server-Fehler gemappt werden"""
    monkeypatch.setattr("requests.post", lambda *a, **k: FakeResp(500, {}))
    c = ClaudeClient("K", "claude-3-7-sonnet-20250219", 2, 0)
    r = c.generate([{"role": "user", "content": "x"}])
    assert r["error_type"] == "server"
    assert r["http_status"] == 500
    assert r["provider"] == "claude"

def test_claude_timeout_handling(monkeypatch):
    """Test dass Timeout-Exceptions korrekt behandelt werden"""
    import requests
    monkeypatch.setattr("requests.post", lambda *a, **k: (_ for _ in ()).throw(requests.exceptions.Timeout()))
    c = ClaudeClient("K", "claude-3-7-sonnet-20250219", 2, 0)
    r = c.generate([{"role": "user", "content": "x"}])
    assert r["error_type"] == "timeout"
    assert r["provider"] == "claude"
