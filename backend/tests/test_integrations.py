"""
Integration Tests für n8n, Email, Slack
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import json

from main import app
from integrations.n8n_client import N8NClient, N8NWebhookHandler
from integrations.email_client import EmailClient, EmailConfig, EmailMessage
from integrations.slack_client import SlackClient, SlackConfig, SlackMessage


class TestN8NIntegration:
    """Test n8n integration"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.mark.asyncio
    async def test_n8n_client_initialization(self):
        """Test N8N client initialization"""
        client = N8NClient()
        assert client.webhook_url is None
        assert client.api_key is None
        assert client.base_url is None
    
    @pytest.mark.asyncio
    async def test_n8n_webhook_handler(self):
        """Test n8n webhook handler"""
        handler = N8NWebhookHandler()
        
        # Test handler registration
        async def test_handler(data):
            return {"processed": True}
        
        handler.register_handler("test_event", test_handler)
        assert "test_event" in handler.handlers
        
        # Test webhook handling
        result = await handler.handle_webhook({
            "event_type": "test_event",
            "data": {"test": "value"}
        })
        
        assert result["status"] == "success"
        assert result["result"]["processed"] is True
    
    @pytest.mark.asyncio
    async def test_n8n_webhook_endpoint(self, client):
        """Test n8n webhook endpoint"""
        webhook_data = {
            "event_type": "test_event",
            "data": {"test": "value"}
        }
        
        response = client.post("/webhooks/n8n", json=webhook_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "processed_at" in data
    
    @pytest.mark.asyncio
    async def test_cashbot_webhook_endpoint(self, client):
        """Test cashbot webhook endpoint"""
        webhook_data = {
            "scan_id": "test-scan-123",
            "findings": [
                {"title": "Test Finding", "severity": "high"}
            ]
        }
        
        response = client.post("/webhooks/n8n/cashbot", json=webhook_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_finance_webhook_endpoint(self, client):
        """Test finance webhook endpoint"""
        webhook_data = {
            "alert_type": "budget_exceeded",
            "message": "Budget exceeded by 10%",
            "severity": "high"
        }
        
        response = client.post("/webhooks/n8n/finance", json=webhook_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_practice_webhook_endpoint(self, client):
        """Test practice webhook endpoint"""
        webhook_data = {
            "notification_type": "appointment_reminder",
            "message": "Appointment reminder for tomorrow",
            "patient_id": "patient-123"
        }
        
        response = client.post("/webhooks/n8n/practice", json=webhook_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_webhook_health_endpoint(self, client):
        """Test webhook health endpoint"""
        response = client.get("/webhooks/n8n/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_webhook_handlers_endpoint(self, client):
        """Test webhook handlers endpoint"""
        response = client.get("/webhooks/n8n/handlers")
        
        assert response.status_code == 200
        data = response.json()
        assert "handlers" in data
        assert "total" in data


class TestEmailIntegration:
    """Test email integration"""
    
    @pytest.mark.asyncio
    async def test_email_client_initialization(self):
        """Test email client initialization"""
        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_username="test@example.com",
            smtp_password="test-password",
            from_email="test@example.com"
        )
        
        client = EmailClient(config)
        assert client.smtp_host == "smtp.example.com"
        assert client.smtp_username == "test@example.com"
        assert client.from_email == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_email_message_creation(self):
        """Test email message creation"""
        message = EmailMessage(
            to=["test@example.com"],
            subject="Test Subject",
            body="Test Body"
        )
        
        assert message.to == ["test@example.com"]
        assert message.subject == "Test Subject"
        assert message.body == "Test Body"
    
    @pytest.mark.asyncio
    async def test_send_notification(self):
        """Test send notification"""
        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_username="test@example.com",
            smtp_password="test-password",
            from_email="test@example.com"
        )
        
        client = EmailClient(config)
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            result = await client.send_notification(
                to=["test@example.com"],
                subject="Test Subject",
                message="Test Message"
            )
            
            assert result is True
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once()
            mock_server.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_cashbot_alert(self):
        """Test send cashbot alert"""
        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_username="test@example.com",
            smtp_password="test-password",
            from_email="test@example.com"
        )
        
        client = EmailClient(config)
        
        findings = [
            {"title": "Test Finding 1", "severity": "high"},
            {"title": "Test Finding 2", "severity": "medium"}
        ]
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            result = await client.send_cashbot_alert(
                to=["test@example.com"],
                scan_id="test-scan-123",
                findings=findings
            )
            
            assert result is True
            mock_server.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_finance_alert(self):
        """Test send finance alert"""
        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_username="test@example.com",
            smtp_password="test-password",
            from_email="test@example.com"
        )
        
        client = EmailClient(config)
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            result = await client.send_finance_alert(
                to=["test@example.com"],
                alert_type="budget_exceeded",
                message="Budget exceeded by 10%",
                severity="high"
            )
            
            assert result is True
            mock_server.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_practice_notification(self):
        """Test send practice notification"""
        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_username="test@example.com",
            smtp_password="test-password",
            from_email="test@example.com"
        )
        
        client = EmailClient(config)
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            result = await client.send_practice_notification(
                to=["test@example.com"],
                notification_type="appointment_reminder",
                message="Appointment reminder for tomorrow",
                patient_id="patient-123"
            )
            
            assert result is True
            mock_server.send_message.assert_called_once()


