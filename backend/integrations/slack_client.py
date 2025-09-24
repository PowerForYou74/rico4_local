"""
Slack Integration für Rico Orchestrator System
"""
import httpx
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from ..config.settings import settings


logger = logging.getLogger(__name__)


class SlackConfig(BaseModel):
    """Slack configuration"""
    webhook_url: str
    channel: Optional[str] = None
    username: str = "Rico Orchestrator"
    icon_emoji: str = ":robot_face:"


class SlackMessage(BaseModel):
    """Slack message"""
    text: str
    channel: Optional[str] = None
    username: Optional[str] = None
    icon_emoji: Optional[str] = None
    attachments: List[Dict[str, Any]] = []


class SlackClient:
    """Slack client for sending notifications"""
    
    def __init__(self, config: SlackConfig):
        self.config = config
        self.webhook_url = config.webhook_url
        self.channel = config.channel
        self.username = config.username
        self.icon_emoji = config.icon_emoji
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def send_message(self, message: SlackMessage) -> bool:
        """Send Slack message"""
        try:
            payload = {
                "text": message.text,
                "channel": message.channel or self.channel,
                "username": message.username or self.username,
                "icon_emoji": message.icon_emoji or self.icon_emoji,
                "attachments": message.attachments
            }
            
            response = await self.client.post(self.webhook_url, json=payload)
            response.raise_for_status()
            
            logger.info("Slack message sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Slack message: {str(e)}")
            return False
    
    async def send_notification(
        self, 
        text: str, 
        channel: Optional[str] = None,
        attachments: List[Dict[str, Any]] = []
    ) -> bool:
        """Send notification to Slack"""
        message = SlackMessage(
            text=text,
            channel=channel,
            attachments=attachments
        )
        
        return await self.send_message(message)
    
    async def send_cashbot_alert(
        self, 
        scan_id: str, 
        findings: List[Dict[str, Any]],
        channel: Optional[str] = None
    ) -> bool:
        """Send cashbot scan alert to Slack"""
        # Create message text
        text = f"🔍 *Cashbot Scan Alert*\nScan ID: `{scan_id}`\nFindings: {len(findings)}"
        
        # Create attachments
        attachments = []
        for finding in findings:
            color = "danger" if finding.get('severity') == 'critical' else "warning" if finding.get('severity') == 'high' else "good"
            attachments.append({
                "color": color,
                "title": finding.get('title', 'Unknown'),
                "text": finding.get('description', 'No description'),
                "fields": [
                    {
                        "title": "Severity",
                        "value": finding.get('severity', 'Unknown'),
                        "short": True
                    },
                    {
                        "title": "Confidence",
                        "value": f"{finding.get('confidence', 0) * 100:.1f}%",
                        "short": True
                    }
                ]
            })
        
        return await self.send_notification(text, channel, attachments)
    
    async def send_finance_alert(
        self, 
        alert_type: str, 
        message: str,
        severity: str = "medium",
        channel: Optional[str] = None
    ) -> bool:
        """Send finance alert to Slack"""
        # Create message text
        emoji = "🚨" if severity == "high" else "⚠️" if severity == "medium" else "ℹ️"
        text = f"{emoji} *Finance Alert*\nType: {alert_type}\nSeverity: {severity}\nMessage: {message}"
        
        # Create attachment
        color = "danger" if severity == "high" else "warning" if severity == "medium" else "good"
        attachments = [{
            "color": color,
            "title": f"Finance Alert - {alert_type}",
            "text": message,
            "fields": [
                {
                    "title": "Type",
                    "value": alert_type,
                    "short": True
                },
                {
                    "title": "Severity",
                    "value": severity,
                    "short": True
                }
            ]
        }]
        
        return await self.send_notification(text, channel, attachments)
    
    async def send_practice_notification(
        self, 
        notification_type: str, 
        message: str,
        patient_id: Optional[str] = None,
        channel: Optional[str] = None
    ) -> bool:
        """Send practice notification to Slack"""
        # Create message text
        text = f"🏥 *Practice Notification*\nType: {notification_type}\nMessage: {message}"
        if patient_id:
            text += f"\nPatient ID: `{patient_id}`"
        
        # Create attachment
        attachments = [{
            "color": "good",
            "title": f"Practice Notification - {notification_type}",
            "text": message,
            "fields": [
                {
                    "title": "Type",
                    "value": notification_type,
                    "short": True
                }
            ]
        }]
        
        if patient_id:
            attachments[0]["fields"].append({
                "title": "Patient ID",
                "value": patient_id,
                "short": True
            })
        
        return await self.send_notification(text, channel, attachments)
    
    async def send_system_health_alert(
        self, 
        health_status: Dict[str, Any],
        channel: Optional[str] = None
    ) -> bool:
        """Send system health alert to Slack"""
        status = health_status.get('status', 'unknown')
        emoji = "✅" if status == "healthy" else "❌" if status == "unhealthy" else "⚠️"
        
        text = f"{emoji} *System Health Alert*\nStatus: {status}\nLatency: {health_status.get('latency_ms', 0):.0f}ms"
        
        # Create attachment with provider details
        attachments = [{
            "color": "good" if status == "healthy" else "danger",
            "title": "System Health Status",
            "text": f"Overall Status: {status}",
            "fields": []
        }]
        
        providers = health_status.get('providers', [])
        for provider in providers:
            provider_emoji = "✅" if provider.get('status') == 'healthy' else "❌"
            attachments[0]["fields"].append({
                "title": f"{provider_emoji} {provider.get('provider', 'Unknown')}",
                "value": f"Status: {provider.get('status', 'unknown')}\nLatency: {provider.get('latency_ms', 0):.0f}ms",
                "short": True
            })
        
        return await self.send_notification(text, channel, attachments)
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Global Slack client instance
slack_client: Optional[SlackClient] = None


def get_slack_client() -> Optional[SlackClient]:
    """Get Slack client instance"""
    global slack_client
    
    if slack_client is None:
        # Check if Slack configuration is available
        if hasattr(settings, 'slack_webhook_url') and settings.slack_webhook_url:
            config = SlackConfig(
                webhook_url=settings.slack_webhook_url,
                channel=getattr(settings, 'slack_channel', None),
                username=getattr(settings, 'slack_username', 'Rico Orchestrator'),
                icon_emoji=getattr(settings, 'slack_icon_emoji', ':robot_face:')
            )
            slack_client = SlackClient(config)
    
    return slack_client


async def send_slack_notification(
    text: str, 
    channel: Optional[str] = None,
    attachments: List[Dict[str, Any]] = []
) -> bool:
    """Send Slack notification using global client"""
    client = get_slack_client()
    if not client:
        logger.warning("Slack client not configured")
        return False
    
    return await client.send_notification(text, channel, attachments)
