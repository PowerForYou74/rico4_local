"""
n8n Webhook Integration für Rico Orchestrator System
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from datetime import datetime
import json

from ..config.settings import settings
from .n8n_client import n8n_client, webhook_handler


router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class WebhookPayload(BaseModel):
    """n8n webhook payload"""
    event_type: str
    data: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WebhookResponse(BaseModel):
    """Webhook response"""
    status: str
    message: str
    processed_at: datetime = Field(default_factory=datetime.utcnow)


@router.post("/n8n", response_model=WebhookResponse)
async def handle_n8n_webhook(request: Request):
    """Handle incoming n8n webhook"""
    try:
        # Parse request body
        body = await request.body()
        data = json.loads(body) if body else {}
        
        # Create webhook payload
        payload = WebhookPayload(
            event_type=data.get("event_type", "unknown"),
            data=data.get("data", {}),
            timestamp=datetime.utcnow()
        )
        
        # Process webhook
        result = await webhook_handler.handle_webhook(payload.dict())
        
        return WebhookResponse(
            status=result["status"],
            message=result.get("message", "Webhook processed"),
            processed_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


@router.post("/n8n/cashbot", response_model=WebhookResponse)
async def handle_cashbot_webhook(request: Request):
    """Handle cashbot-specific n8n webhook"""
    try:
        body = await request.body()
        data = json.loads(body) if body else {}
        
        # Process cashbot webhook
        result = await webhook_handler.handle_webhook({
            "event_type": "cashbot_scan",
            "data": data
        })
        
        return WebhookResponse(
            status=result["status"],
            message=result.get("message", "Cashbot webhook processed"),
            processed_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cashbot webhook processing failed: {str(e)}")


@router.post("/n8n/finance", response_model=WebhookResponse)
async def handle_finance_webhook(request: Request):
    """Handle finance-specific n8n webhook"""
    try:
        body = await request.body()
        data = json.loads(body) if body else {}
        
        # Process finance webhook
        result = await webhook_handler.handle_webhook({
            "event_type": "finance_alert",
            "data": data
        })
        
        return WebhookResponse(
            status=result["status"],
            message=result.get("message", "Finance webhook processed"),
            processed_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Finance webhook processing failed: {str(e)}")


@router.post("/n8n/practice", response_model=WebhookResponse)
async def handle_practice_webhook(request: Request):
    """Handle practice-specific n8n webhook"""
    try:
        body = await request.body()
        data = json.loads(body) if body else {}
        
        # Process practice webhook
        result = await webhook_handler.handle_webhook({
            "event_type": "practice_notification",
            "data": data
        })
        
        return WebhookResponse(
            status=result["status"],
            message=result.get("message", "Practice webhook processed"),
            processed_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Practice webhook processing failed: {str(e)}")


@router.get("/n8n/health")
async def webhook_health():
    """Check webhook system health"""
    try:
        # Check n8n client health
        n8n_health = await n8n_client.health_check()
        
        return {
            "status": "healthy",
            "n8n_client": n8n_health,
            "webhook_handlers": len(webhook_handler.handlers),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/n8n/handlers")
async def list_webhook_handlers():
    """List available webhook handlers"""
    return {
        "handlers": list(webhook_handler.handlers.keys()),
        "total": len(webhook_handler.handlers)
    }
