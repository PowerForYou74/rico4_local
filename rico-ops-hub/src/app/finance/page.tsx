'use client'

import { useState, useEffect } from 'react'
import { useAppStore } from '@/lib/store'
import { getFinanceKPIs } from '@/lib/api'
import { MetricCard } from '@/components/MetricCard'
import { Button } from '@/components/Button'
import { Euro, TrendingUp, AlertCircle, Calendar } from 'lucide-react'

export default function FinancePage() {
  const { financeKPIs, setFinanceKPIs, setLoading, loading, setError } = useAppStore()
  const [forecast, setForecast] = useState<any>(null)

  useEffect(() => {
    loadFinanceData()
  }, [])

  const loadFinanceData = async () => {
    try {
      setLoading('finance', true)
      const kpis = await getFinanceKPIs()
      setFinanceKPIs(kpis)
      
      // Mock forecast data
      setForecast({
        monthly: [
          { month: '2024-01', revenue: 5000, costs: 3000, profit: 2000 },
          { month: '2024-02', revenue: 5250, costs: 3090, profit: 2160 },
          { month: '2024-03', revenue: 5513, costs: 3183, profit: 2330 },
          { month: '2024-04', revenue: 5788, costs: 3278, profit: 2510 },
          { month: '2024-05', revenue: 6078, costs: 3376, profit: 2702 },
          { month: '2024-06', revenue: 6382, costs: 3477, profit: 2905 },
        ]
      })
    } catch (error) {
      setError('Failed to load finance data')
    } finally {
      setLoading('finance', false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Finanz-KPIs</h1>
          <p className="text-gray-600">Übersicht über Finanzkennzahlen und Forecast</p>
        </div>

        {/* KPIs */}
        {financeKPIs && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <MetricCard
              title="MRR"
              value={`${financeKPIs.mrr.toFixed(0)} €`}
              subtitle="Monatlich wiederkehrend"
              icon={<TrendingUp className="h-5 w-5" />}
              status="success"
            />
            <MetricCard
              title="ARR"
              value={`${financeKPIs.arr.toFixed(0)} €`}
              subtitle="Jährlich wiederkehrend"
              icon={<TrendingUp className="h-5 w-5" />}
              status="success"
            />
            <MetricCard
              title="Cash on Hand"
              value={`${financeKPIs.cash_on_hand.toFixed(0)} €`}
              subtitle="Verfügbares Kapital"
              icon={<Euro className="h-5 w-5" />}
              status="info"
            />
            <MetricCard
              title="Runway"
              value={`${financeKPIs.runway_days} Tage`}
              subtitle="Verbleibende Zeit"
              icon={<AlertCircle className="h-5 w-5" />}
              status={financeKPIs.runway_days > 90 ? 'success' : financeKPIs.runway_days > 30 ? 'warning' : 'error'}
            />
          </div>
        )}

        {/* Burn Rate */}
        {financeKPIs && (
          <div className="bg-white p-6 rounded-lg shadow mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Burn Rate</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Monatliche Ausgaben</h3>
                <p className="text-3xl font-bold text-red-600">
                  {financeKPIs.burn_rate.toFixed(0)} €
                </p>
                <p className="text-sm text-gray-600">Pro Monat</p>
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Tägliche Ausgaben</h3>
                <p className="text-3xl font-bold text-red-600">
                  {(financeKPIs.burn_rate / 30).toFixed(0)} €
                </p>
                <p className="text-sm text-gray-600">Pro Tag</p>
              </div>
            </div>
          </div>
        )}

        {/* Forecast Chart */}
        {forecast && (
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">12-Monats Forecast</h2>
              <Button onClick={loadFinanceData} disabled={loading.finance}>
                Aktualisieren
              </Button>
            </div>
            
            <div className="space-y-4">
              {forecast.monthly.map((month: any, index: number) => (
                <div key={month.month} className="flex items-center space-x-4">
                  <div className="w-20 text-sm font-medium text-gray-600">
                    {month.month}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-4">
                      <div className="flex-1">
                        <div className="flex justify-between text-sm mb-1">
                          <span>Umsatz</span>
                          <span className="font-medium">{month.revenue.toFixed(0)} €</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-green-500 h-2 rounded-full" 
                            style={{ width: `${(month.revenue / 7000) * 100}%` }}
                          />
                        </div>
                      </div>
                      <div className="flex-1">
                        <div className="flex justify-between text-sm mb-1">
                          <span>Kosten</span>
                          <span className="font-medium">{month.costs.toFixed(0)} €</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-red-500 h-2 rounded-full" 
                            style={{ width: `${(month.costs / 4000) * 100}%` }}
                          />
                        </div>
                      </div>
                      <div className="flex-1">
                        <div className="flex justify-between text-sm mb-1">
                          <span>Gewinn</span>
                          <span className={`font-medium ${month.profit > 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {month.profit.toFixed(0)} €
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full ${month.profit > 0 ? 'bg-green-500' : 'bg-red-500'}`}
                            style={{ width: `${Math.abs(month.profit / 3000) * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
