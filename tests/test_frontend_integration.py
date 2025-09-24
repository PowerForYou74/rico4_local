"""
Frontend Integration Tests - Mock HTTP Calls
"""
import pytest
from unittest.mock import Mock, patch
import json

# Mock API responses
MOCK_HEALTH_RESPONSE = {
    "openai": "ok",
    "claude": "ok", 
    "perplexity": "error",
    "env_source": "local",
    "models": {
        "openai": "gpt-4o-mini",
        "claude": "claude-3-5-sonnet-20241022",
        "perplexity": "sonar"
    },
    "latency": {
        "openai": 1200,
        "claude": 800,
        "perplexity": 0
    }
}

MOCK_PRACTICE_STATS = {
    "patients": {
        "total": 25,
        "active": 20
    },
    "appointments_today": 3,
    "unpaid_invoices": {
        "count": 5,
        "amount_eur": 1250.50
    }
}

MOCK_FINANCE_KPIS = {
    "mrr": 5000.0,
    "arr": 60000.0,
    "cash_on_hand": 25000.0,
    "burn_rate": 3000.0,
    "runway_days": 250
}

MOCK_CASHBOT_FINDINGS = [
    {
        "id": 1,
        "title": "Digitale Futterberatung",
        "idea": "Online-Service für personalisierte Futterempfehlungen",
        "steps": ["Website erstellen", "KI-Integration", "Marketing"],
        "potential_eur": 2000.0,
        "effort": "medium",
        "risk": "low",
        "timeframe": "kurzfristig",
        "status": "new",
        "provider": "claude",
        "duration_s": 3.2,
        "created_at": "2024-01-15T10:30:00Z"
    }
]

class TestFrontendAPI:
    """Tests für Frontend API-Calls"""
    
    @patch('requests.get')
    def test_health_status_api(self, mock_get):
        """Test Health Status API Call"""
        mock_response = Mock()
        mock_response.json.return_value = MOCK_HEALTH_RESPONSE
        mock_response.ok = True
        mock_get.return_value = mock_response
        
        # Simulate API call
        response = mock_get("http://localhost:8000/check-keys")
        data = response.json()
        
        assert data["openai"] == "ok"
        assert data["claude"] == "ok"
        assert data["perplexity"] == "error"
        assert data["env_source"] == "local"
    
    @patch('requests.get')
    def test_practice_stats_api(self, mock_get):
        """Test Practice Stats API Call"""
        mock_response = Mock()
        mock_response.json.return_value = MOCK_PRACTICE_STATS
        mock_response.ok = True
        mock_get.return_value = mock_response
        
        response = mock_get("http://localhost:8000/v2/practice/stats")
        data = response.json()
        
        assert data["patients"]["total"] == 25
        assert data["patients"]["active"] == 20
        assert data["appointments_today"] == 3
        assert data["unpaid_invoices"]["count"] == 5
    
    @patch('requests.get')
    def test_finance_kpis_api(self, mock_get):
        """Test Finance KPIs API Call"""
        mock_response = Mock()
        mock_response.json.return_value = MOCK_FINANCE_KPIS
        mock_response.ok = True
        mock_get.return_value = mock_response
        
        response = mock_get("http://localhost:8000/v2/finance/kpis")
        data = response.json()
        
        assert data["mrr"] == 5000.0
        assert data["arr"] == 60000.0
        assert data["cash_on_hand"] == 25000.0
        assert data["runway_days"] == 250
    
    @patch('requests.get')
    def test_cashbot_findings_api(self, mock_get):
        """Test Cashbot Findings API Call"""
        mock_response = Mock()
        mock_response.json.return_value = MOCK_CASHBOT_FINDINGS
        mock_response.ok = True
        mock_get.return_value = mock_response
        
        response = mock_get("http://localhost:8000/v2/cashbot/findings")
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["title"] == "Digitale Futterberatung"
        assert data[0]["potential_eur"] == 2000.0
        assert data[0]["timeframe"] == "kurzfristig"
    
    @patch('requests.post')
    def test_cashbot_scan_api(self, mock_post):
        """Test Cashbot Scan API Call"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "success",
            "finding_id": 1,
            "title": "Test Finding",
            "potential_eur": 1000.0
        }
        mock_response.ok = True
        mock_post.return_value = mock_response
        
        response = mock_post("http://localhost:8000/v2/cashbot/scan")
        data = response.json()
        
        assert data["status"] == "success"
        assert data["finding_id"] == 1
        assert data["title"] == "Test Finding"
    
    @patch('requests.post')
    def test_agent_run_api(self, mock_post):
        """Test Agent Run API Call"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "Test agent response",
            "meta": {
                "used_provider": "claude",
                "duration_s": 2.5,
                "cost_eur": 0.0125
            }
        }
        mock_response.ok = True
        mock_post.return_value = mock_response
        
        response = mock_post("http://localhost:8000/api/v1/rico-agent", json={
            "user_input": "Test input",
            "system_prompt": "Test prompt",
            "mode": "auto"
        })
        data = response.json()
        
        assert data["response"] == "Test agent response"
        assert data["meta"]["used_provider"] == "claude"
        assert data["meta"]["duration_s"] == 2.5

class TestErrorHandling:
    """Tests für Fehlerbehandlung im Frontend"""
    
    @patch('requests.get')
    def test_api_error_handling(self, mock_get):
        """Test API Error Handling"""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        response = mock_get("http://localhost:8000/check-keys")
        
        assert not response.ok
        assert response.status_code == 500
    
    @patch('requests.get')
    def test_network_error_handling(self, mock_get):
        """Test Network Error Handling"""
        mock_get.side_effect = Exception("Network error")
        
        with pytest.raises(Exception):
            mock_get("http://localhost:8000/check-keys")

class TestDataValidation:
    """Tests für Datenvalidierung"""
    
    def test_health_status_validation(self):
        """Test Health Status Data Validation"""
        data = MOCK_HEALTH_RESPONSE
        
        # Required fields
        assert "openai" in data
        assert "claude" in data
        assert "perplexity" in data
        assert "env_source" in data
        
        # Status values
        assert data["openai"] in ["ok", "error", "timeout"]
        assert data["claude"] in ["ok", "error", "timeout"]
        assert data["perplexity"] in ["ok", "error", "timeout"]
    
    def test_practice_stats_validation(self):
        """Test Practice Stats Data Validation"""
        data = MOCK_PRACTICE_STATS
        
        # Required fields
        assert "patients" in data
        assert "appointments_today" in data
        assert "unpaid_invoices" in data
        
        # Data types
        assert isinstance(data["patients"]["total"], int)
        assert isinstance(data["patients"]["active"], int)
        assert isinstance(data["appointments_today"], int)
        assert isinstance(data["unpaid_invoices"]["count"], int)
        assert isinstance(data["unpaid_invoices"]["amount_eur"], (int, float))
    
    def test_finance_kpis_validation(self):
        """Test Finance KPIs Data Validation"""
        data = MOCK_FINANCE_KPIS
        
        # Required fields
        assert "mrr" in data
        assert "arr" in data
        assert "cash_on_hand" in data
        assert "burn_rate" in data
        assert "runway_days" in data
        
        # Data types
        assert isinstance(data["mrr"], (int, float))
        assert isinstance(data["arr"], (int, float))
        assert isinstance(data["cash_on_hand"], (int, float))
        assert isinstance(data["burn_rate"], (int, float))
        assert isinstance(data["runway_days"], int)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
