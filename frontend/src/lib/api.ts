import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    console.error('API Response Error:', error)
    
    // Handle different error types
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.detail || error.response.data?.message || 'Server error'
      throw new Error(`${error.response.status}: ${message}`)
    } else if (error.request) {
      // Request was made but no response received
      throw new Error('Network error: No response from server')
    } else {
      // Something else happened
      throw new Error(`Request error: ${error.message}`)
    }
  }
)

// API Types
export interface SystemHealth {
  status: string
  latency_ms: number
  model: string
  env_source: string
  providers: Array<{
    provider: string
    model: string
    status: string
    latency_ms: number
    error?: string
  }>
  timestamp: string
}

export interface PromptRequest {
  prompt: string
  provider?: string
  max_tokens?: number
  temperature?: number
}

export interface PromptResponse {
  id: string
  content: string
  provider: string
  model: string
  usage: Record<string, any>
  latency_ms: number
  timestamp: string
}

export interface AIAskRequest {
  task: string
  prompt: string
  preferred: string
  online: boolean
}

export interface AIAskResponse {
  id: string
  content: string
  tokens_in: number
  tokens_out: number
  provider: string
  provider_model: string
  duration_s: number
  finish_reason?: string
  task: string
  routing_reason: string
  timestamp: string
}

export interface AIHealthResponse {
  providers: Record<string, any>
  routing_rules: Record<string, string>
  auto_race_enabled: boolean
}

export interface RunRequest {
  name: string
  description?: string
  prompts: string[]
  auto_race?: boolean
}

export interface RunResponse {
  id: string
  name: string
  description?: string
  status: string
  results: PromptResponse[]
  created_at: string
}

export interface KBEntry {
  id: string
  title: string
  content: string
  tags: string[]
  created_at: string
}

export interface ScanRequest {
  target: string
  scan_type: string
  priority: string
}

export interface ScanResult {
  id: string
  target: string
  scan_type: string
  priority: string
  status: string
  findings: Array<{
    id: string
    scan_id: string
    type: string
    severity: string
    title: string
    description: string
    recommendation: string
    confidence: number
    metadata: Record<string, any>
    created_at: string
  }>
  summary: string
  created_at: string
  completed_at?: string
}

export interface KPI {
  id: string
  name: string
  value: number
  unit: string
  trend: string
  change_percent: number
  target?: number
  period: string
  created_at: string
}

export interface Forecast {
  id: string
  metric: string
  current_value: number
  forecast_values: number[]
  forecast_dates: string[]
  confidence: number
  methodology: string
  created_at: string
}

