import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import { SystemHealth } from '@/lib/api'

interface AppState {
  // System state
  systemHealth: SystemHealth | null
  isLoading: boolean
  error: string | null
  
  // UI state
  sidebarOpen: boolean
  theme: 'light' | 'dark' | 'system'
  
  // Actions
  setSystemHealth: (health: SystemHealth | null) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  setSidebarOpen: (open: boolean) => void
  setTheme: (theme: 'light' | 'dark' | 'system') => void
  toggleSidebar: () => void
  
  // Async actions
  loadSystemHealth: () => Promise<void>
  refreshSystemHealth: () => Promise<void>
}

export const useAppStore = create<AppState>()(
  devtools(
    (set, get) => ({
      // Initial state
      systemHealth: null,
      isLoading: false,
      error: null,
      sidebarOpen: false,
      theme: 'system',

      // Actions
      setSystemHealth: (health) => set({ systemHealth: health }),
      setLoading: (loading) => set({ isLoading: loading }),
      setError: (error) => set({ error }),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setTheme: (theme) => set({ theme }),
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

      // Async actions
      loadSystemHealth: async () => {
        set({ isLoading: true, error: null })
        try {
          const { api } = await import('@/lib/api')
          const health = await api.getSystemHealth()
          set({ systemHealth: health, isLoading: false })
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to load system health'
          set({ error: errorMessage, isLoading: false })
        }
      },

      refreshSystemHealth: async () => {
        set({ isLoading: true, error: null })
        try {
          const { api } = await import('@/lib/api')
          const health = await api.getSystemHealth()
          set({ systemHealth: health, isLoading: false })
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to refresh system health'
          set({ error: errorMessage, isLoading: false })
        }
      },
    }),
    {
      name: 'rico-app-store',
    }
  )
)

// Selectors for better performance
export const selectSystemHealth = (state: AppState) => state.systemHealth
export const selectIsLoading = (state: AppState) => state.isLoading
export const selectError = (state: AppState) => state.error
export const selectSidebarOpen = (state: AppState) => state.sidebarOpen
export const selectTheme = (state: AppState) => state.theme

// Computed selectors
export const selectHealthyProviders = (state: AppState) => {
  if (!state.systemHealth?.providers) return []
  return state.systemHealth.providers.filter(p => p.status === 'healthy')
}

export const selectUnhealthyProviders = (state: AppState) => {
  if (!state.systemHealth?.providers) return []
  return state.systemHealth.providers.filter(p => p.status === 'unhealthy')
}

export const selectOverallStatus = (state: AppState) => {
  return state.systemHealth?.status || 'unknown'
}

export const selectSystemLatency = (state: AppState) => {
  return state.systemHealth?.latency_ms || 0
}

export const selectProviderCount = (state: AppState) => {
  return state.systemHealth?.providers.length || 0
}

export const selectHealthyProviderCount = (state: AppState) => {
  if (!state.systemHealth?.providers) return 0
  return state.systemHealth.providers.filter(p => p.status === 'healthy').length
}

// Theme utilities
export const getThemeClass = (theme: 'light' | 'dark' | 'system') => {
  switch (theme) {
    case 'light':
      return 'light'
    case 'dark':
      return 'dark'
    case 'system':
    default:
      return ''
  }
}

// Health status utilities
export const getHealthStatusColor = (status: string) => {
  switch (status) {
    case 'healthy':
      return 'text-green-500'
    case 'unhealthy':
      return 'text-red-500'
    case 'unknown':
      return 'text-yellow-500'
    default:
      return 'text-gray-500'
  }
}

export const getHealthStatusBadge = (status: string) => {
  switch (status) {
    case 'healthy':
      return 'health-healthy'
    case 'unhealthy':
      return 'health-unhealthy'
    case 'unknown':
      return 'health-unknown'
    default:
      return 'health-unknown'
  }
}

// Provider utilities
export const getProviderDisplayName = (provider: string) => {
  switch (provider) {
    case 'openai':
      return 'OpenAI'
    case 'anthropic':
      return 'Anthropic'
    case 'perplexity':
      return 'Perplexity'
    default:
      return provider.charAt(0).toUpperCase() + provider.slice(1)
  }
}

export const getProviderIcon = (provider: string) => {
  switch (provider) {
    case 'openai':
      return '🤖'
    case 'anthropic':
      return '🧠'
    case 'perplexity':
      return '🔍'
    default:
      return '⚡'
  }
}
