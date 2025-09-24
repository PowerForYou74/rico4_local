const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

export interface HealthStatus {
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

export interface PracticeStats {
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

export interface FinanceKPIs {
  mrr: number
  arr: number
  cash_on_hand: number
  burn_rate: number
  runway_days: number
}

export interface CashbotFinding {
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

export interface Prompt {
  id: number
  name: string
  role: string
  tags: string
  created_at: string
}

export interface Run {
  id: number
  provider: string
  model: string
  input_tokens: number
  output_tokens: number
  duration_s: number
  status: string
  created_at: string
}

// API Functions
export async function getHealthStatus(): Promise<HealthStatus> {
  const response = await fetch(`${API_BASE}/check-keys`)
  if (!response.ok) throw new Error('Failed to fetch health status')
  return response.json()
}

export async function getPracticeStats(): Promise<PracticeStats> {
  const response = await fetch(`${API_BASE}/v2/practice/stats`)
  if (!response.ok) throw new Error('Failed to fetch practice stats')
  return response.json()
}

export async function getFinanceKPIs(): Promise<FinanceKPIs> {
  const response = await fetch(`${API_BASE}/v2/finance/kpis`)
  if (!response.ok) throw new Error('Failed to fetch finance KPIs')
  return response.json()
}

export async function getCashbotFindings(): Promise<CashbotFinding[]> {
  const response = await fetch(`${API_BASE}/v2/cashbot/findings`)
  if (!response.ok) throw new Error('Failed to fetch cashbot findings')
  return response.json()
}

export async function triggerCashbotScan(): Promise<{status: string, finding_id?: number, title?: string, potential_eur?: number}> {
  const response = await fetch(`${API_BASE}/v2/cashbot/scan`, {
    method: 'POST'
  })
  if (!response.ok) throw new Error('Failed to trigger cashbot scan')
  return response.json()
}

export async function dispatchCashbotFinding(findingId: number): Promise<{status: string, finding_id: number, dispatched_at: string}> {
  const response = await fetch(`${API_BASE}/v2/cashbot/dispatch/${findingId}`, {
    method: 'POST'
  })
  if (!response.ok) throw new Error('Failed to dispatch finding')
  return response.json()
}

export async function getPrompts(): Promise<Prompt[]> {
  const response = await fetch(`${API_BASE}/v2/core/prompts`)
  if (!response.ok) throw new Error('Failed to fetch prompts')
  return response.json()
}

export async function getRuns(): Promise<Run[]> {
  const response = await fetch(`${API_BASE}/v2/core/runs`)
  if (!response.ok) throw new Error('Failed to fetch runs')
  return response.json()
}

export async function runAgent(prompt: string, userInput: string, kbContext?: string): Promise<{response: string, meta: any}> {
  const response = await fetch(`${API_BASE}/api/v1/rico-agent`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_input: userInput,
      system_prompt: prompt,
      kb_context: kbContext,
      mode: 'auto'
    })
  })
  if (!response.ok) throw new Error('Failed to run agent')
  return response.json()
}
