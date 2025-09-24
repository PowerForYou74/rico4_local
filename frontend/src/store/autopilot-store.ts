'use client';

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

// Types
export interface AutopilotStatus {
  enabled: boolean;
  timestamp: string;
  scheduler: {
    running: boolean;
    jobs_count: number;
    enabled_jobs: number;
  };
  experiments: {
    running_count: number;
    experiments: Array<{
      experiment_id: string;
      status: string;
      start_time: string | null;
    }>;
  };
  knowledge_base: {
    total_sources: number;
    total_chunks: number;
    total_summaries: number;
  };
  last_ingest: string;
}

export interface AutopilotHealth {
  overall_status: 'healthy' | 'degraded' | 'error';
  timestamp: string;
  components: {
    [key: string]: {
      status: 'ok' | 'error';
      message: string;
    };
  };
}

export interface AutopilotMetrics {
  total_runs: number;
  avg_latency_ms: number;
  total_cost: number;
  error_rate: number;
  win_rate: number;
  avg_quality_score: number;
}

export interface AutopilotExperiment {
  experiment_id: string;
  name: string;
  type: string;
  status: string;
  start_time: string | null;
  end_time: string | null;
  variants: Record<string, any>;
  traffic_split: Record<string, number>;
  success_criteria: Record<string, any>;
  guardrails: Record<string, any>;
}

export interface AutopilotPrompt {
  id: string;
  name: string;
  description: string;
  current_version: string;
  status: string;
  created_at: string;
  updated_at: string;
  versions: Record<string, any>;
}

export interface AutopilotPolicy {
  id: string;
  name: string;
  description: string;
  policy_type: string;
  current_version: string;
  status: string;
  created_at: string;
  updated_at: string;
  versions: Record<string, any>;
}

export interface AutopilotKnowledgeStats {
  total_sources: number;
  total_chunks: number;
  total_summaries: number;
  sources_by_type: Record<string, number>;
  chunks_by_type: Record<string, number>;
}

export interface AutopilotChangelogEntry {
  id: string;
  timestamp: string;
  action: string;
  entity_type: string;
  entity_id: string;
  version: string;
  description: string;
  metadata: Record<string, any>;
}

// Store State
interface AutopilotState {
  // Status
  status: AutopilotStatus | null;
  health: AutopilotHealth | null;
  loading: boolean;
  error: string | null;

  // Data
  metrics: AutopilotMetrics | null;
  experiments: AutopilotExperiment[];
  prompts: AutopilotPrompt[];
  policies: AutopilotPolicy[];
  knowledgeStats: AutopilotKnowledgeStats | null;
  changelog: AutopilotChangelogEntry[];

  // Actions
  fetchStatus: () => Promise<void>;
  fetchHealth: () => Promise<void>;
  fetchMetrics: (hours?: number, task?: string, provider?: string) => Promise<void>;
  fetchExperiments: (status?: string, limit?: number) => Promise<void>;
  fetchPrompts: () => Promise<void>;
  fetchPolicies: () => Promise<void>;
  fetchKnowledgeStats: () => Promise<void>;
  fetchChangelog: () => Promise<void>;

  // Experiment Actions
  createExperiment: (config: Partial<AutopilotExperiment>) => Promise<string>;
  startExperiment: (experimentId: string) => Promise<void>;
  stopExperiment: (experimentId: string) => Promise<void>;
  evaluateExperiment: (experimentId: string) => Promise<any>;

  // Registry Actions
  proposeChanges: (prompts?: any[], policies?: any[]) => Promise<void>;
  applyChanges: (promptIds?: string[], policyIds?: string[]) => Promise<void>;
  rollbackChanges: (promptIds?: string[], policyIds?: string[]) => Promise<void>;

  // Knowledge Actions
  ingestKnowledge: (docsPath?: string, resultsPath?: string) => Promise<void>;

  // Scheduler Actions
  runJobManually: (jobId: string) => Promise<any>;
}

// API Client
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

const apiCall = async (endpoint: string, options: RequestInit = {}) => {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }

  return response.json();
};

