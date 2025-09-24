from sqlmodel import SQLModel, Field
from datetime import datetime, date
from typing import Optional
from enum import Enum

class PatientStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    archived = "archived"

class AppointmentStatus(str, Enum):
    scheduled = "scheduled"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"

class InvoiceStatus(str, Enum):
    draft = "draft"
    sent = "sent"
    paid = "paid"
    overdue = "overdue"
    cancelled = "cancelled"

class Patient(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    species: Optional[str] = None  # Hund, Katze, Pferd, etc.
    breed: Optional[str] = None
    age: Optional[int] = None
    status: PatientStatus = PatientStatus.active
    created_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

class Appointment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="patient.id")
    date: date
    time: str  # "14:30"
    duration_minutes: int = 60
    status: AppointmentStatus = AppointmentStatus.scheduled
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Invoice(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="patient.id")
    appointment_id: Optional[int] = Field(foreign_key="appointment.id", default=None)
    invoice_number: str
    amount_eur: float
    status: InvoiceStatus = InvoiceStatus.draft
    due_date: date
    created_at: datetime = Field(default_factory=datetime.utcnow)
    paid_at: Optional[datetime] = None
    notes: Optional[str] = None
