"""
Practice API: Patient, Appointment, Invoice CRUD (Mock Storage)
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import uuid
import random


router = APIRouter(prefix="/v2/practice", tags=["v2-practice"])


# Pydantic Models
class Patient(BaseModel):
    """Patient model"""
    id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    date_of_birth: datetime
    address: Optional[str] = None
    insurance_info: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Appointment(BaseModel):
    """Appointment model"""
    id: str
    patient_id: str
    doctor_name: str
    appointment_date: datetime
    duration_minutes: int = 30
    status: str = "scheduled"  # scheduled, completed, cancelled, no_show
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Invoice(BaseModel):
    """Invoice model"""
    id: str
    patient_id: str
    appointment_id: Optional[str] = None
    amount: float
    currency: str = "USD"
    status: str = "pending"  # pending, paid, overdue, cancelled
    due_date: datetime
    description: str
    line_items: List[Dict[str, Any]] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Mock storage
patients_storage: Dict[str, Patient] = {}
appointments_storage: Dict[str, Appointment] = {}
invoices_storage: Dict[str, Invoice] = {}


def generate_mock_data():
    """Generate mock data for testing"""
    # Generate patients
    patient_names = [
        ("John", "Doe", "john.doe@email.com", "+1-555-0101"),
        ("Jane", "Smith", "jane.smith@email.com", "+1-555-0102"),
        ("Bob", "Johnson", "bob.johnson@email.com", "+1-555-0103"),
        ("Alice", "Brown", "alice.brown@email.com", "+1-555-0104"),
        ("Charlie", "Wilson", "charlie.wilson@email.com", "+1-555-0105")
    ]
    
    for first_name, last_name, email, phone in patient_names:
        patient = Patient(
            id=str(uuid.uuid4()),
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            date_of_birth=datetime.utcnow() - timedelta(days=random.randint(18*365, 80*365)),
            address=f"{random.randint(100, 999)} Main St, City, State",
            insurance_info=f"Insurance Provider {random.randint(1, 5)}"
        )
        patients_storage[patient.id] = patient
    
    # Generate appointments
    doctors = ["Dr. Smith", "Dr. Johnson", "Dr. Brown", "Dr. Wilson", "Dr. Davis"]
    patient_ids = list(patients_storage.keys())
    
    for i in range(10):
        appointment = Appointment(
            id=str(uuid.uuid4()),
            patient_id=random.choice(patient_ids),
            doctor_name=random.choice(doctors),
            appointment_date=datetime.utcnow() + timedelta(days=random.randint(-30, 30)),
            duration_minutes=random.choice([30, 45, 60]),
            status=random.choice(["scheduled", "completed", "cancelled"]),
            notes=f"Appointment notes {i+1}"
        )
        appointments_storage[appointment.id] = appointment
    
    # Generate invoices
    for i in range(15):
        invoice = Invoice(
            id=str(uuid.uuid4()),
            patient_id=random.choice(patient_ids),
            appointment_id=random.choice(list(appointments_storage.keys())) if appointments_storage else None,
            amount=round(random.uniform(50, 500), 2),
            status=random.choice(["pending", "paid", "overdue"]),
            due_date=datetime.utcnow() + timedelta(days=random.randint(-10, 30)),
            description=f"Medical services - Invoice {i+1}",
            line_items=[
                {"description": "Consultation", "amount": round(random.uniform(50, 200), 2)},
                {"description": "Lab Work", "amount": round(random.uniform(25, 100), 2)}
            ]
        )
        invoices_storage[invoice.id] = invoice


# Patient endpoints
@router.post("/patients", response_model=Patient)
async def create_patient(
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
    date_of_birth: datetime,
    address: Optional[str] = None,
    insurance_info: Optional[str] = None
):
    """Create a new patient"""
    patient = Patient(
        id=str(uuid.uuid4()),
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        date_of_birth=date_of_birth,
        address=address,
        insurance_info=insurance_info
    )
    
    patients_storage[patient.id] = patient
    return patient


@router.get("/patients/{patient_id}", response_model=Patient)
async def get_patient(patient_id: str):
    """Get a specific patient by ID"""
    if patient_id not in patients_storage:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return patients_storage[patient_id]


@router.get("/patients", response_model=List[Patient])
async def list_patients(limit: int = 50, offset: int = 0):
    """List all patients"""
    if not patients_storage:
        generate_mock_data()
    
    patients = list(patients_storage.values())
    return patients[offset:offset + limit]


@router.put("/patients/{patient_id}", response_model=Patient)
async def update_patient(
    patient_id: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    address: Optional[str] = None,
    insurance_info: Optional[str] = None
):
    """Update a patient"""
    if patient_id not in patients_storage:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    patient = patients_storage[patient_id]
    
    if first_name is not None:
        patient.first_name = first_name
    if last_name is not None:
        patient.last_name = last_name
    if email is not None:
        patient.email = email
    if phone is not None:
        patient.phone = phone
    if address is not None:
        patient.address = address
    if insurance_info is not None:
        patient.insurance_info = insurance_info
    
    patient.updated_at = datetime.utcnow()
    patients_storage[patient_id] = patient
    
    return patient


@router.delete("/patients/{patient_id}")
async def delete_patient(patient_id: str):
    """Delete a patient"""
    if patient_id not in patients_storage:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    del patients_storage[patient_id]
    return {"message": "Patient deleted successfully"}


# Appointment endpoints
@router.post("/appointments", response_model=Appointment)
async def create_appointment(
    patient_id: str,
    doctor_name: str,
    appointment_date: datetime,
    duration_minutes: int = 30,
    notes: Optional[str] = None
):
    """Create a new appointment"""
    if patient_id not in patients_storage:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    appointment = Appointment(
        id=str(uuid.uuid4()),
        patient_id=patient_id,
        doctor_name=doctor_name,
        appointment_date=appointment_date,
        duration_minutes=duration_minutes,
        notes=notes
    )
    
    appointments_storage[appointment.id] = appointment
    return appointment


@router.get("/appointments/{appointment_id}", response_model=Appointment)
async def get_appointment(appointment_id: str):
    """Get a specific appointment by ID"""
    if appointment_id not in appointments_storage:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    return appointments_storage[appointment_id]


@router.get("/appointments", response_model=List[Appointment])
async def list_appointments(
    patient_id: Optional[str] = None,
    doctor_name: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List appointments with optional filters"""
    if not appointments_storage:
        generate_mock_data()
    
    appointments = list(appointments_storage.values())
    
    if patient_id:
        appointments = [a for a in appointments if a.patient_id == patient_id]
    if doctor_name:
        appointments = [a for a in appointments if a.doctor_name == doctor_name]
    if status:
        appointments = [a for a in appointments if a.status == status]
    
    # Sort by appointment date
    appointments.sort(key=lambda x: x.appointment_date)
    return appointments[offset:offset + limit]


