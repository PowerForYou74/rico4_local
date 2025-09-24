from fastapi import APIRouter, Depends
from sqlmodel import select, func, and_
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
from .models import Transaction, Forecast, TransactionType
from ..core.db import session

router = APIRouter(prefix="/v2/finance")

@router.get("/kpis")
def get_finance_kpis(s=Depends(session)):
    """Finanz-KPIs für Dashboard"""
    today = date.today()
    this_month = today.replace(day=1)
    last_month = (this_month - timedelta(days=1)).replace(day=1)
    
    # MRR (Monthly Recurring Revenue) - vereinfacht
    mrr = s.exec(
        select(func.sum(Transaction.amount_eur))
        .where(Transaction.type == TransactionType.revenue)
        .where(Transaction.date >= this_month)
    ).first() or 0
    
    # ARR (Annual Recurring Revenue) - MRR * 12
    arr = float(mrr) * 12 if mrr else 0.0
    
    # Cash on Hand (vereinfacht - letzte 30 Tage)
    cash_in = s.exec(
        select(func.sum(Transaction.amount_eur))
        .where(Transaction.type == TransactionType.revenue)
        .where(Transaction.date >= today - timedelta(days=30))
    ).first() or 0
    
    cash_out = s.exec(
        select(func.sum(Transaction.amount_eur))
        .where(Transaction.type == TransactionType.expense)
        .where(Transaction.date >= today - timedelta(days=30))
    ).first() or 0
    
    cash_on_hand = float(cash_in) - float(cash_out) if cash_in and cash_out else 0.0
    
    # Burn Rate (monatliche Ausgaben)
    burn_rate = s.exec(
        select(func.sum(Transaction.amount_eur))
        .where(Transaction.type == TransactionType.expense)
        .where(Transaction.date >= this_month)
    ).first() or 0
    
    # Runway (wie lange reicht das Geld)
    runway_days = 0
    if burn_rate and burn_rate > 0:
        runway_days = int((cash_on_hand / float(burn_rate)) * 30) if cash_on_hand > 0 else 0
    
    return {
        "mrr": float(mrr) if mrr else 0.0,
        "arr": arr,
        "cash_on_hand": cash_on_hand,
        "burn_rate": float(burn_rate) if burn_rate else 0.0,
        "runway_days": runway_days
    }

@router.get("/forecast")
def get_forecast(s=Depends(session)):
    """12-Monats Forecast"""
    today = date.today()
    monthly_data = []
    
    # Generiere 12 Monate Forecast
    for i in range(12):
        forecast_date = today.replace(day=1) + timedelta(days=32*i)
        month_str = forecast_date.strftime("%Y-%m")
        
        # Vereinfachte Forecast-Logik
        base_revenue = 5000.0  # Basis-Umsatz
        growth_rate = 0.05    # 5% Wachstum pro Monat
        revenue = base_revenue * (1 + growth_rate) ** i
        
        base_costs = 3000.0   # Basis-Kosten
        cost_growth = 0.03    # 3% Kostenwachstum
        costs = base_costs * (1 + cost_growth) ** i
        
        profit = revenue - costs
        
        monthly_data.append({
            "month": month_str,
            "revenue": round(revenue, 2),
            "costs": round(costs, 2),
            "profit": round(profit, 2)
        })
    
    return {
        "monthly": monthly_data,
        "assumptions": {
            "revenue_growth_rate": 0.05,
            "cost_growth_rate": 0.03,
            "base_revenue": 5000.0,
            "base_costs": 3000.0
        }
    }

@router.get("/transactions")
def list_transactions(s=Depends(session)):
    """Letzte Transaktionen"""
    return s.exec(
        select(Transaction)
        .order_by(Transaction.date.desc())
        .limit(50)
    ).all()

@router.post("/transactions")
def create_transaction(transaction: Transaction, s=Depends(session)):
    s.add(transaction)
    s.commit()
    s.refresh(transaction)
    return transaction