class TestSlackIntegration:
    """Test Slack integration"""
    
    @pytest.mark.asyncio
    async def test_slack_client_initialization(self):
        """Test Slack client initialization"""
        config = SlackConfig(
            webhook_url="https://hooks.slack.com/services/test",
            channel="#test-channel",
            username="Test Bot"
        )
        
        client = SlackClient(config)
        assert client.webhook_url == "https://hooks.slack.com/services/test"
        assert client.channel == "#test-channel"
        assert client.username == "Test Bot"
    
    @pytest.mark.asyncio
    async def test_slack_message_creation(self):
        """Test Slack message creation"""
        message = SlackMessage(
            text="Test Message",
            channel="#test-channel",
            username="Test Bot"
        )
        
        assert message.text == "Test Message"
        assert message.channel == "#test-channel"
        assert message.username == "Test Bot"
    
    @pytest.mark.asyncio
    async def test_send_notification(self):
        """Test send Slack notification"""
        config = SlackConfig(
            webhook_url="https://hooks.slack.com/services/test"
        )
        
        client = SlackClient(config)
        
        with patch.object(client.client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            result = await client.send_notification(
                text="Test Message",
                channel="#test-channel"
            )
            
            assert result is True
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_cashbot_alert(self):
        """Test send cashbot alert to Slack"""
        config = SlackConfig(
            webhook_url="https://hooks.slack.com/services/test"
        )
        
        client = SlackClient(config)
        
        findings = [
            {"title": "Test Finding 1", "severity": "high", "description": "Test description 1"},
            {"title": "Test Finding 2", "severity": "medium", "description": "Test description 2"}
        ]
        
        with patch.object(client.client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            result = await client.send_cashbot_alert(
                scan_id="test-scan-123",
                findings=findings,
                channel="#test-channel"
            )
            
            assert result is True
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_finance_alert(self):
        """Test send finance alert to Slack"""
        config = SlackConfig(
            webhook_url="https://hooks.slack.com/services/test"
        )
        
        client = SlackClient(config)
        
        with patch.object(client.client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            result = await client.send_finance_alert(
                alert_type="budget_exceeded",
                message="Budget exceeded by 10%",
                severity="high",
                channel="#test-channel"
            )
            
            assert result is True
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_practice_notification(self):
        """Test send practice notification to Slack"""
        config = SlackConfig(
            webhook_url="https://hooks.slack.com/services/test"
        )
        
        client = SlackClient(config)
        
        with patch.object(client.client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            result = await client.send_practice_notification(
                notification_type="appointment_reminder",
                message="Appointment reminder for tomorrow",
                patient_id="patient-123",
                channel="#test-channel"
            )
            
            assert result is True
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_system_health_alert(self):
        """Test send system health alert to Slack"""
        config = SlackConfig(
            webhook_url="https://hooks.slack.com/services/test"
        )
        
        client = SlackClient(config)
        
        health_status = {
            "status": "healthy",
            "latency_ms": 150.0,
            "providers": [
                {"provider": "openai", "status": "healthy", "latency_ms": 100.0},
                {"provider": "anthropic", "status": "healthy", "latency_ms": 200.0}
            ]
        }
        
        with patch.object(client.client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            result = await client.send_system_health_alert(
                health_status=health_status,
                channel="#test-channel"
            )
            
            assert result is True
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_client(self):
        """Test close Slack client"""
        config = SlackConfig(
            webhook_url="https://hooks.slack.com/services/test"
        )
        
        client = SlackClient(config)
        
        with patch.object(client.client, 'aclose') as mock_close:
            await client.close()
            mock_close.assert_called_once()


@pytest.mark.asyncio
async def test_integration_health_checks():
    """Test integration health checks"""
    # Test n8n client health check
    n8n_client = N8NClient()
    health = await n8n_client.health_check()
    assert "status" in health
    
    # Test email client (should return None if not configured)
    from integrations.email_client import get_email_client
    email_client = get_email_client()
    assert email_client is None  # Not configured in test environment
    
    # Test Slack client (should return None if not configured)
    from integrations.slack_client import get_slack_client
    slack_client = get_slack_client()
    assert slack_client is None  # Not configured in test environment
