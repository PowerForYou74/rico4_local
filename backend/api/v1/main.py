"""
Legacy /rico-agent Endpoint (Hello World / simple mock)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

router = APIRouter(prefix="/v1", tags=["v1-legacy"])


class RicoAgentRequest(BaseModel):
    """Rico Agent request model"""
    message: str
    context: Optional[Dict[str, Any]] = None


class RicoAgentResponse(BaseModel):
    """Rico Agent response model"""
    response: str
    timestamp: datetime
    status: str = "success"


@router.post("/rico-agent", response_model=RicoAgentResponse)
async def rico_agent(request: RicoAgentRequest):
    """Legacy Rico Agent endpoint - Hello World / simple mock"""
    
    # Simple mock responses based on message content
    message_lower = request.message.lower()
    
    if "hello" in message_lower or "hi" in message_lower:
        response_text = "Hello! I'm Rico, your AI assistant. How can I help you today?"
    elif "help" in message_lower:
        response_text = "I can help you with various tasks. What would you like to know?"
    elif "status" in message_lower:
        response_text = "System status: All systems operational. Rico Orchestrator v2.0 is running smoothly."
    elif "health" in message_lower:
        response_text = "Health check: All providers are healthy and ready to assist you."
    elif "test" in message_lower:
        response_text = "Test successful! Rico Orchestrator is working correctly."
    else:
        response_text = f"I received your message: '{request.message}'. This is a mock response from the legacy Rico Agent endpoint."
    
    return RicoAgentResponse(
        response=response_text,
        timestamp=datetime.utcnow(),
        status="success"
    )


@router.get("/rico-agent/status")
async def rico_agent_status():
    """Get Rico Agent status"""
    return {
        "status": "active",
        "version": "1.0.0",
        "endpoint": "/v1/rico-agent",
        "message": "Legacy Rico Agent endpoint is operational",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/rico-agent/health")
async def rico_agent_health():
    """Get Rico Agent health"""
    return {
        "status": "healthy",
        "uptime": "100%",
        "last_check": datetime.utcnow().isoformat(),
        "message": "Rico Agent is healthy and ready to serve requests"
    }