// Store Implementation
export const useAutopilotStore = create<AutopilotState>()(
  devtools(
    (set, get) => ({
      // Initial State
      status: null,
      health: null,
      loading: false,
      error: null,
      metrics: null,
      experiments: [],
      prompts: [],
      policies: [],
      knowledgeStats: null,
      changelog: [],

      // Status Actions
      fetchStatus: async () => {
        set({ loading: true, error: null });
        try {
          const status = await apiCall('/v2/autopilot/status');
          set({ status, loading: false });
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Unknown error',
            loading: false 
          });
        }
      },

      fetchHealth: async () => {
        try {
          const health = await apiCall('/v2/autopilot/health');
          set({ health });
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Unknown error'
          });
        }
      },

      // Data Actions
      fetchMetrics: async (hours = 24, task, provider) => {
        try {
          const params = new URLSearchParams();
          if (hours) params.append('hours', hours.toString());
          if (task) params.append('task', task);
          if (provider) params.append('provider', provider);

          const response = await apiCall(`/v2/autopilot/metrics/summary?${params}`);
          set({ metrics: response.summary });
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Unknown error'
          });
        }
      },

      fetchExperiments: async (status, limit = 50) => {
        try {
          const params = new URLSearchParams();
          if (status) params.append('status', status);
          if (limit) params.append('limit', limit.toString());

          const response = await apiCall(`/v2/autopilot/experiments?${params}`);
          set({ experiments: response.experiments });
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Unknown error'
          });
        }
      },

      fetchPrompts: async () => {
        try {
          // Mock data - in real implementation, this would call the API
          const prompts: AutopilotPrompt[] = [
            {
              id: 'prompt_1',
              name: 'Master Prompt V5',
              description: 'Hauptprompt für Rico V5',
              current_version: 'v1.0.0',
              status: 'active',
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
              versions: {}
            }
          ];
          set({ prompts });
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Unknown error'
          });
        }
      },

      fetchPolicies: async () => {
        try {
          // Mock data - in real implementation, this would call the API
          const policies: AutopilotPolicy[] = [
            {
              id: 'policy_1',
              name: 'Routing Policy V1',
              description: 'Standard-Routing-Policy',
              policy_type: 'routing',
              current_version: 'v1.0.0',
              status: 'active',
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
              versions: {}
            }
          ];
          set({ policies });
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Unknown error'
          });
        }
      },

      fetchKnowledgeStats: async () => {
        try {
          const response = await apiCall('/v2/autopilot/kb/stats');
          set({ knowledgeStats: response.stats });
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Unknown error'
          });
        }
      },

      fetchChangelog: async () => {
        try {
          // Mock data - in real implementation, this would call the API
          const changelog: AutopilotChangelogEntry[] = [
            {
              id: 'changelog_1',
              timestamp: new Date().toISOString(),
              action: 'created',
              entity_type: 'prompt',
              entity_id: 'prompt_1',
              version: '1.0.0',
              description: 'Created prompt "Master Prompt V5"',
              metadata: {}
            }
          ];
          set({ changelog });
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Unknown error'
          });
        }
      },

      // Experiment Actions
      createExperiment: async (config) => {
        try {
          const response = await apiCall('/v2/autopilot/experiments', {
            method: 'POST',
            body: JSON.stringify(config)
          });
          await get().fetchExperiments();
          return response.experiment_id;
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Unknown error'
          });
          throw error;
        }
      },

      startExperiment: async (experimentId) => {
        try {
          await apiCall(`/v2/autopilot/experiments/${experimentId}/start`, {
            method: 'POST'
          });
          await get().fetchExperiments();
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Unknown error'
          });
        }
      },

      stopExperiment: async (experimentId) => {
        try {
          await apiCall(`/v2/autopilot/experiments/${experimentId}/stop`, {
            method: 'POST'
          });
          await get().fetchExperiments();
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Unknown error'
          });
        }
      },

      evaluateExperiment: async (experimentId) => {
        try {
          const response = await apiCall(`/v2/autopilot/experiments/${experimentId}/evaluate`, {
            method: 'POST'
          });
          return response.evaluation;
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Unknown error'
          });
          throw error;
        }
      },

      // Registry Actions
      proposeChanges: async (prompts, policies) => {
        try {
          await apiCall('/v2/autopilot/propose', {
            method: 'POST',
            body: JSON.stringify({ prompt_variants: prompts, routing_policies: policies })
          });
          await get().fetchPrompts();
          await get().fetchPolicies();
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Unknown error'
          });
        }
      },

      applyChanges: async (promptIds, policyIds) => {
        try {
          await apiCall('/v2/autopilot/apply', {
            method: 'POST',
            body: JSON.stringify({ prompt_ids: promptIds, policy_ids: policyIds })
          });
          await get().fetchPrompts();
          await get().fetchPolicies();
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Unknown error'
          });
        }
      },

      rollbackChanges: async (promptIds, policyIds) => {
        try {
          await apiCall('/v2/autopilot/rollback', {
            method: 'POST',
            body: JSON.stringify({ prompt_ids: promptIds, policy_ids: policyIds })
          });
          await get().fetchPrompts();
          await get().fetchPolicies();
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Unknown error'
          });
        }
      },

      // Knowledge Actions
      ingestKnowledge: async (docsPath = 'docs', resultsPath = 'data/results') => {
        try {
          await apiCall('/v2/autopilot/kb/ingest', {
            method: 'POST',
            body: JSON.stringify({ docs_path: docsPath, results_path: resultsPath })
          });
          await get().fetchKnowledgeStats();
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Unknown error'
          });
        }
      },

      // Scheduler Actions
      runJobManually: async (jobId) => {
        try {
          const response = await apiCall(`/v2/autopilot/scheduler/jobs/${jobId}/run`, {
            method: 'POST'
          });
          return response.job_result;
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Unknown error'
          });
          throw error;
        }
      },
    }),
    {
      name: 'autopilot-store',
    }
  )
);
