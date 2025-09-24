'use client'

import { useState, useEffect } from 'react'
import { useAppStore } from '@/lib/store'
import { getPrompts, runAgent } from '@/lib/api'
import { Button } from '@/components/Button'
import { StatusDot } from '@/components/StatusDot'
import { Brain, Play, Clock, DollarSign } from 'lucide-react'

export default function AgentsPage() {
  const { healthStatus, lastRun, setLastRun, setLoading, loading, setError } = useAppStore()
  const [prompts, setPrompts] = useState<any[]>([])
  const [selectedPrompt, setSelectedPrompt] = useState('')
  const [userInput, setUserInput] = useState('')
  const [kbContext, setKbContext] = useState('')
  const [response, setResponse] = useState('')

  useEffect(() => {
    loadPrompts()
  }, [])

  const loadPrompts = async () => {
    try {
      const data = await getPrompts()
      setPrompts(data)
    } catch (error) {
      setError('Failed to load prompts')
    }
  }

  const handleRunAgent = async () => {
    if (!selectedPrompt || !userInput) return

    try {
      setLoading('agent', true)
      setResponse('')
      
      const result = await runAgent(selectedPrompt, userInput, kbContext || undefined)
      setResponse(result.response)
      setLastRun(result.meta)
    } catch (error) {
      setError('Failed to run agent')
    } finally {
      setLoading('agent', false)
    }
  }

  const getProviderStatus = (provider: string) => {
    if (!healthStatus) return 'unknown'
    return healthStatus[provider] || 'unknown'
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Multi-Provider Konsole</h1>
          <p className="text-gray-600">KI-Agents mit verschiedenen Providern ausführen</p>
        </div>

        {/* Provider Status */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Provider Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {['openai', 'claude', 'perplexity'].map((provider) => (
              <div key={provider} className="bg-white p-4 rounded-lg shadow border">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900 capitalize">{provider}</h3>
                    <p className="text-sm text-gray-600">
                      {healthStatus?.models?.[provider] || 'N/A'}
                    </p>
                  </div>
                  <StatusDot status={getProviderStatus(provider)} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Agent Console */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Input */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Agent Konfiguration</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  System Prompt
                </label>
                <select
                  value={selectedPrompt}
                  onChange={(e) => setSelectedPrompt(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Prompt auswählen...</option>
                  {prompts.map((prompt) => (
                    <option key={prompt.id} value={prompt.name}>
                      {prompt.name} ({prompt.role})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  User Input
                </label>
                <textarea
                  value={userInput}
                  onChange={(e) => setUserInput(e.target.value)}
                  rows={4}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Ihre Anfrage an den Agent..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  KB Kontext (optional)
                </label>
                <textarea
                  value={kbContext}
                  onChange={(e) => setKbContext(e.target.value)}
                  rows={2}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Zusätzlicher Kontext aus der Knowledge Base..."
                />
              </div>

              <Button
                onClick={handleRunAgent}
                disabled={!selectedPrompt || !userInput || loading.agent}
                className="w-full"
              >
                <Play className="h-4 w-4 mr-2" />
                Agent ausführen
              </Button>
            </div>
          </div>

          {/* Output */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Antwort</h2>
            
            {response ? (
              <div className="space-y-4">
                <div className="p-4 bg-gray-50 rounded-md">
                  <pre className="whitespace-pre-wrap text-sm">{response}</pre>
                </div>
                
                {lastRun && (
                  <div className="border-t pt-4">
                    <h3 className="font-semibold text-gray-900 mb-2">Run Details</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="flex items-center">
                        <Brain className="h-4 w-4 mr-2 text-gray-400" />
                        <span>{lastRun.used_provider}</span>
                      </div>
                      <div className="flex items-center">
                        <Clock className="h-4 w-4 mr-2 text-gray-400" />
                        <span>{lastRun.duration_s?.toFixed(2)}s</span>
                      </div>
                      <div className="flex items-center">
                        <DollarSign className="h-4 w-4 mr-2 text-gray-400" />
                        <span>~{lastRun.cost_eur?.toFixed(4)} €</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                <Brain className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>Führen Sie einen Agent aus, um die Antwort hier zu sehen</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
