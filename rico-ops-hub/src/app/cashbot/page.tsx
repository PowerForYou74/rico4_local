'use client'

import { useState, useEffect } from 'react'
import { useAppStore } from '@/lib/store'
import { getCashbotFindings, triggerCashbotScan, dispatchCashbotFinding } from '@/lib/api'
import { Button } from '@/components/Button'
import { StatusDot } from '@/components/StatusDot'
import { TrendingUp, Play, Send, Clock, Euro, AlertCircle } from 'lucide-react'

export default function CashbotPage() {
  const { cashbotFindings, setCashbotFindings, setLoading, loading, setError } = useAppStore()
  const [scanning, setScanning] = useState(false)

  useEffect(() => {
    loadFindings()
  }, [])

  const loadFindings = async () => {
    try {
      setLoading('cashbot', true)
      const findings = await getCashbotFindings()
      setCashbotFindings(findings)
    } catch (error) {
      setError('Failed to load cashbot findings')
    } finally {
      setLoading('cashbot', false)
    }
  }

  const handleScan = async () => {
    try {
      setScanning(true)
      const result = await triggerCashbotScan()
      if (result.status === 'success') {
        await loadFindings() // Reload findings
      }
    } catch (error) {
      setError('Failed to trigger cashbot scan')
    } finally {
      setScanning(false)
    }
  }

  const handleDispatch = async (findingId: number) => {
    try {
      await dispatchCashbotFinding(findingId)
      await loadFindings() // Reload to update status
    } catch (error) {
      setError('Failed to dispatch finding')
    }
  }

  const getPriorityColor = (timeframe: string) => {
    switch (timeframe) {
      case 'sofort': return 'bg-red-100 text-red-800'
      case 'kurzfristig': return 'bg-yellow-100 text-yellow-800'
      case 'mittel': return 'bg-blue-100 text-blue-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getEffortColor = (effort: string) => {
    switch (effort) {
      case 'low': return 'bg-green-100 text-green-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'high': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Cashbot - Cashflow Radar</h1>
          <p className="text-gray-600">KI-gestützte Cashflow-Optimierung für die Tierheilpraxis</p>
        </div>

        {/* Scan Controls */}
        <div className="bg-white p-6 rounded-lg shadow mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Cashflow-Scan</h2>
              <p className="text-gray-600">Startet KI-Analyse für neue Cashflow-Chancen</p>
            </div>
            <Button
              onClick={handleScan}
              disabled={scanning || loading.cashbot}
              className="bg-green-600 hover:bg-green-700"
            >
              <Play className="h-4 w-4 mr-2" />
              {scanning ? 'Scan läuft...' : 'Scan starten'}
            </Button>
          </div>
        </div>

        {/* Findings */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">Findings</h2>
              <Button onClick={loadFindings} disabled={loading.cashbot}>
                Aktualisieren
              </Button>
            </div>
          </div>

          <div className="p-6">
            {cashbotFindings.length > 0 ? (
              <div className="space-y-4">
                {cashbotFindings.map((finding) => (
                  <div key={finding.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <h3 className="font-semibold text-gray-900">{finding.title}</h3>
                          <span className={`px-2 py-1 rounded-full text-xs ${getPriorityColor(finding.timeframe)}`}>
                            {finding.timeframe}
                          </span>
                          <span className={`px-2 py-1 rounded-full text-xs ${getEffortColor(finding.effort)}`}>
                            {finding.effort}
                          </span>
                        </div>
                        
                        <p className="text-gray-600 mb-3">{finding.idea}</p>
                        
                        {finding.steps && finding.steps.length > 0 && (
                          <div className="mb-3">
                            <h4 className="text-sm font-medium text-gray-700 mb-1">Schritte:</h4>
                            <ul className="text-sm text-gray-600 list-disc list-inside">
                              {finding.steps.map((step: string, index: number) => (
                                <li key={index}>{step}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                          <div className="flex items-center">
                            <Euro className="h-4 w-4 mr-1" />
                            <span className="font-semibold text-green-600">
                              {finding.potential_eur.toFixed(0)} €
                            </span>
                          </div>
                          <div className="flex items-center">
                            <Clock className="h-4 w-4 mr-1" />
                            <span>{finding.duration_s.toFixed(1)}s</span>
                          </div>
                          <div className="flex items-center">
                            <TrendingUp className="h-4 w-4 mr-1" />
                            <span>{finding.provider}</span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="ml-4 flex flex-col space-y-2">
                        <Button
                          onClick={() => handleDispatch(finding.id)}
                          disabled={finding.status === 'in_progress'}
                          size="sm"
                          className="bg-blue-600 hover:bg-blue-700"
                        >
                          <Send className="h-4 w-4 mr-1" />
                          {finding.status === 'in_progress' ? 'Gesendet' : 'An n8n senden'}
                        </Button>
                        
                        {finding.status === 'in_progress' && (
                          <div className="flex items-center text-xs text-blue-600">
                            <AlertCircle className="h-3 w-3 mr-1" />
                            In Bearbeitung
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-gray-500 py-12">
                <TrendingUp className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p className="text-lg font-medium">Keine Findings gefunden</p>
                <p className="text-sm">Starten Sie einen Scan, um Cashflow-Chancen zu entdecken</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
