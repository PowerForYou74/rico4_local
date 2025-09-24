from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, func
from datetime import datetime, date, timedelta
from .models import Patient, Appointment, Invoice, PatientStatus, AppointmentStatus, InvoiceStatus
from ..core.db import session

router = APIRouter(prefix="/v2/practice")

# Stats
@router.get("/stats")
def get_stats(s=Depends(session)):
    """Practice KPIs für Dashboard"""
    today = date.today()
    
    # Patienten
    total_patients = s.exec(select(func.count(Patient.id))).first() or 0
    active_patients = s.exec(select(func.count(Patient.id)).where(Patient.status == PatientStatus.active)).first() or 0
    
    # Termine heute
    appointments_today = s.exec(
        select(func.count(Appointment.id))
        .where(Appointment.date == today)
        .where(Appointment.status.in_([AppointmentStatus.scheduled, AppointmentStatus.confirmed]))
    ).first() or 0
    
    # Unbezahlte Rechnungen
    unpaid_invoices = s.exec(
        select(func.count(Invoice.id))
        .where(Invoice.status.in_([InvoiceStatus.sent, InvoiceStatus.overdue]))
    ).first() or 0
    
    unpaid_amount = s.exec(
        select(func.sum(Invoice.amount_eur))
        .where(Invoice.status.in_([InvoiceStatus.sent, InvoiceStatus.overdue]))
    ).first() or 0
    
    return {
        "patients": {
            "total": total_patients,
            "active": active_patients
        },
        "appointments_today": appointments_today,
        "unpaid_invoices": {
            "count": unpaid_invoices,
            "amount_eur": float(unpaid_amount) if unpaid_amount else 0.0
        }
    }

# Patients
@router.get("/patients")
def list_patients(s=Depends(session)):
    return s.exec(select(Patient).order_by(Patient.name)).all()

@router.post("/patients")
def create_patient(patient: Patient, s=Depends(session)):
    s.add(patient)
    s.commit()
    s.refresh(patient)
    return patient

@router.get("/patients/{patient_id}")
def get_patient(patient_id: int, s=Depends(session)):
    patient = s.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

# Appointments
@router.get("/appointments")
def list_appointments(s=Depends(session)):
    return s.exec(select(Appointment).order_by(Appointment.date, Appointment.time)).all()

@router.post("/appointments")
def create_appointment(appointment: Appointment, s=Depends(session)):
    s.add(appointment)
    s.commit()
    s.refresh(appointment)
    return appointment

@router.get("/appointments/{appointment_id}")
def get_appointment(appointment_id: int, s=Depends(session)):
    appointment = s.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment

# Invoices
@router.get("/invoices")
def list_invoices(s=Depends(session)):
    return s.exec(select(Invoice).order_by(Invoice.created_at.desc())).all()

@router.post("/invoices")
def create_invoice(invoice: Invoice, s=Depends(session)):
    s.add(invoice)
    s.commit()
    s.refresh(invoice)
    return invoice

@router.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: int, s=Depends(session)):
    invoice = s.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@router.post("/invoices/{invoice_id}/mark_paid")
def mark_invoice_paid(invoice_id: int, s=Depends(session)):
    invoice = s.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice.status = InvoiceStatus.paid
    invoice.paid_at = datetime.utcnow()
    s.add(invoice)
    s.commit()
    return {"status": "paid", "paid_at": invoice.paid_at}