// API Functions
export const api = {
  // Health endpoints
  async getSystemHealth(): Promise<SystemHealth> {
    const response = await apiClient.get('/health/')
    return response.data
  },

  async getQuickHealth(): Promise<{ status: string; env_source: string; timestamp: string }> {
    const response = await apiClient.get('/health/quick')
    return response.data
  },

  async getProvidersHealth(): Promise<Record<string, any>> {
    const response = await apiClient.get('/health/providers')
    return response.data
  },

  // Core v2 endpoints
  async createPrompt(request: PromptRequest): Promise<PromptResponse> {
    const response = await apiClient.post('/v2/core/prompts', request)
    return response.data
  },

  async getPrompt(promptId: string): Promise<PromptResponse> {
    const response = await apiClient.get(`/v2/core/prompts/${promptId}`)
    return response.data
  },

  async listPrompts(limit = 50, offset = 0): Promise<PromptResponse[]> {
    const response = await apiClient.get(`/v2/core/prompts?limit=${limit}&offset=${offset}`)
    return response.data
  },

  async createRun(request: RunRequest): Promise<RunResponse> {
    const response = await apiClient.post('/v2/core/runs', request)
    return response.data
  },

  async getRun(runId: string): Promise<RunResponse> {
    const response = await apiClient.get(`/v2/core/runs/${runId}`)
    return response.data
  },

  async listRuns(limit = 50, offset = 0): Promise<RunResponse[]> {
    const response = await apiClient.get(`/v2/core/runs?limit=${limit}&offset=${offset}`)
    return response.data
  },

  async createKBEntry(title: string, content: string, tags: string[] = []): Promise<KBEntry> {
    const response = await apiClient.post('/v2/core/kb', {
      title,
      content,
      tags
    })
    return response.data
  },

  async getKBEntry(entryId: string): Promise<KBEntry> {
    const response = await apiClient.get(`/v2/core/kb/${entryId}`)
    return response.data
  },

  async searchKB(query?: string, tags?: string): Promise<KBEntry[]> {
    const params = new URLSearchParams()
    if (query) params.append('q', query)
    if (tags) params.append('tags', tags)
    
    const response = await apiClient.get(`/v2/core/kb?${params.toString()}`)
    return response.data
  },

  async getEvents(limit = 100, eventType?: string): Promise<Array<{
    id: string
    type: string
    message: string
    data: Record<string, any>
    timestamp: string
  }>> {
    const params = new URLSearchParams()
    params.append('limit', limit.toString())
    if (eventType) params.append('event_type', eventType)
    
    const response = await apiClient.get(`/v2/core/events?${params.toString()}`)
    return response.data
  },

  // Cashbot endpoints
  async createScan(request: ScanRequest): Promise<ScanResult> {
    const response = await apiClient.post('/v2/cashbot/scan', request)
    return response.data
  },

  async getScan(scanId: string): Promise<ScanResult> {
    const response = await apiClient.get(`/v2/cashbot/scans/${scanId}`)
    return response.data
  },

  async listScans(limit = 50, status?: string): Promise<ScanResult[]> {
    const params = new URLSearchParams()
    params.append('limit', limit.toString())
    if (status) params.append('status', status)
    
    const response = await apiClient.get(`/v2/cashbot/scans?${params.toString()}`)
    return response.data
  },

  async getFinding(findingId: string): Promise<any> {
    const response = await apiClient.get(`/v2/cashbot/findings/${findingId}`)
    return response.data
  },

  async listFindings(scanId?: string, severity?: string): Promise<any[]> {
    const params = new URLSearchParams()
    if (scanId) params.append('scan_id', scanId)
    if (severity) params.append('severity', severity)
    
    const response = await apiClient.get(`/v2/cashbot/findings?${params.toString()}`)
    return response.data
  },

  async createDispatch(scanId: string, action: string, recipients: string[] = [], message?: string): Promise<any> {
    const response = await apiClient.post('/v2/cashbot/dispatch', {
      scan_id: scanId,
      action,
      recipients,
      message
    })
    return response.data
  },

  async getDispatch(dispatchId: string): Promise<any> {
    const response = await apiClient.get(`/v2/cashbot/dispatches/${dispatchId}`)
    return response.data
  },

  async listDispatches(scanId?: string, status?: string): Promise<any[]> {
    const params = new URLSearchParams()
    if (scanId) params.append('scan_id', scanId)
    if (status) params.append('status', status)
    
    const response = await apiClient.get(`/v2/cashbot/dispatches?${params.toString()}`)
    return response.data
  },

  // Finance endpoints
  async getKPIs(period?: string): Promise<KPI[]> {
    const params = new URLSearchParams()
    if (period) params.append('period', period)
    
    const response = await apiClient.get(`/v2/finance/kpis?${params.toString()}`)
    return response.data
  },

  async getForecasts(metric?: string): Promise<Forecast[]> {
    const params = new URLSearchParams()
    if (metric) params.append('metric', metric)
    
    const response = await apiClient.get(`/v2/finance/forecasts?${params.toString()}`)
    return response.data
  },

  async getDashboard(): Promise<{
    key_metrics: Record<string, any>
    forecasts: Record<string, any>
    summary: Record<string, any>
  }> {
    const response = await apiClient.get('/v2/finance/dashboard')
    return response.data
  },

  // Practice endpoints
  async getPracticeDashboard(): Promise<{
    summary: Record<string, any>
    appointment_statuses: Record<string, number>
    invoice_statuses: Record<string, number>
    upcoming_appointments: number
    last_updated: string
  }> {
    const response = await apiClient.get('/v2/practice/dashboard')
    return response.data
  },

  // AI v2 endpoints
  async askAI(request: AIAskRequest): Promise<AIAskResponse> {
    const response = await apiClient.post('/v2/ai/ask', request)
    return response.data
  },

  async getAIHealth(): Promise<AIHealthResponse> {
    const response = await apiClient.get('/v2/ai/health')
    return response.data
  },

  async getRoutingRules(): Promise<Record<string, any>> {
    const response = await apiClient.get('/v2/ai/routing-rules')
    return response.data
  },

  async getRuns(): Promise<AIAskResponse[]> {
    // For now, return empty array - runs are stored in component state
    // In a real app, this would fetch from a persistent store
    return []
  },

  // Legacy v1 endpoints
  async ricoAgent(message: string, context?: Record<string, any>): Promise<{
    response: string
    timestamp: string
    status: string
  }> {
    const response = await apiClient.post('/v1/rico-agent', {
      message,
      context
    })
    return response.data
  }
}

export default api
