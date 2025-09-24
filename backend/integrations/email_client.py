"""
Email Integration für Rico Orchestrator System
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from ..config.settings import settings


logger = logging.getLogger(__name__)


class EmailConfig(BaseModel):
    """Email configuration"""
    smtp_host: str
    smtp_port: int = 587
    smtp_username: str
    smtp_password: str
    from_email: str
    from_name: str = "Rico Orchestrator"


class EmailMessage(BaseModel):
    """Email message"""
    to: List[str]
    subject: str
    body: str
    html_body: Optional[str] = None
    cc: List[str] = []
    bcc: List[str] = []


class EmailClient:
    """Email client for sending notifications"""
    
    def __init__(self, config: EmailConfig):
        self.config = config
        self.smtp_host = config.smtp_host
        self.smtp_port = config.smtp_port
        self.smtp_username = config.smtp_username
        self.smtp_password = config.smtp_password
        self.from_email = config.from_email
        self.from_name = config.from_name
    
    async def send_email(self, message: EmailMessage) -> bool:
        """Send email message"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = ", ".join(message.to)
            msg['Subject'] = message.subject
            
            if message.cc:
                msg['Cc'] = ", ".join(message.cc)
            
            # Add recipients
            recipients = message.to + message.cc + message.bcc
            
            # Add text body
            text_part = MIMEText(message.body, 'plain')
            msg.attach(text_part)
            
            # Add HTML body if provided
            if message.html_body:
                html_part = MIMEText(message.html_body, 'html')
                msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg, to_addrs=recipients)
            
            logger.info(f"Email sent successfully to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    async def send_notification(
        self, 
        to: List[str], 
        subject: str, 
        message: str,
        html_message: Optional[str] = None
    ) -> bool:
        """Send notification email"""
        email_message = EmailMessage(
            to=to,
            subject=subject,
            body=message,
            html_body=html_message
        )
        
        return await self.send_email(email_message)
    
    async def send_cashbot_alert(
        self, 
        to: List[str], 
        scan_id: str, 
        findings: List[Dict[str, Any]]
    ) -> bool:
        """Send cashbot scan alert"""
        subject = f"Cashbot Scan Alert - {scan_id}"
        
        # Create text message
        text_message = f"""
Cashbot Scan Alert

Scan ID: {scan_id}
Findings: {len(findings)}

Findings Details:
"""
        for finding in findings:
            text_message += f"- {finding.get('title', 'Unknown')} ({finding.get('severity', 'Unknown')})\n"
        
        # Create HTML message
        html_message = f"""
<html>
<body>
    <h2>Cashbot Scan Alert</h2>
    <p><strong>Scan ID:</strong> {scan_id}</p>
    <p><strong>Findings:</strong> {len(findings)}</p>
    
    <h3>Findings Details:</h3>
    <ul>
"""
        for finding in findings:
            html_message += f"""
        <li>
            <strong>{finding.get('title', 'Unknown')}</strong> 
            <span style="color: {'red' if finding.get('severity') == 'critical' else 'orange' if finding.get('severity') == 'high' else 'blue'}">
                ({finding.get('severity', 'Unknown')})
            </span>
        </li>
"""
        html_message += """
    </ul>
</body>
</html>
"""
        
        return await self.send_notification(
            to=to,
            subject=subject,
            message=text_message,
            html_message=html_message
        )
    
    async def send_finance_alert(
        self, 
        to: List[str], 
        alert_type: str, 
        message: str,
        severity: str = "medium"
    ) -> bool:
        """Send finance alert"""
        subject = f"Finance Alert - {alert_type}"
        
        # Create text message
        text_message = f"""
Finance Alert

Type: {alert_type}
Severity: {severity}
Message: {message}
"""
        
        # Create HTML message
        html_message = f"""
<html>
<body>
    <h2>Finance Alert</h2>
    <p><strong>Type:</strong> {alert_type}</p>
    <p><strong>Severity:</strong> 
        <span style="color: {'red' if severity == 'high' else 'orange' if severity == 'medium' else 'blue'}">
            {severity}
        </span>
    </p>
    <p><strong>Message:</strong> {message}</p>
</body>
</html>
"""
        
        return await self.send_notification(
            to=to,
            subject=subject,
            message=text_message,
            html_message=html_message
        )
    
    async def send_practice_notification(
        self, 
        to: List[str], 
        notification_type: str, 
        message: str,
        patient_id: Optional[str] = None
    ) -> bool:
        """Send practice notification"""
        subject = f"Practice Notification - {notification_type}"
        
        # Create text message
        text_message = f"""
Practice Notification

Type: {notification_type}
Message: {message}
"""
        if patient_id:
            text_message += f"Patient ID: {patient_id}\n"
        
        # Create HTML message
        html_message = f"""
<html>
<body>
    <h2>Practice Notification</h2>
    <p><strong>Type:</strong> {notification_type}</p>
    <p><strong>Message:</strong> {message}</p>
"""
        if patient_id:
            html_message += f"<p><strong>Patient ID:</strong> {patient_id}</p>"
        
        html_message += """
</body>
</html>
"""
        
        return await self.send_notification(
            to=to,
            subject=subject,
            message=text_message,
            html_message=html_message
        )


# Global email client instance
email_client: Optional[EmailClient] = None


def get_email_client() -> Optional[EmailClient]:
    """Get email client instance"""
    global email_client
    
    if email_client is None:
        # Check if email configuration is available
        if hasattr(settings, 'smtp_host') and settings.smtp_host:
            config = EmailConfig(
                smtp_host=settings.smtp_host,
                smtp_port=getattr(settings, 'smtp_port', 587),
                smtp_username=settings.smtp_username,
                smtp_password=settings.smtp_password,
                from_email=settings.from_email,
                from_name=getattr(settings, 'from_name', 'Rico Orchestrator')
            )
            email_client = EmailClient(config)
    
    return email_client


async def send_notification_email(
    to: List[str], 
    subject: str, 
    message: str,
    html_message: Optional[str] = None
) -> bool:
    """Send notification email using global client"""
    client = get_email_client()
    if not client:
        logger.warning("Email client not configured")
        return False
    
    return await client.send_notification(to, subject, message, html_message)
