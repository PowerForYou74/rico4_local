from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum

class FindingPriority(str, Enum):
    sofort = "sofort"        # Sofort umsetzbar
    kurzfristig = "kurzfristig"  # 1-4 Wochen
    mittel = "mittel"        # 1-3 Monate

class FindingStatus(str, Enum):
    new = "new"
    in_progress = "in_progress"
    completed = "completed"
    dismissed = "dismissed"

class CashbotFinding(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    idea: str
    steps: str  # JSON string mit Schritten
    potential_eur: float
    effort: str  # "low", "medium", "high"
    risk: str    # "low", "medium", "high"
    timeframe: FindingPriority
    status: FindingStatus = FindingStatus.new
    source_hints: str  # JSON string mit Quellen
    provider: str      # "openai", "claude", "perplexity"
    duration_s: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    dispatched_at: Optional[datetime] = None

class CashbotConfig(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    interval_cron: str = "0 */6 * * *"  # Alle 6 Stunden
    providers_enabled: str = "openai,claude"  # JSON string
    online_capable: bool = False
    last_scan: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
