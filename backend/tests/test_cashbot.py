"""
Cashbot Tests
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import json

from main import app
from api.v2.cashbot import ScanRequest, Finding, ScanResult, DispatchRequest


class TestCashbotEndpoints:
    """Test cashbot API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.mark.asyncio
    async def test_create_scan_financial(self, client):
        """Test creating a financial scan"""
        with patch('api.v2.cashbot.get_providers') as mock_get_providers:
            # Mock providers
            mock_provider = AsyncMock()
            mock_provider.generate_response.return_value = MagicMock(
                success=True,
                content="Financial analysis: Found 3 cost savings opportunities worth $50,000 annually.",
                provider="openai",
                model="gpt-3.5-turbo",
                usage={"total_tokens": 100},
                latency_ms=150.0
            )
            mock_provider.close = AsyncMock()
            mock_get_providers.return_value = [mock_provider]
            
            scan_data = {
                "target": "https://example.com/financial-data",
                "scan_type": "financial",
                "priority": "high"
            }
            
            response = client.post("/v2/cashbot/scan", json=scan_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["target"] == scan_data["target"]
            assert data["scan_type"] == "financial"
            assert data["priority"] == "high"
            assert data["status"] == "completed"
            assert len(data["findings"]) > 0
            assert data["summary"] is not None
    
    @pytest.mark.asyncio
    async def test_create_scan_security(self, client):
        """Test creating a security scan"""
        with patch('api.v2.cashbot.get_providers') as mock_get_providers:
            mock_provider = AsyncMock()
            mock_provider.generate_response.return_value = MagicMock(
                success=True,
                content="Security analysis: Found 2 critical vulnerabilities in authentication system.",
                provider="anthropic",
                model="claude-3-sonnet-20240229",
                usage={"input_tokens": 50, "output_tokens": 50},
                latency_ms=200.0
            )
            mock_provider.close = AsyncMock()
            mock_get_providers.return_value = [mock_provider]
            
            scan_data = {
                "target": "https://example.com/security-audit",
                "scan_type": "security",
                "priority": "critical"
            }
            
            response = client.post("/v2/cashbot/scan", json=scan_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["scan_type"] == "security"
            assert data["priority"] == "critical"
            assert data["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_create_scan_compliance(self, client):
        """Test creating a compliance scan"""
        with patch('api.v2.cashbot.get_providers') as mock_get_providers:
            mock_provider = AsyncMock()
            mock_provider.generate_response.return_value = MagicMock(
                success=True,
                content="Compliance analysis: Found 1 GDPR violation in data processing procedures.",
                provider="perplexity",
                model="sonar",
                usage={"total_tokens": 75},
                latency_ms=180.0
            )
            mock_provider.close = AsyncMock()
            mock_get_providers.return_value = [mock_provider]
            
            scan_data = {
                "target": "https://example.com/compliance-check",
                "scan_type": "compliance",
                "priority": "medium"
            }
            
            response = client.post("/v2/cashbot/scan", json=scan_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["scan_type"] == "compliance"
            assert data["priority"] == "medium"
            assert data["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_create_scan_no_providers(self, client):
        """Test scan creation with no providers configured"""
        with patch('api.v2.cashbot.get_providers') as mock_get_providers:
            mock_get_providers.return_value = []
            
            scan_data = {
                "target": "https://example.com/test",
                "scan_type": "financial",
                "priority": "medium"
            }
            
            response = client.post("/v2/cashbot/scan", json=scan_data)
            
            assert response.status_code == 503
            data = response.json()
            assert "No providers configured" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_create_scan_provider_failure(self, client):
        """Test scan creation with provider failure"""
        with patch('api.v2.cashbot.get_providers') as mock_get_providers:
            mock_provider = AsyncMock()
            mock_provider.generate_response.side_effect = Exception("API Error")
            mock_provider.close = AsyncMock()
            mock_get_providers.return_value = [mock_provider]
            
            scan_data = {
                "target": "https://example.com/test",
                "scan_type": "financial",
                "priority": "medium"
            }
            
            response = client.post("/v2/cashbot/scan", json=scan_data)
            
            assert response.status_code == 500
            data = response.json()
            assert "Analysis failed" in data["detail"]
    
    def test_get_scan(self, client):
        """Test getting a specific scan"""
        # First create a scan
        with patch('api.v2.cashbot.get_providers') as mock_get_providers:
            mock_provider = AsyncMock()
            mock_provider.generate_response.return_value = MagicMock(
                success=True,
                content="Test analysis",
                provider="openai",
                model="gpt-3.5-turbo",
                usage={},
                latency_ms=100.0
            )
            mock_provider.close = AsyncMock()
            mock_get_providers.return_value = [mock_provider]
            
            scan_data = {
                "target": "https://example.com/test",
                "scan_type": "financial",
                "priority": "medium"
            }
            
            create_response = client.post("/v2/cashbot/scan", json=scan_data)
            scan_id = create_response.json()["id"]
            
            # Now get the scan
            response = client.get(f"/v2/cashbot/scans/{scan_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == scan_id
            assert data["target"] == scan_data["target"]
    
    def test_get_scan_not_found(self, client):
        """Test getting a non-existent scan"""
        response = client.get("/v2/cashbot/scans/non-existent-id")
        
        assert response.status_code == 404
        data = response.json()
        assert "Scan not found" in data["detail"]
    
    def test_list_scans(self, client):
        """Test listing scans"""
        response = client.get("/v2/cashbot/scans")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_scans_with_status_filter(self, client):
        """Test listing scans with status filter"""
        response = client.get("/v2/cashbot/scans?status=completed")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_finding(self, client):
        """Test getting a specific finding"""
        # First create a scan to get a finding
        with patch('api.v2.cashbot.get_providers') as mock_get_providers:
            mock_provider = AsyncMock()
            mock_provider.generate_response.return_value = MagicMock(
                success=True,
                content="Test analysis with findings",
                provider="openai",
                model="gpt-3.5-turbo",
                usage={},
                latency_ms=100.0
            )
            mock_provider.close = AsyncMock()
            mock_get_providers.return_value = [mock_provider]
            
            scan_data = {
                "target": "https://example.com/test",
                "scan_type": "financial",
                "priority": "medium"
            }
            
            create_response = client.post("/v2/cashbot/scan", json=scan_data)
            scan_data = create_response.json()
            
            if scan_data["findings"]:
                finding_id = scan_data["findings"][0]["id"]
                
                response = client.get(f"/v2/cashbot/findings/{finding_id}")
                
                assert response.status_code == 200
                data = response.json()
                assert data["id"] == finding_id
    
    def test_get_finding_not_found(self, client):
        """Test getting a non-existent finding"""
        response = client.get("/v2/cashbot/findings/non-existent-id")
        
        assert response.status_code == 404
        data = response.json()
        assert "Finding not found" in data["detail"]
    
    def test_list_findings(self, client):
        """Test listing findings"""
        response = client.get("/v2/cashbot/findings")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_findings_with_filters(self, client):
        """Test listing findings with filters"""
        response = client.get("/v2/cashbot/findings?severity=high")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_dispatch(self, client):
        """Test creating a dispatch"""
        # First create a scan
        with patch('api.v2.cashbot.get_providers') as mock_get_providers:
            mock_provider = AsyncMock()
            mock_provider.generate_response.return_value = MagicMock(
                success=True,
                content="Test analysis",
                provider="openai",
                model="gpt-3.5-turbo",
                usage={},
                latency_ms=100.0
            )
            mock_provider.close = AsyncMock()
            mock_get_providers.return_value = [mock_provider]
            
            scan_data = {
                "target": "https://example.com/test",
                "scan_type": "financial",
                "priority": "medium"
            }
            
            create_response = client.post("/v2/cashbot/scan", json=scan_data)
            scan_id = create_response.json()["id"]
            
            # Create dispatch
            dispatch_data = {
                "scan_id": scan_id,
                "action": "notify",
                "recipients": ["admin@example.com"],
                "message": "Please review the scan results"
            }
            
            response = client.post("/v2/cashbot/dispatch", json=dispatch_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["scan_id"] == scan_id
            assert data["action"] == "notify"
            assert data["status"] == "sent"
    
    def test_create_dispatch_scan_not_found(self, client):
        """Test creating dispatch for non-existent scan"""
        dispatch_data = {
            "scan_id": "non-existent-id",
            "action": "notify",
            "recipients": ["admin@example.com"]
        }
        
        response = client.post("/v2/cashbot/dispatch", json=dispatch_data)
        
        assert response.status_code == 404
        data = response.json()
        assert "Scan not found" in data["detail"]
    
    def test_get_dispatch(self, client):
        """Test getting a specific dispatch"""
        # First create a scan and dispatch
        with patch('api.v2.cashbot.get_providers') as mock_get_providers:
            mock_provider = AsyncMock()
            mock_provider.generate_response.return_value = MagicMock(
                success=True,
                content="Test analysis",
                provider="openai",
                model="gpt-3.5-turbo",
                usage={},
                latency_ms=100.0
            )
            mock_provider.close = AsyncMock()
            mock_get_providers.return_value = [mock_provider]
            
            scan_data = {
                "target": "https://example.com/test",
                "scan_type": "financial",
                "priority": "medium"
            }
            
            create_response = client.post("/v2/cashbot/scan", json=scan_data)
            scan_id = create_response.json()["id"]
            
            dispatch_data = {
                "scan_id": scan_id,
                "action": "notify",
                "recipients": ["admin@example.com"]
            }
            
            create_dispatch_response = client.post("/v2/cashbot/dispatch", json=dispatch_data)
            dispatch_id = create_dispatch_response.json()["id"]
            
            # Get dispatch
            response = client.get(f"/v2/cashbot/dispatches/{dispatch_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == dispatch_id
            assert data["scan_id"] == scan_id
    
    def test_list_dispatches(self, client):
        """Test listing dispatches"""
        response = client.get("/v2/cashbot/dispatches")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_dispatches_with_filters(self, client):
        """Test listing dispatches with filters"""
        response = client.get("/v2/cashbot/dispatches?status=sent")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestCashbotModels:
    """Test cashbot data models"""
    
    def test_scan_request_model(self):
        """Test scan request model"""
        scan_request = ScanRequest(
            target="https://example.com",
            scan_type="financial",
            priority="high"
        )
        
        assert scan_request.target == "https://example.com"
        assert scan_request.scan_type == "financial"
        assert scan_request.priority == "high"
    
    def test_finding_model(self):
        """Test finding model"""
        finding = Finding(
            id="test-id",
            scan_id="scan-id",
            type="analysis",
            severity="high",
            title="Test Finding",
            description="Test description",
            recommendation="Test recommendation",
            confidence=0.8
        )
        
        assert finding.id == "test-id"
        assert finding.scan_id == "scan-id"
        assert finding.type == "analysis"
        assert finding.severity == "high"
        assert finding.title == "Test Finding"
        assert finding.confidence == 0.8
    
    def test_scan_result_model(self):
        """Test scan result model"""
        finding = Finding(
            id="test-id",
            scan_id="scan-id",
            type="analysis",
            severity="high",
            title="Test Finding",
            description="Test description",
            recommendation="Test recommendation",
            confidence=0.8
        )
        
        scan_result = ScanResult(
            id="scan-id",
            target="https://example.com",
            scan_type="financial",
            priority="high",
            status="completed",
            findings=[finding],
            summary="Test summary"
        )
        
        assert scan_result.id == "scan-id"
        assert scan_result.target == "https://example.com"
        assert scan_result.scan_type == "financial"
        assert scan_result.priority == "high"
        assert scan_result.status == "completed"
        assert len(scan_result.findings) == 1
        assert scan_result.summary == "Test summary"
    
    def test_dispatch_request_model(self):
        """Test dispatch request model"""
        dispatch_request = DispatchRequest(
            scan_id="scan-id",
            action="notify",
            recipients=["admin@example.com"],
            message="Test message"
        )
        
        assert dispatch_request.scan_id == "scan-id"
        assert dispatch_request.action == "notify"
        assert dispatch_request.recipients == ["admin@example.com"]
        assert dispatch_request.message == "Test message"
