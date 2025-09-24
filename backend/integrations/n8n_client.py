"""
n8n Integration: Webhook-Client mit ENV-based Config
"""
import asyncio
import time
from typing import Dict, Any, Optional, List
import httpx
from datetime import datetime
import json

from ..config.settings import settings


class N8NClient:
    """n8n webhook client with ENV-based configuration"""
    
    def __init__(self):
        self.webhook_url = settings.n8n_webhook_url
        self.api_key = settings.n8n_api_key
        self.base_url = self.webhook_url.replace('/webhook/', '/api/') if self.webhook_url else None
        
        self.client = httpx.AsyncClient(
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}" if self.api_key else None
            },
            timeout=30.0
        ) if self.base_url else None
    
    async def send_webhook(
        self, 
        data: Dict[str, Any], 
        webhook_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send data to n8n webhook"""
        if not self.webhook_url:
            raise ValueError("n8n webhook URL not configured")
        
        url = self.webhook_url
        if webhook_path:
            url = f"{self.webhook_url.rstrip('/')}/{webhook_path.lstrip('/')}"
        
        try:
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to send webhook: {str(e)}")
    
    async def trigger_workflow(
        self, 
        workflow_id: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Trigger a specific n8n workflow"""
        if not self.base_url:
            raise ValueError("n8n API URL not configured")
        
        url = f"{self.base_url}/workflows/{workflow_id}/execute"
        
        try:
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to trigger workflow: {str(e)}")
    
    async def get_workflows(self) -> List[Dict[str, Any]]:
        """Get list of available workflows"""
        if not self.base_url:
            raise ValueError("n8n API URL not configured")
        
        url = f"{self.base_url}/workflows"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to get workflows: {str(e)}")
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get status of a specific workflow"""
        if not self.base_url:
            raise ValueError("n8n API URL not configured")
        
        url = f"{self.base_url}/workflows/{workflow_id}"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to get workflow status: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check n8n service health"""
        if not self.base_url:
            return {
                "status": "not_configured",
                "message": "n8n API URL not configured"
            }
        
        try:
            start_time = time.time()
            response = await self.client.get(f"{self.base_url}/health")
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "latency_ms": latency_ms,
                    "service": "n8n"
                }
            else:
                return {
                    "status": "unhealthy",
                    "latency_ms": latency_ms,
                    "service": "n8n",
                    "error": f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "n8n",
                "error": str(e)
            }
    
    async def close(self):
        """Close the HTTP client"""
        if self.client:
            await self.client.aclose()


class N8NWebhookHandler:
    """Handler for incoming n8n webhooks"""
    
    def __init__(self):
        self.handlers = {}
    
    def register_handler(self, event_type: str, handler_func):
        """Register a handler for a specific event type"""
        self.handlers[event_type] = handler_func
    
    async def handle_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming webhook data"""
        event_type = data.get("event_type", "unknown")
        
        if event_type in self.handlers:
            try:
                result = await self.handlers[event_type](data)
                return {
                    "status": "success",
                    "event_type": event_type,
                    "result": result
                }
            except Exception as e:
                return {
                    "status": "error",
                    "event_type": event_type,
                    "error": str(e)
                }
        else:
            return {
                "status": "unhandled",
                "event_type": event_type,
                "message": "No handler registered for this event type"
            }


# Global n8n client instance
n8n_client = N8NClient()
webhook_handler = N8NWebhookHandler()


# Predefined webhook handlers
async def handle_cashbot_scan(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle cashbot scan results from n8n"""
    scan_id = data.get("scan_id")
    findings = data.get("findings", [])
    
    # Process findings
    processed_findings = []
    for finding in findings:
        processed_findings.append({
            "id": finding.get("id"),
            "type": finding.get("type"),
            "severity": finding.get("severity"),
            "title": finding.get("title"),
            "description": finding.get("description")
        })
    
    return {
        "scan_id": scan_id,
        "processed_findings": processed_findings,
        "timestamp": datetime.utcnow().isoformat()
    }


async def handle_finance_alert(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle finance alerts from n8n"""
    alert_type = data.get("alert_type")
    message = data.get("message")
    severity = data.get("severity", "medium")
    
    return {
        "alert_type": alert_type,
        "message": message,
        "severity": severity,
        "processed_at": datetime.utcnow().isoformat()
    }


async def handle_practice_notification(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle practice notifications from n8n"""
    notification_type = data.get("notification_type")
    patient_id = data.get("patient_id")
    message = data.get("message")
    
    return {
        "notification_type": notification_type,
        "patient_id": patient_id,
        "message": message,
        "processed_at": datetime.utcnow().isoformat()
    }


# Register default handlers
webhook_handler.register_handler("cashbot_scan", handle_cashbot_scan)
webhook_handler.register_handler("finance_alert", handle_finance_alert)
webhook_handler.register_handler("practice_notification", handle_practice_notification)
