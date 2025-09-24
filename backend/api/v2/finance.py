"""
Finance API: KPIs + Forecast (Mock)
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import uuid
import random


router = APIRouter(prefix="/v2/finance", tags=["v2-finance"])


# Pydantic Models
class KPI(BaseModel):
    """Key Performance Indicator"""
    id: str
    name: str
    value: float
    unit: str
    trend: str  # up, down, stable
    change_percent: float
    target: Optional[float] = None
    period: str  # daily, weekly, monthly, quarterly, yearly
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Forecast(BaseModel):
    """Financial forecast"""
    id: str
    metric: str
    current_value: float
    forecast_values: List[float]
    forecast_dates: List[datetime]
    confidence: float
    methodology: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FinancialReport(BaseModel):
    """Financial report"""
    id: str
    title: str
    period: str
    kpis: List[KPI]
    forecasts: List[Forecast]
    summary: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Mock data storage
kpis_storage: Dict[str, KPI] = {}
forecasts_storage: Dict[str, Forecast] = {}
reports_storage: Dict[str, FinancialReport] = {}


def generate_mock_kpis() -> List[KPI]:
    """Generate mock KPIs"""
    kpis = [
        KPI(
            id=str(uuid.uuid4()),
            name="Revenue",
            value=125000.0,
            unit="USD",
            trend="up",
            change_percent=12.5,
            target=150000.0,
            period="monthly"
        ),
        KPI(
            id=str(uuid.uuid4()),
            name="Customer Acquisition Cost",
            value=45.0,
            unit="USD",
            trend="down",
            change_percent=-8.2,
            target=40.0,
            period="monthly"
        ),
        KPI(
            id=str(uuid.uuid4()),
            name="Monthly Recurring Revenue",
            value=85000.0,
            unit="USD",
            trend="up",
            change_percent=15.3,
            target=100000.0,
            period="monthly"
        ),
        KPI(
            id=str(uuid.uuid4()),
            name="Churn Rate",
            value=3.2,
            unit="%",
            trend="down",
            change_percent=-0.5,
            target=2.5,
            period="monthly"
        ),
        KPI(
            id=str(uuid.uuid4()),
            name="Gross Margin",
            value=78.5,
            unit="%",
            trend="stable",
            change_percent=0.2,
            target=80.0,
            period="monthly"
        ),
        KPI(
            id=str(uuid.uuid4()),
            name="Operating Expenses",
            value=45000.0,
            unit="USD",
            trend="up",
            change_percent=5.1,
            target=40000.0,
            period="monthly"
        )
    ]
    
    # Store KPIs
    for kpi in kpis:
        kpis_storage[kpi.id] = kpi
    
    return kpis


def generate_mock_forecasts() -> List[Forecast]:
    """Generate mock forecasts"""
    base_date = datetime.utcnow()
    forecasts = []
    
    # Revenue forecast
    revenue_forecast = Forecast(
        id=str(uuid.uuid4()),
        metric="Revenue",
        current_value=125000.0,
        forecast_values=[130000.0, 135000.0, 140000.0, 145000.0, 150000.0],
        forecast_dates=[
            base_date + timedelta(days=30),
            base_date + timedelta(days=60),
            base_date + timedelta(days=90),
            base_date + timedelta(days=120),
            base_date + timedelta(days=150)
        ],
        confidence=0.85,
        methodology="Linear regression with seasonal adjustment"
    )
    forecasts.append(revenue_forecast)
    
    # MRR forecast
    mrr_forecast = Forecast(
        id=str(uuid.uuid4()),
        metric="Monthly Recurring Revenue",
        current_value=85000.0,
        forecast_values=[90000.0, 95000.0, 100000.0, 105000.0, 110000.0],
        forecast_dates=[
            base_date + timedelta(days=30),
            base_date + timedelta(days=60),
            base_date + timedelta(days=90),
            base_date + timedelta(days=120),
            base_date + timedelta(days=150)
        ],
        confidence=0.90,
        methodology="Growth rate analysis with cohort modeling"
    )
    forecasts.append(mrr_forecast)
    
    # Store forecasts
    for forecast in forecasts:
        forecasts_storage[forecast.id] = forecast
    
    return forecasts


@router.get("/kpis", response_model=List[KPI])
async def get_kpis(period: Optional[str] = None):
    """Get financial KPIs"""
    if not kpis_storage:
        generate_mock_kpis()
    
    kpis = list(kpis_storage.values())
    
    if period:
        kpis = [k for k in kpis if k.period == period]
    
    return kpis


@router.get("/kpis/{kpi_id}", response_model=KPI)
async def get_kpi(kpi_id: str):
    """Get a specific KPI by ID"""
    if kpi_id not in kpis_storage:
        raise HTTPException(status_code=404, detail="KPI not found")
    
    return kpis_storage[kpi_id]


@router.post("/kpis", response_model=KPI)
async def create_kpi(
    name: str,
    value: float,
    unit: str,
    trend: str,
    change_percent: float,
    target: Optional[float] = None,
    period: str = "monthly"
):
    """Create a new KPI"""
    kpi = KPI(
        id=str(uuid.uuid4()),
        name=name,
        value=value,
        unit=unit,
        trend=trend,
        change_percent=change_percent,
        target=target,
        period=period
    )
    
    kpis_storage[kpi.id] = kpi
    return kpi


@router.get("/forecasts", response_model=List[Forecast])
async def get_forecasts(metric: Optional[str] = None):
    """Get financial forecasts"""
    if not forecasts_storage:
        generate_mock_forecasts()
    
    forecasts = list(forecasts_storage.values())
    
    if metric:
        forecasts = [f for f in forecasts if f.metric == metric]
    
    return forecasts


@router.get("/forecasts/{forecast_id}", response_model=Forecast)
async def get_forecast(forecast_id: str):
    """Get a specific forecast by ID"""
    if forecast_id not in forecasts_storage:
        raise HTTPException(status_code=404, detail="Forecast not found")
    
    return forecasts_storage[forecast_id]


@router.post("/forecasts", response_model=Forecast)
async def create_forecast(
    metric: str,
    current_value: float,
    forecast_values: List[float],
    forecast_dates: List[datetime],
    confidence: float,
    methodology: str
):
    """Create a new forecast"""
    forecast = Forecast(
        id=str(uuid.uuid4()),
        metric=metric,
        current_value=current_value,
        forecast_values=forecast_values,
        forecast_dates=forecast_dates,
        confidence=confidence,
        methodology=methodology
    )
    
    forecasts_storage[forecast.id] = forecast
    return forecast


@router.get("/reports", response_model=List[FinancialReport])
async def get_reports(period: Optional[str] = None):
    """Get financial reports"""
    if not reports_storage:
        # Generate a mock report
        kpis = generate_mock_kpis()
        forecasts = generate_mock_forecasts()
        
        report = FinancialReport(
            id=str(uuid.uuid4()),
            title="Monthly Financial Report",
            period="monthly",
            kpis=kpis,
            forecasts=forecasts,
            summary="Strong revenue growth with improving margins. MRR showing consistent growth trend."
        )
        
        reports_storage[report.id] = report
    
    reports = list(reports_storage.values())
    
    if period:
        reports = [r for r in reports if r.period == period]
    
    return reports


@router.get("/reports/{report_id}", response_model=FinancialReport)
async def get_report(report_id: str):
    """Get a specific report by ID"""
    if report_id not in reports_storage:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return reports_storage[report_id]


@router.post("/reports", response_model=FinancialReport)
async def create_report(
    title: str,
    period: str,
    kpi_ids: List[str],
    forecast_ids: List[str],
    summary: str
):
    """Create a new financial report"""
    # Get KPIs and forecasts
    kpis = [kpis_storage[kpi_id] for kpi_id in kpi_ids if kpi_id in kpis_storage]
    forecasts = [forecasts_storage[forecast_id] for forecast_id in forecast_ids if forecast_id in forecasts_storage]
    
    report = FinancialReport(
        id=str(uuid.uuid4()),
        title=title,
        period=period,
        kpis=kpis,
        forecasts=forecasts,
        summary=summary
    )
    
    reports_storage[report.id] = report
    return report


@router.get("/dashboard")
async def get_dashboard():
    """Get financial dashboard data"""
    if not kpis_storage:
        generate_mock_kpis()
    if not forecasts_storage:
        generate_mock_forecasts()
    
    # Get key metrics
    revenue_kpi = next((k for k in kpis_storage.values() if k.name == "Revenue"), None)
    mrr_kpi = next((k for k in kpis_storage.values() if k.name == "Monthly Recurring Revenue"), None)
    churn_kpi = next((k for k in kpis_storage.values() if k.name == "Churn Rate"), None)
    
    # Get forecasts
    revenue_forecast = next((f for f in forecasts_storage.values() if f.metric == "Revenue"), None)
    mrr_forecast = next((f for f in forecasts_storage.values() if f.metric == "Monthly Recurring Revenue"), None)
    
    return {
        "key_metrics": {
            "revenue": revenue_kpi.dict() if revenue_kpi else None,
            "mrr": mrr_kpi.dict() if mrr_kpi else None,
            "churn_rate": churn_kpi.dict() if churn_kpi else None
        },
        "forecasts": {
            "revenue": revenue_forecast.dict() if revenue_forecast else None,
            "mrr": mrr_forecast.dict() if mrr_forecast else None
        },
        "summary": {
            "total_kpis": len(kpis_storage),
            "total_forecasts": len(forecasts_storage),
            "last_updated": datetime.utcnow().isoformat()
        }
    }
