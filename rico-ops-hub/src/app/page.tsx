'use client'

import { useEffect, useState } from 'react'
import { StatusDot } from '@/components/StatusDot'
import { MetricCard } from '@/components/MetricCard'
import { Button } from '@/components/Button'
import { Activity, Users, Euro, TrendingUp, Brain, AlertCircle, RefreshCw } from 'lucide-react'

interface HealthStatus {
  openai: string
  claude: string
  perplexity: string
  env_source: string
  models: {
    openai: string
    claude: string
    perplexity: string
  }
  latency: {
    openai: number
    claude: number
    perplexity: number
  }
}

interface PracticeStats {
  patients: {
    total: number
    active: number
  }
  appointments_today: number
  unpaid_invoices: {
    count: number
    amount_eur: number
  }
}

interface FinanceKPIs {
  mrr: number
  arr: number
  cash_on_hand: number
  burn_rate: number
  runway_days: number
}

interface CashbotFinding {
  id: number
  title: string
  idea: string
  steps: string[]
  potential_eur: number
  effort: string
  risk: string
  timeframe: string
  status: string
  provider: string
  duration_s: number
  created_at: string
  dispatched_at?: string
}

export default function HomePage() {
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null)
  const [practiceStats, setPracticeStats] = useState<PracticeStats | null>(null)
  const [financeKPIs, setFinanceKPIs] = useState<FinanceKPIs | null>(null)
  const [cashbotFindings, setCashbotFindings] = useState<CashbotFinding[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      // Health Status
      const healthResponse = await fetch(`${API_BASE}/check-keys`)
      if (healthResponse.ok) {
        const health = await healthResponse.json()
        setHealthStatus(health)
      }

      // Practice Stats
      const practiceResponse = await fetch(`${API_BASE}/v2/practice/stats`)
      if (practiceResponse.ok) {
        const practice = await practiceResponse.json()
        setPracticeStats(practice)
      }

      // Finance KPIs
      const financeResponse = await fetch(`${API_BASE}/v2/finance/kpis`)
      if (financeResponse.ok) {
        const finance = await financeResponse.json()
        setFinanceKPIs(finance)
      }

      // Cashbot Findings
      const cashbotResponse = await fetch(`${API_BASE}/v2/cashbot/findings`)
      if (cashbotResponse.ok) {
        const findings = await cashbotResponse.json()
        setCashbotFindings(findings)
      }
    } catch (err) {
      setError('Fehler beim Laden der Daten')
      console.error('Error loading data:', err)
    } finally {
      setLoading(false)
    }
  }

  const triggerCashbotScan = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE}/v2/cashbot/scan`, {
        method: 'POST'
      })
      const result = await response.json()
      if (result.status === 'success') {
        await loadData() // Reload findings
        alert(`Cashbot Scan erfolgreich! Finding: ${result.title}`)
      } else {
        alert('Cashbot Scan fehlgeschlagen')
      }
    } catch (err) {
      console.error('Error triggering scan:', err)
      alert('Fehler beim Cashbot Scan')
    } finally {
      setLoading(false)
    }
  }

  const getHealthCount = () => {
    if (!healthStatus) return { ok: 0, total: 3 }
    const providers = [healthStatus.openai, healthStatus.claude, healthStatus.perplexity]
    const ok = providers.filter(status => status === 'OK').length
    return { ok, total: providers.length }
  }

  const healthCount = getHealthCount()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">RICO 4.0 Ops Hub</h1>
              <p className="text-gray-600">Produktionsreife Rico-Zentrale</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <StatusDot status={healthCount.ok === healthCount.total ? 'ok' : 'warning'} />
                <span className="text-sm text-gray-600">
                  {healthCount.ok}/{healthCount.total} Provider OK
                </span>
              </div>
              <Button onClick={loadData} disabled={loading}>
                <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Aktualisieren
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        {/* Health Status */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">System Health</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {healthStatus && (
              <>
                <MetricCard
                  title="OpenAI"
                  value={healthStatus.openai}
                  subtitle={`${healthStatus.latency.openai}ms`}
                  icon={<Brain className="h-5 w-5" />}
                  status={healthStatus.openai === 'OK' ? 'success' : 'error'}
                />
                <MetricCard
                  title="Claude"
                  value={healthStatus.claude}
                  subtitle={`${healthStatus.latency.claude}ms`}
                  icon={<Brain className="h-5 w-5" />}
                  status={healthStatus.claude === 'OK' ? 'success' : 'error'}
                />
                <MetricCard
                  title="Perplexity"
                  value={healthStatus.perplexity}
                  subtitle={`${healthStatus.latency.perplexity}ms`}
                  icon={<Brain className="h-5 w-5" />}
                  status={healthStatus.perplexity === 'OK' ? 'success' : 'error'}
                />
              </>
            )}
          </div>
        </div>

        {/* Practice KPIs */}
        {practiceStats && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Tierheilpraxis</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
                icon={<Activity className="h-5 w-5" />}
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
          </div>
        )}

        {/* Finance KPIs */}
        {financeKPIs && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Finanz-KPIs</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <MetricCard
                title="MRR"
                value={`${financeKPIs.mrr.toFixed(0)} €`}
                subtitle="Monatlich"
                icon={<TrendingUp className="h-5 w-5" />}
                status="success"
              />
              <MetricCard
                title="ARR"
                value={`${financeKPIs.arr.toFixed(0)} €`}
                subtitle="Jährlich"
                icon={<TrendingUp className="h-5 w-5" />}
                status="success"
              />
              <MetricCard
                title="Cash on Hand"
                value={`${financeKPIs.cash_on_hand.toFixed(0)} €`}
                subtitle="Verfügbar"
                icon={<Euro className="h-5 w-5" />}
                status="info"
              />
              <MetricCard
                title="Runway"
                value={`${financeKPIs.runway_days} Tage`}
                subtitle="Verbleibend"
                icon={<AlertCircle className="h-5 w-5" />}
                status={financeKPIs.runway_days > 90 ? 'success' : financeKPIs.runway_days > 30 ? 'warning' : 'error'}
              />
            </div>
          </div>
        )}

        {/* Cashbot Findings */}
        {cashbotFindings.length > 0 && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Cashbot Findings</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {cashbotFindings.slice(0, 6).map((finding) => (
                <div key={finding.id} className="bg-white p-4 rounded-lg shadow border">
                  <h3 className="font-semibold text-gray-900">{finding.title}</h3>
                  <p className="text-sm text-gray-600 mt-1">{finding.idea}</p>
                  <div className="flex justify-between items-center mt-3">
                    <span className="text-lg font-bold text-green-600">
                      {finding.potential_eur.toFixed(0)} €
                    </span>
                    <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                      {finding.timeframe}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button onClick={triggerCashbotScan} disabled={loading} className="w-full">
              <Brain className="h-4 w-4 mr-2" />
              Cashbot Scan
            </Button>
            <Button onClick={loadData} disabled={loading} className="w-full">
              <RefreshCw className="h-4 w-4 mr-2" />
              Aktualisieren
            </Button>
            <Button 
              onClick={() => window.open('http://localhost:8000/api/v1/docs', '_blank')} 
              className="w-full"
            >
              <TrendingUp className="h-4 w-4 mr-2" />
              API Docs
            </Button>
            <Button 
              onClick={() => window.open('http://localhost:8501', '_blank')} 
              className="w-full"
            >
              <Activity className="h-4 w-4 mr-2" />
              Streamlit
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}