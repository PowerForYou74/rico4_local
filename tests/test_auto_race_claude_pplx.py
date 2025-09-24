def test_claude_and_perplexity_headers_are_isolated():
    """Test dass Claude und Perplexity isolierte Header haben"""
    from backend.app.services.providers.claude_client import ClaudeClient
    from backend.app.services.providers.pplx_client import PerplexityClient
    
    # Claude-Client
    claude = ClaudeClient("claude-key", "claude-3-7-sonnet-20250219", 30, 1)
    claude_headers = claude._headers()
    
    # Perplexity-Client  
    pplx = PerplexityClient("pplx-key", "sonar", 30, 1)
    pplx_headers = pplx._headers()
    
    # Claude sollte nur x-api-key und anthropic-version haben
    assert "x-api-key" in claude_headers
    assert "anthropic-version" in claude_headers
    assert "Authorization" not in claude_headers
    assert claude_headers["x-api-key"] == "claude-key"
    assert claude_headers["anthropic-version"] == "2023-06-01"
    
    # Perplexity sollte nur Authorization: Bearer haben
    assert "Authorization" in pplx_headers
    assert "x-api-key" not in pplx_headers
    assert "anthropic-version" not in pplx_headers
    assert pplx_headers["Authorization"] == "Bearer pplx-key"
    
    # Beide sollten Content-Type haben
    assert "Content-Type" in claude_headers
    assert "Content-Type" in pplx_headers

def test_provider_clients_are_created_correctly():
    """Test dass Provider-Clients korrekt erstellt werden"""
    from backend.app.services.provider_clients import build_provider_client
    
    # Test Claude-Client
    claude_client = build_provider_client("claude")
    assert hasattr(claude_client, 'generate')
    assert hasattr(claude_client, '_headers')
    
    # Test Perplexity-Client
    pplx_client = build_provider_client("perplexity")
    assert hasattr(pplx_client, 'generate')
    assert hasattr(pplx_client, '_headers')
    
    # Test dass Header isoliert sind
    claude_headers = claude_client._headers()
    pplx_headers = pplx_client._headers()
    
    # Claude sollte x-api-key haben, Perplexity nicht
    assert "x-api-key" in claude_headers
    assert "x-api-key" not in pplx_headers
    
    # Perplexity sollte Authorization haben, Claude nicht
    assert "Authorization" in pplx_headers
    assert "Authorization" not in claude_headers

def test_unknown_provider_raises_error():
    """Test dass unbekannte Provider einen Fehler werfen"""
    from backend.app.services.provider_clients import build_provider_client
    
    try:
        build_provider_client("unknown")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unknown provider: unknown" in str(e)
