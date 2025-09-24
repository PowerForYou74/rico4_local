import { create } from 'zustand'

interface AppState {
  // Health Status
  healthStatus: any | null
  setHealthStatus: (status: any) => void
  
  // Practice Stats
  practiceStats: any | null
  setPracticeStats: (stats: any) => void
  
  // Finance KPIs
  financeKPIs: any | null
  setFinanceKPIs: (kpis: any) => void
  
  // Cashbot Findings
  cashbotFindings: any[]
  setCashbotFindings: (findings: any[]) => void
  
  // Last Run
  lastRun: any | null
  setLastRun: (run: any) => void
  
  // Loading States
  loading: {
    health: boolean
    practice: boolean
    finance: boolean
    cashbot: boolean
    agent: boolean
  }
  setLoading: (key: keyof AppState['loading'], value: boolean) => void
  
  // Error States
  error: string | null
  setError: (error: string | null) => void
}

export const useAppStore = create<AppState>((set) => ({
  healthStatus: null,
  setHealthStatus: (status) => set({ healthStatus: status }),
  
  practiceStats: null,
  setPracticeStats: (stats) => set({ practiceStats: stats }),
  
  financeKPIs: null,
  setFinanceKPIs: (kpis) => set({ financeKPIs: kpis }),
  
  cashbotFindings: [],
  setCashbotFindings: (findings) => set({ cashbotFindings: findings }),
  
  lastRun: null,
  setLastRun: (run) => set({ lastRun: run }),
  
  loading: {
    health: false,
    practice: false,
    finance: false,
    cashbot: false,
    agent: false,
  },
  setLoading: (key, value) => set((state) => ({
    loading: { ...state.loading, [key]: value }
  })),
  
  error: null,
  setError: (error) => set({ error }),
}))
