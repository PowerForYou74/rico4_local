// Token-Preise pro 1k Tokens (EUR)
export const TOKEN_PRICES = {
  openai: {
    'gpt-4o': 0.005,
    'gpt-4o-mini': 0.00015,
    'gpt-4': 0.03,
    'gpt-3.5-turbo': 0.0015,
  },
  claude: {
    'claude-3-5-sonnet-20241022': 0.003,
    'claude-3-5-haiku-20241022': 0.0008,
    'claude-3-opus-20240229': 0.015,
    'claude-3-sonnet-20240229': 0.003,
    'claude-3-haiku-20240307': 0.0008,
  },
  perplexity: {
    'sonar': 0.001,
    'sonar-pro': 0.005,
  }
}

export function calculateCost(provider: string, model: string, inputTokens: number, outputTokens: number): number {
  const prices = TOKEN_PRICES[provider as keyof typeof TOKEN_PRICES]
  if (!prices) return 0
  
  const modelPrice = prices[model as keyof typeof prices]
  if (!modelPrice) return 0
  
  const inputCost = (inputTokens / 1000) * modelPrice
  const outputCost = (outputTokens / 1000) * modelPrice * 2 // Output ist meist teurer
  
  return inputCost + outputCost
}

export function formatCost(cost: number): string {
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 4,
    maximumFractionDigits: 4,
  }).format(cost)
}
