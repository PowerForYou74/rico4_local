'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useAppStore } from '@/store/app-store'
import { api } from '@/lib/api'
import { 
  Brain, 
  Zap, 
  Search, 
  Send, 
  Clock, 
  CheckCircle, 
  XCircle,
  Loader2
} from 'lucide-react'

export default function AgentsPage() {
  const { systemHealth } = useAppStore()
  const [activeTab, setActiveTab] = useState('ask')
  const [prompt, setPrompt] = useState('')
  const [task, setTask] = useState('analysis')
  const [preferred, setPreferred] = useState('auto')
  const [online, setOnline] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [runs, setRuns] = useState<any[]>([])
  const [aiHealth, setAiHealth] = useState<any>(null)

  const tasks = [
    { value: 'research', label: 'Research', description: 'Online research with Perplexity' },
    { value: 'analysis', label: 'Analysis', description: 'Data analysis with OpenAI' },
    { value: 'write', label: 'Write', description: 'Creative writing with Claude' },
    { value: 'review', label: 'Review', description: 'Content review with Claude' }
  ]

  const providers = [
    { value: 'auto', label: 'Auto-Route (Recommended)', description: 'Smart routing based on task' },
    { value: 'openai', label: 'OpenAI GPT', description: 'GPT-4o for analysis' },
    { value: 'anthropic', label: 'Anthropic Claude', description: 'Claude-3-7-Sonnet for writing' },
    { value: 'perplexity', label: 'Perplexity Sonar', description: 'Real-time web search' }
  ]

  const handleAskSubmit = async () => {
    if (!prompt.trim()) return

    setIsLoading(true)
    setResult(null)

    try {
      const response = await api.askAI({
        task: task,
        prompt: prompt.trim(),
        preferred: preferred,
        online: online
      })

      setResult(response)
      // Add to runs list
      setRuns(prev => [response, ...prev.slice(0, 9)]) // Keep last 10 runs
    } catch (error) {
      console.error('Failed to ask AI:', error)
      setResult({ error: 'Failed to ask AI' })
    } finally {
      setIsLoading(false)
    }
  }

  const loadAIHealth = async () => {
    try {
      const health = await api.getAIHealth()
      setAiHealth(health)
    } catch (error) {
      console.error('Failed to load AI health:', error)
    }
  }

  const loadRuns = async () => {
    try {
      const runsData = await api.getRuns()
      setRuns(runsData)
    } catch (error) {
      console.error('Failed to load runs:', error)
    }
  }

  const getProviderStatus = (provider: string) => {
    if (!systemHealth?.providers) return 'unknown'
    
    const providerData = systemHealth.providers.find(p => p.provider === provider)
    return providerData?.status || 'unknown'
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'health-healthy'
      case 'unhealthy': return 'health-unhealthy'
      default: return 'health-unknown'
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center space-x-4">
            <div className="rico-gradient p-2 rounded-lg">
              <Brain className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-foreground">Agent Workflows</h1>
              <p className="text-sm text-muted-foreground">AI Provider Orchestration & Knowledge Base</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="ask">Ask AI</TabsTrigger>
            <TabsTrigger value="runs">Runs</TabsTrigger>
            <TabsTrigger value="health">Health</TabsTrigger>
          </TabsList>

          {/* Ask AI Tab */}
          <TabsContent value="ask" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Input Panel */}
              <Card>
                <CardHeader>
                  <CardTitle>Ask AI</CardTitle>
                  <CardDescription>
                    Multi-AI orchestration with smart routing and auto-race
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="task">Task Type</Label>
                    <Select value={task} onValueChange={setTask}>
                      <SelectTrigger className="rico-input">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {tasks.map((taskItem) => (
                          <SelectItem key={taskItem.value} value={taskItem.value}>
                            <div>
                              <div className="font-medium">{taskItem.label}</div>
                              <div className="text-xs text-muted-foreground">{taskItem.description}</div>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="prompt">Prompt</Label>
                    <Textarea
                      id="prompt"
                      placeholder="Enter your prompt here..."
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                      rows={4}
                      className="rico-input"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="preferred">Preferred Provider</Label>
                    <Select value={preferred} onValueChange={setPreferred}>
                      <SelectTrigger className="rico-input">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {providers.map((provider) => (
                          <SelectItem key={provider.value} value={provider.value}>
                            <div className="flex items-center space-x-2">
                              <span>{provider.label}</span>
                              <Badge 
                                variant="outline" 
                                className={`health-indicator ${getStatusColor(getProviderStatus(provider.value))}`}
                              >
                                {getProviderStatus(provider.value)}
                              </Badge>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground">
                      {providers.find(p => p.value === preferred)?.description}
                    </p>
                  </div>

                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="online"
                      checked={online}
                      onChange={(e) => setOnline(e.target.checked)}
                      className="rounded"
                    />
                    <Label htmlFor="online">Online Mode (Research)</Label>
                  </div>

                  <Button 
                    onClick={handleAskSubmit}
                    disabled={isLoading || !prompt.trim()}
                    className="w-full rico-button-primary"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Asking AI...
                      </>
                    ) : (
                      <>
                        <Send className="h-4 w-4 mr-2" />
                        Ask AI
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>

              {/* Result Panel */}
              <Card>
                <CardHeader>
                  <CardTitle>AI Response</CardTitle>
                  <CardDescription>
                    Response from {result?.provider || 'selected provider'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {isLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                    </div>
                  ) : result ? (
                    <div className="space-y-4">
                      {result.error ? (
                        <div className="flex items-center space-x-2 text-destructive">
                          <XCircle className="h-4 w-4" />
                          <span>{result.error}</span>
                        </div>
                      ) : (
                        <>
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              <Badge variant="outline" className="health-indicator health-healthy">
                                {result.provider}
                              </Badge>
                              <Badge variant="secondary" className="text-xs">
                                {result.routing_reason}
                              </Badge>
                            </div>
                            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                              <Clock className="h-4 w-4" />
                              <span>{(result.duration_s * 1000).toFixed(0)}ms</span>
                            </div>
                          </div>
                          <div className="prose prose-sm max-w-none">
                            <p className="whitespace-pre-wrap">{result.content}</p>
                          </div>
                          <div className="grid grid-cols-2 gap-4 text-xs text-muted-foreground">
                            <div>Model: {result.provider_model}</div>
                            <div>Tokens: {result.tokens_in + result.tokens_out}</div>
                            <div>In: {result.tokens_in}</div>
                            <div>Out: {result.tokens_out}</div>
                          </div>
                        </>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      <Brain className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>Enter a prompt to ask AI</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Runs Tab */}
          <TabsContent value="runs" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Recent AI Runs</CardTitle>
                <CardDescription>
                  Last 10 AI requests with provider and performance metrics
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {runs.length > 0 ? (
                    runs.map((run, index) => (
                      <div key={run.id || index} className="border border-border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            <Badge variant="outline" className="health-indicator health-healthy">
                              {run.provider}
                            </Badge>
                            <Badge variant="secondary" className="text-xs">
                              {run.task}
                            </Badge>
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {new Date(run.timestamp).toLocaleString()}
                          </div>
                        </div>
                        <p className="text-sm text-muted-foreground mb-2">{run.content.substring(0, 100)}...</p>
                        <div className="grid grid-cols-4 gap-4 text-xs text-muted-foreground">
                          <div>Model: {run.provider_model}</div>
                          <div>Duration: {(run.duration_s * 1000).toFixed(0)}ms</div>
                          <div>Tokens: {run.tokens_in + run.tokens_out}</div>
                          <div>Reason: {run.routing_reason}</div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      <Zap className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>No AI runs yet</p>
                      <p className="text-sm">Make your first AI request in the Ask tab</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Health Tab */}
          <TabsContent value="health" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>AI Provider Health</CardTitle>
                <CardDescription>
                  Status of all AI providers and routing rules
                </CardDescription>
              </CardHeader>
              <CardContent>
                {aiHealth ? (
                  <div className="space-y-6">
                    {/* Provider Status */}
                    <div>
                      <h4 className="font-medium mb-3">Provider Status</h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {Object.entries(aiHealth.providers).map(([provider, status]: [string, any]) => (
                          <div key={provider} className="border border-border rounded-lg p-4">
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-medium capitalize">{provider}</span>
                              <Badge 
                                variant="outline" 
                                className={`health-indicator ${
                                  status.status === 'healthy' ? 'health-healthy' : 'health-unhealthy'
                                }`}
                              >
                                {status.status}
                              </Badge>
                            </div>
                            <div className="text-xs text-muted-foreground">
                              <div>Latency: {status.latency_ms?.toFixed(0) || 'N/A'}ms</div>
                              <div>Model: {status.model || 'N/A'}</div>
                              {status.error && <div className="text-red-500">Error: {status.error}</div>}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Routing Rules */}
                    <div>
                      <h4 className="font-medium mb-3">Routing Rules</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {Object.entries(aiHealth.routing_rules).map(([rule, provider]) => (
                          <div key={rule} className="border border-border rounded-lg p-3">
                            <div className="font-medium text-sm">{rule}</div>
                            <div className="text-xs text-muted-foreground">{String(provider)}</div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Auto-Race Status */}
                    <div className="flex items-center space-x-2">
                      <span className="font-medium">Auto-Race:</span>
                      <Badge variant={aiHealth.auto_race_enabled ? "default" : "secondary"}>
                        {aiHealth.auto_race_enabled ? "Enabled" : "Disabled"}
                      </Badge>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <CheckCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Loading AI health status...</p>
                    <Button onClick={loadAIHealth} variant="outline" className="mt-4">
                      Load Health Status
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
