from sqlmodel import SQLModel, Field
from datetime import datetime, date
from typing import Optional, List
from enum import Enum

class TransactionType(str, Enum):
    revenue = "revenue"
    expense = "expense"
    investment = "investment"

class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: date
    amount_eur: float
    type: TransactionType
    category: str  # "consultation", "medication", "rent", "marketing", etc.
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Forecast(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    month: str  # "2024-01"
    revenue_forecast: float
    cost_forecast: float
    assumptions: str  # JSON string
    created_at: datetime = Field(default_factory=datetime.utcnow)
