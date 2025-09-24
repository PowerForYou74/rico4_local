"""
Tests für v2 APIs - Unit & Integration Tests
"""
import pytest
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.app.main import app

client = TestClient(app)

class TestV2CoreAPI:
    """Tests für v2/core Endpoints"""
    
    def test_health_check(self):
        """Test /check-keys endpoint"""
        response = client.get("/check-keys")
        assert response.status_code == 200
        data = response.json()
        assert "openai" in data
        assert "claude" in data
        assert "perplexity" in data
        assert "env_source" in data
    
    def test_prompts_list(self):
        """Test GET /v2/core/prompts"""
        response = client.get("/v2/core/prompts")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_prompts_create(self):
        """Test POST /v2/core/prompts"""
        response = client.post("/v2/core/prompts", data={
            "name": "Test Prompt",
            "role": "system",
            "tags": "test",
            "body": "Test prompt body"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_runs_list(self):
        """Test GET /v2/core/runs"""
        response = client.get("/v2/core/runs")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_runs_create(self):
        """Test POST /v2/core/runs"""
        run_data = {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "input_tokens": 100,
            "output_tokens": 50,
            "duration_s": 2.5,
            "status": "success"
        }
        response = client.post("/v2/core/runs", json=run_data)
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] == True

class TestV2PracticeAPI:
    """Tests für v2/practice Endpoints"""
    
    def test_practice_stats(self):
        """Test GET /v2/practice/stats"""
        response = client.get("/v2/practice/stats")
        assert response.status_code == 200
        data = response.json()
        assert "patients" in data
        assert "appointments_today" in data
        assert "unpaid_invoices" in data
    
    def test_patients_list(self):
        """Test GET /v2/practice/patients"""
        response = client.get("/v2/practice/patients")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_patients_create(self):
        """Test POST /v2/practice/patients"""
        patient_data = {
            "name": "Test Patient",
            "species": "Hund",
            "breed": "Labrador",
            "status": "active"
        }
        response = client.post("/v2/practice/patients", json=patient_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Patient"

class TestV2FinanceAPI:
    """Tests für v2/finance Endpoints"""
    
    def test_finance_kpis(self):
        """Test GET /v2/finance/kpis"""
        response = client.get("/v2/finance/kpis")
        assert response.status_code == 200
        data = response.json()
        assert "mrr" in data
        assert "arr" in data
        assert "cash_on_hand" in data
        assert "burn_rate" in data
        assert "runway_days" in data
    
    def test_finance_forecast(self):
        """Test GET /v2/finance/forecast"""
        response = client.get("/v2/finance/forecast")
        assert response.status_code == 200
        data = response.json()
        assert "monthly" in data
        assert "assumptions" in data
        assert isinstance(data["monthly"], list)

class TestV2CashbotAPI:
    """Tests für v2/cashbot Endpoints"""
    
    def test_cashbot_findings(self):
        """Test GET /v2/cashbot/findings"""
        response = client.get("/v2/cashbot/findings")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_cashbot_config(self):
        """Test GET /v2/cashbot/config"""
        response = client.get("/v2/cashbot/config")
        assert response.status_code == 200
        data = response.json()
        assert "interval_cron" in data
        assert "providers_enabled" in data
        assert "online_capable" in data
    
    @patch('backend.v2.cashbot.api.run_cashbot_scan')
    def test_cashbot_scan(self, mock_scan):
        """Test POST /v2/cashbot/scan"""
        mock_scan.return_value = {
            "response": json.dumps({
                "title": "Test Finding",
                "idea": "Test idea",
                "steps": ["Step 1", "Step 2"],
                "potential_eur": 1000.0,
                "effort": "medium",
                "risk": "low",
                "timeframe": "kurzfristig",
                "source_hints": ["Test source"]
            }),
            "meta": {
                "used_provider": "openai",
                "duration_s": 2.5
            }
        }
        
        response = client.post("/v2/cashbot/scan")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "finding_id" in data

class TestErrorHandling:
    """Tests für Fehlerbehandlung"""
    
    def test_invalid_endpoint(self):
        """Test 404 für ungültige Endpoints"""
        response = client.get("/v2/invalid/endpoint")
        assert response.status_code == 404
    
    def test_validation_errors(self):
        """Test Validierungsfehler"""
        response = client.post("/v2/core/prompts", data={})
        assert response.status_code == 422  # Validation Error

class TestCORS:
    """Tests für CORS-Konfiguration"""
    
    def test_cors_headers(self):
        """Test CORS-Headers für Next.js"""
        response = client.options("/check-keys")
        assert response.status_code == 200
        
        # Test mit Origin-Header
        response = client.get("/check-keys", headers={"Origin": "http://localhost:3000"})
        assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
