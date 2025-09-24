'use client'

import { useState, useEffect } from 'react'
import { useAppStore } from '@/lib/store'
import { getPracticeStats } from '@/lib/api'
import { MetricCard } from '@/components/MetricCard'
import { Button } from '@/components/Button'
import { Users, Calendar, Euro, Plus } from 'lucide-react'

export default function PracticePage() {
  const { practiceStats, setPracticeStats, setLoading, loading, setError } = useAppStore()
  const [patients, setPatients] = useState<any[]>([])
  const [appointments, setAppointments] = useState<any[]>([])
  const [invoices, setInvoices] = useState<any[]>([])

  useEffect(() => {
    loadPracticeData()
  }, [])

  const loadPracticeData = async () => {
    try {
      setLoading('practice', true)
      const stats = await getPracticeStats()
      setPracticeStats(stats)
      
      // Mock data for demo
      setPatients([
        { id: 1, name: 'Max Mustermann', species: 'Hund', breed: 'Labrador', status: 'active' },
        { id: 2, name: 'Bella Schmidt', species: 'Katze', breed: 'Perser', status: 'active' },
        { id: 3, name: 'Rex Weber', species: 'Hund', breed: 'Dackel', status: 'inactive' },
      ])
      
      setAppointments([
        { id: 1, patient: 'Max Mustermann', date: '2024-01-15', time: '14:30', status: 'scheduled' },
        { id: 2, patient: 'Bella Schmidt', date: '2024-01-15', time: '16:00', status: 'confirmed' },
      ])
      
      setInvoices([
        { id: 1, patient: 'Max Mustermann', amount: 150.00, status: 'paid', due_date: '2024-01-10' },
        { id: 2, patient: 'Bella Schmidt', amount: 85.50, status: 'sent', due_date: '2024-01-20' },
        { id: 3, patient: 'Rex Weber', amount: 200.00, status: 'overdue', due_date: '2023-12-15' },
      ])
    } catch (error) {
      setError('Failed to load practice data')
    } finally {
      setLoading('practice', false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'inactive': return 'bg-gray-100 text-gray-800'
      case 'scheduled': return 'bg-blue-100 text-blue-800'
      case 'confirmed': return 'bg-green-100 text-green-800'
      case 'paid': return 'bg-green-100 text-green-800'
      case 'sent': return 'bg-yellow-100 text-yellow-800'
      case 'overdue': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Tierheilpraxis</h1>
          <p className="text-gray-600">Patienten, Termine und Rechnungen verwalten</p>
        </div>

        {/* Stats */}
        {practiceStats && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <MetricCard
              title="Aktive Patienten"
              value={practiceStats.patients.active}
              subtitle={`von ${practiceStats.patients.total} total`}
              icon={<Users className="h-5 w-5" />}
              status="info"
            />
            <MetricCard
              title="Termine heute"
              value={practiceStats.appointments_today}
              subtitle="geplant"
              icon={<Calendar className="h-5 w-5" />}
              status="info"
            />
            <MetricCard
              title="Offene Rechnungen"
              value={practiceStats.unpaid_invoices.count}
              subtitle={`${practiceStats.unpaid_invoices.amount_eur.toFixed(2)} €`}
              icon={<Euro className="h-5 w-5" />}
              status={practiceStats.unpaid_invoices.count > 0 ? 'warning' : 'success'}
            />
          </div>
        )}

        {/* Patients */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="p-6 border-b">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">Patienten</h2>
              <Button className="bg-green-600 hover:bg-green-700">
                <Plus className="h-4 w-4 mr-2" />
                Neuer Patient
              </Button>
            </div>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {patients.map((patient) => (
                <div key={patient.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                  <div>
                    <h3 className="font-semibold text-gray-900">{patient.name}</h3>
                    <p className="text-sm text-gray-600">{patient.species} - {patient.breed}</p>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(patient.status)}`}>
                    {patient.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Appointments */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="p-6 border-b">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">Termine</h2>
              <Button className="bg-blue-600 hover:bg-blue-700">
                <Plus className="h-4 w-4 mr-2" />
                Neuer Termin
              </Button>
            </div>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {appointments.map((appointment) => (
                <div key={appointment.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                  <div>
                    <h3 className="font-semibold text-gray-900">{appointment.patient}</h3>
                    <p className="text-sm text-gray-600">{appointment.date} um {appointment.time}</p>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(appointment.status)}`}>
                    {appointment.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Invoices */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">Rechnungen</h2>
              <Button className="bg-purple-600 hover:bg-purple-700">
                <Plus className="h-4 w-4 mr-2" />
                Neue Rechnung
              </Button>
            </div>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {invoices.map((invoice) => (
                <div key={invoice.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                  <div>
                    <h3 className="font-semibold text-gray-900">{invoice.patient}</h3>
                    <p className="text-sm text-gray-600">Fällig: {invoice.due_date}</p>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className="text-lg font-bold text-gray-900">
                      {invoice.amount.toFixed(2)} €
                    </span>
                    <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(invoice.status)}`}>
                      {invoice.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
