"""
Cashbot API: Scan → Findings → Dispatch Workflow
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from ...config.settings import settings
from ...providers.openai_client import OpenAIProvider
from ...providers.anthropic_client import AnthropicProvider
from ...providers.perplexity_client import PerplexityProvider
from ...orchestrator.auto_race import AutoRaceOrchestrator


router = APIRouter(prefix="/v2/cashbot", tags=["v2-cashbot"])


# Pydantic Models
class ScanRequest(BaseModel):
    """Cashbot scan request"""
    target: str  # URL, text, or identifier to scan
    scan_type: str = "financial"  # financial, security, compliance
    priority: str = "medium"  # low, medium, high, critical


class Finding(BaseModel):
    """Cashbot finding"""
    id: str
    scan_id: str
    type: str
    severity: str
    title: str
    description: str
    recommendation: str
    confidence: float
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScanResult(BaseModel):
    """Cashbot scan result"""
    id: str
    target: str
    scan_type: str
    priority: str
    status: str
    findings: List[Finding]
    summary: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class DispatchRequest(BaseModel):
    """Dispatch request"""
    scan_id: str
    action: str  # notify, escalate, auto_fix, manual_review
    recipients: List[str] = []
    message: Optional[str] = None


class DispatchResult(BaseModel):
    """Dispatch result"""
    id: str
    scan_id: str
    action: str
    status: str
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


# In-memory storage
scans_storage: Dict[str, ScanResult] = {}
findings_storage: Dict[str, Finding] = {}
dispatches_storage: Dict[str, DispatchResult] = {}


def get_providers():
    """Get configured providers"""
    providers = []
    
    if settings.openai_api_key:
        providers.append(OpenAIProvider(settings.openai_api_key))
    if settings.anthropic_api_key:
        providers.append(AnthropicProvider(settings.anthropic_api_key))
    if settings.perplexity_api_key:
        providers.append(PerplexityProvider(settings.perplexity_api_key))
    
    return providers


@router.post("/scan", response_model=ScanResult)
async def create_scan(request: ScanRequest):
    """Create a new cashbot scan"""
    scan_id = str(uuid.uuid4())
    
    # Initialize scan result
    scan_result = ScanResult(
        id=scan_id,
        target=request.target,
        scan_type=request.scan_type,
        priority=request.priority,
        status="running",
        findings=[],
        summary=""
    )
    
    scans_storage[scan_id] = scan_result
    
    try:
        providers = get_providers()
        if not providers:
            raise HTTPException(status_code=503, detail="No providers configured")
        
        # Create analysis prompt based on scan type
        if request.scan_type == "financial":
            prompt = f"""
            Analyze the following target for financial issues, risks, or opportunities:
            Target: {request.target}
            
            Please identify:
            1. Financial risks or red flags
            2. Potential cost savings opportunities
            3. Revenue optimization possibilities
            4. Compliance issues
            5. Security vulnerabilities related to finances
            
            Provide specific findings with severity levels (low, medium, high, critical) and actionable recommendations.
            """
        elif request.scan_type == "security":
            prompt = f"""
            Analyze the following target for security vulnerabilities:
            Target: {request.target}
            
            Please identify:
            1. Security vulnerabilities
            2. Access control issues
            3. Data protection concerns
            4. Authentication/authorization problems
            5. Network security issues
            
            Provide specific findings with severity levels and remediation steps.
            """
        else:  # compliance
            prompt = f"""
            Analyze the following target for compliance issues:
            Target: {request.target}
            
            Please identify:
            1. Regulatory compliance gaps
            2. Policy violations
            3. Documentation issues
            4. Process compliance problems
            5. Audit trail concerns
            
            Provide specific findings with severity levels and compliance recommendations.
            """
        
        # Use auto-race to get analysis
        orchestrator = AutoRaceOrchestrator(providers)
        race_result = await orchestrator.race(prompt)
        
        if not race_result.winner or not race_result.winner.success:
            raise HTTPException(status_code=500, detail="Analysis failed")
        
        # Parse findings from response
        analysis_content = race_result.winner.content
        findings = parse_findings_from_analysis(analysis_content, scan_id)
        
        # Update scan result
        scan_result.findings = findings
        scan_result.summary = generate_summary(findings)
        scan_result.status = "completed"
        scan_result.completed_at = datetime.utcnow()
        
        # Store findings
        for finding in findings:
            findings_storage[finding.id] = finding
        
        scans_storage[scan_id] = scan_result
        
        return scan_result
        
    except Exception as e:
        scan_result.status = "failed"
        scans_storage[scan_id] = scan_result
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up providers
        for provider in providers:
            if hasattr(provider, 'close'):
                await provider.close()


def parse_findings_from_analysis(content: str, scan_id: str) -> List[Finding]:
    """Parse findings from AI analysis content"""
    findings = []
    
    # Simple parsing logic - in production, use more sophisticated NLP
    lines = content.split('\n')
    current_finding = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Look for finding indicators
        if any(keyword in line.lower() for keyword in ['finding', 'issue', 'risk', 'vulnerability', 'problem']):
            if current_finding:
                findings.append(current_finding)
            
            # Extract severity and title
            severity = "medium"
            if any(word in line.lower() for word in ['critical', 'high']):
                severity = "high"
            elif any(word in line.lower() for word in ['low', 'minor']):
                severity = "low"
            
            current_finding = Finding(
                id=str(uuid.uuid4()),
                scan_id=scan_id,
                type="analysis",
                severity=severity,
                title=line[:100] + "..." if len(line) > 100 else line,
                description=line,
                recommendation="Review and address this finding",
                confidence=0.8
            )
        elif current_finding and line.startswith(('Recommendation:', 'Action:', 'Fix:')):
            current_finding.recommendation = line
        elif current_finding:
            current_finding.description += " " + line
    
    if current_finding:
        findings.append(current_finding)
    
    # If no structured findings, create a general one
    if not findings:
        findings.append(Finding(
            id=str(uuid.uuid4()),
            scan_id=scan_id,
            type="analysis",
            severity="medium",
            title="Analysis completed",
            description=content[:500] + "..." if len(content) > 500 else content,
            recommendation="Review the analysis results",
            confidence=0.7
        ))
    
    return findings


def generate_summary(findings: List[Finding]) -> str:
    """Generate summary from findings"""
    if not findings:
        return "No findings identified"
    
    critical_count = len([f for f in findings if f.severity == "critical"])
    high_count = len([f for f in findings if f.severity == "high"])
    medium_count = len([f for f in findings if f.severity == "medium"])
    low_count = len([f for f in findings if f.severity == "low"])
    
    return f"Scan completed: {len(findings)} findings identified ({critical_count} critical, {high_count} high, {medium_count} medium, {low_count} low)"


@router.get("/scans/{scan_id}", response_model=ScanResult)
async def get_scan(scan_id: str):
    """Get a specific scan by ID"""
    if scan_id not in scans_storage:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    return scans_storage[scan_id]


@router.get("/scans", response_model=List[ScanResult])
async def list_scans(limit: int = 50, status: Optional[str] = None):
    """List all scans"""
    scans = list(scans_storage.values())
    
    if status:
        scans = [s for s in scans if s.status == status]
    
    # Sort by creation time (newest first)
    scans.sort(key=lambda x: x.created_at, reverse=True)
    return scans[:limit]


@router.get("/findings/{finding_id}", response_model=Finding)
async def get_finding(finding_id: str):
    """Get a specific finding by ID"""
    if finding_id not in findings_storage:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    return findings_storage[finding_id]


@router.get("/findings", response_model=List[Finding])
async def list_findings(scan_id: Optional[str] = None, severity: Optional[str] = None):
    """List findings"""
    findings = list(findings_storage.values())
    
    if scan_id:
        findings = [f for f in findings if f.scan_id == scan_id]
    
    if severity:
        findings = [f for f in findings if f.severity == severity]
    
    # Sort by creation time (newest first)
    findings.sort(key=lambda x: x.created_at, reverse=True)
    return findings


@router.post("/dispatch", response_model=DispatchResult)
async def create_dispatch(request: DispatchRequest):
    """Create a dispatch for a scan"""
    if request.scan_id not in scans_storage:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    dispatch_id = str(uuid.uuid4())
    
    # Create dispatch result
    dispatch_result = DispatchResult(
        id=dispatch_id,
        scan_id=request.scan_id,
        action=request.action,
        status="pending",
        message=request.message or f"Dispatch created for scan {request.scan_id}"
    )
    
    dispatches_storage[dispatch_id] = dispatch_result
    
    # Simulate dispatch processing
    try:
        # In production, integrate with actual notification systems
        if request.action == "notify":
            dispatch_result.status = "sent"
            dispatch_result.message = f"Notifications sent to {len(request.recipients)} recipients"
        elif request.action == "escalate":
            dispatch_result.status = "escalated"
            dispatch_result.message = "Issue escalated to management"
        elif request.action == "auto_fix":
            dispatch_result.status = "attempted"
            dispatch_result.message = "Automatic fix attempted"
        else:  # manual_review
            dispatch_result.status = "queued"
            dispatch_result.message = "Queued for manual review"
        
        dispatches_storage[dispatch_id] = dispatch_result
        
        return dispatch_result
        
    except Exception as e:
        dispatch_result.status = "failed"
        dispatch_result.message = f"Dispatch failed: {str(e)}"
        dispatches_storage[dispatch_id] = dispatch_result
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dispatches/{dispatch_id}", response_model=DispatchResult)
async def get_dispatch(dispatch_id: str):
    """Get a specific dispatch by ID"""
    if dispatch_id not in dispatches_storage:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    
    return dispatches_storage[dispatch_id]


@router.get("/dispatches", response_model=List[DispatchResult])
async def list_dispatches(scan_id: Optional[str] = None, status: Optional[str] = None):
    """List dispatches"""
    dispatches = list(dispatches_storage.values())
    
    if scan_id:
        dispatches = [d for d in dispatches if d.scan_id == scan_id]
    
    if status:
        dispatches = [d for d in dispatches if d.status == status]
    
    # Sort by creation time (newest first)
    dispatches.sort(key=lambda x: x.created_at, reverse=True)
    return dispatches