@router.put("/appointments/{appointment_id}", response_model=Appointment)
async def update_appointment(
    appointment_id: str,
    doctor_name: Optional[str] = None,
    appointment_date: Optional[datetime] = None,
    duration_minutes: Optional[int] = None,
    status: Optional[str] = None,
    notes: Optional[str] = None
):
    """Update an appointment"""
    if appointment_id not in appointments_storage:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    appointment = appointments_storage[appointment_id]
    
    if doctor_name is not None:
        appointment.doctor_name = doctor_name
    if appointment_date is not None:
        appointment.appointment_date = appointment_date
    if duration_minutes is not None:
        appointment.duration_minutes = duration_minutes
    if status is not None:
        appointment.status = status
    if notes is not None:
        appointment.notes = notes
    
    appointment.updated_at = datetime.utcnow()
    appointments_storage[appointment_id] = appointment
    
    return appointment


@router.delete("/appointments/{appointment_id}")
async def delete_appointment(appointment_id: str):
    """Delete an appointment"""
    if appointment_id not in appointments_storage:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    del appointments_storage[appointment_id]
    return {"message": "Appointment deleted successfully"}


# Invoice endpoints
@router.post("/invoices", response_model=Invoice)
async def create_invoice(
    patient_id: str,
    amount: float,
    description: str,
    due_date: datetime,
    appointment_id: Optional[str] = None,
    line_items: List[Dict[str, Any]] = []
):
    """Create a new invoice"""
    if patient_id not in patients_storage:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    if appointment_id and appointment_id not in appointments_storage:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    invoice = Invoice(
        id=str(uuid.uuid4()),
        patient_id=patient_id,
        appointment_id=appointment_id,
        amount=amount,
        due_date=due_date,
        description=description,
        line_items=line_items
    )
    
    invoices_storage[invoice.id] = invoice
    return invoice


@router.get("/invoices/{invoice_id}", response_model=Invoice)
async def get_invoice(invoice_id: str):
    """Get a specific invoice by ID"""
    if invoice_id not in invoices_storage:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return invoices_storage[invoice_id]


@router.get("/invoices", response_model=List[Invoice])
async def list_invoices(
    patient_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List invoices with optional filters"""
    if not invoices_storage:
        generate_mock_data()
    
    invoices = list(invoices_storage.values())
    
    if patient_id:
        invoices = [i for i in invoices if i.patient_id == patient_id]
    if status:
        invoices = [i for i in invoices if i.status == status]
    
    # Sort by creation date
    invoices.sort(key=lambda x: x.created_at, reverse=True)
    return invoices[offset:offset + limit]


@router.put("/invoices/{invoice_id}", response_model=Invoice)
async def update_invoice(
    invoice_id: str,
    amount: Optional[float] = None,
    status: Optional[str] = None,
    due_date: Optional[datetime] = None,
    description: Optional[str] = None,
    line_items: Optional[List[Dict[str, Any]]] = None
):
    """Update an invoice"""
    if invoice_id not in invoices_storage:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice = invoices_storage[invoice_id]
    
    if amount is not None:
        invoice.amount = amount
    if status is not None:
        invoice.status = status
    if due_date is not None:
        invoice.due_date = due_date
    if description is not None:
        invoice.description = description
    if line_items is not None:
        invoice.line_items = line_items
    
    invoice.updated_at = datetime.utcnow()
    invoices_storage[invoice_id] = invoice
    
    return invoice


@router.delete("/invoices/{invoice_id}")
async def delete_invoice(invoice_id: str):
    """Delete an invoice"""
    if invoice_id not in invoices_storage:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    del invoices_storage[invoice_id]
    return {"message": "Invoice deleted successfully"}


@router.get("/dashboard")
async def get_practice_dashboard():
    """Get practice dashboard data"""
    if not patients_storage:
        generate_mock_data()
    
    # Calculate statistics
    total_patients = len(patients_storage)
    total_appointments = len(appointments_storage)
    total_invoices = len(invoices_storage)
    
    # Appointment status breakdown
    appointment_statuses = {}
    for appointment in appointments_storage.values():
        status = appointment.status
        appointment_statuses[status] = appointment_statuses.get(status, 0) + 1
    
    # Invoice status breakdown
    invoice_statuses = {}
    total_revenue = 0
    for invoice in invoices_storage.values():
        status = invoice.status
        invoice_statuses[status] = invoice_statuses.get(status, 0) + 1
        if status == "paid":
            total_revenue += invoice.amount
    
    # Upcoming appointments (next 7 days)
    upcoming_date = datetime.utcnow() + timedelta(days=7)
    upcoming_appointments = [
        a for a in appointments_storage.values()
        if a.appointment_date <= upcoming_date and a.status == "scheduled"
    ]
    
    return {
        "summary": {
            "total_patients": total_patients,
            "total_appointments": total_appointments,
            "total_invoices": total_invoices,
            "total_revenue": round(total_revenue, 2)
        },
        "appointment_statuses": appointment_statuses,
        "invoice_statuses": invoice_statuses,
        "upcoming_appointments": len(upcoming_appointments),
        "last_updated": datetime.utcnow().isoformat()
    }
