// frontend/src/lib/autopilot-api.ts
/**
 * Autopilot API Client
 * Zentrale API-Funktionen für Autopilot-Frontend
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export interface ApiResponse<T = any> {
  status: 'success' | 'error';
  data?: T;
  message?: string;
  error?: string;
}

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

// Generic API call function
async function apiCall<T = any>(
  endpoint: string, 
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    return {
      status: 'success',
      data,
    };
  } catch (error) {
    return {
      status: 'error',
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

// Status & Health
export async function getAutopilotStatus(): Promise<ApiResponse<AutopilotStatus>> {
  return apiCall<AutopilotStatus>('/v2/autopilot/status');
}

export async function getAutopilotHealth(): Promise<ApiResponse<AutopilotHealth>> {
  return apiCall<AutopilotHealth>('/v2/autopilot/health');
}

// Metrics
export async function getMetricsSummary(
  hours: number = 24,
  task?: string,
  provider?: string
): Promise<ApiResponse<AutopilotMetrics>> {
  const params = new URLSearchParams();
  params.append('hours', hours.toString());
  if (task) params.append('task', task);
  if (provider) params.append('provider', provider);

  return apiCall<AutopilotMetrics>(`/v2/autopilot/metrics/summary?${params}`);
}

export async function rollupMetrics(): Promise<ApiResponse<any>> {
  return apiCall('/v2/autopilot/metrics/rollup', {
    method: 'POST',
  });
}

export async function logMetrics(metrics: {
  task: string;
  provider: string;
  latency_ms: number;
  cost_est?: number;
  quality_score?: number;
  win?: boolean;
  error_type?: string;
  run_id?: string;
  experiment_id?: string;
  metadata?: Record<string, any>;
}): Promise<ApiResponse<{ run_id: string }>> {
  return apiCall<{ run_id: string }>('/v2/autopilot/metrics', {
    method: 'POST',
    body: JSON.stringify(metrics),
  });
}

// Experiments
export async function getExperiments(
  status?: string,
  limit: number = 50
): Promise<ApiResponse<AutopilotExperiment[]>> {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  params.append('limit', limit.toString());

  return apiCall<AutopilotExperiment[]>(`/v2/autopilot/experiments?${params}`);
}

export async function getExperimentStatus(
  experimentId: string
): Promise<ApiResponse<any>> {
  return apiCall(`/v2/autopilot/experiments/${experimentId}/status`);
}

export async function createExperiment(config: {
  name: string;
  type: string;
  variants: Record<string, any>;
  traffic_split: Record<string, number>;
  duration_hours?: number;
  min_samples?: number;
  success_criteria?: Record<string, any>;
  guardrails?: Record<string, any>;
}): Promise<ApiResponse<{ experiment_id: string }>> {
  return apiCall<{ experiment_id: string }>('/v2/autopilot/experiments', {
    method: 'POST',
    body: JSON.stringify(config),
  });
}

export async function startExperiment(experimentId: string): Promise<ApiResponse<void>> {
  return apiCall(`/v2/autopilot/experiments/${experimentId}/start`, {
    method: 'POST',
  });
}

export async function stopExperiment(experimentId: string): Promise<ApiResponse<void>> {
  return apiCall(`/v2/autopilot/experiments/${experimentId}/stop`, {
    method: 'POST',
  });
}

export async function evaluateExperiment(experimentId: string): Promise<ApiResponse<any>> {
  return apiCall(`/v2/autopilot/experiments/${experimentId}/evaluate`, {
    method: 'POST',
  });
}

// Evaluation & Optimization
export async function evaluateSystem(): Promise<ApiResponse<any>> {
  return apiCall('/v2/autopilot/evaluate', {
    method: 'POST',
  });
}

export async function optimizeSystem(
  basePrompt: string,
  objectives?: Record<string, number>
): Promise<ApiResponse<any>> {
  return apiCall('/v2/autopilot/optimize', {
    method: 'POST',
    body: JSON.stringify({
      base_prompt: basePrompt,
      objectives,
    }),
  });
}

// Registry Management
export async function proposeChanges(
  promptVariants?: any[],
  routingPolicies?: any[]
): Promise<ApiResponse<any>> {
  return apiCall('/v2/autopilot/propose', {
    method: 'POST',
    body: JSON.stringify({
      prompt_variants: promptVariants,
      routing_policies: routingPolicies,
    }),
  });
}

export async function applyChanges(
  promptIds?: string[],
  policyIds?: string[]
): Promise<ApiResponse<any>> {
  return apiCall('/v2/autopilot/apply', {
    method: 'POST',
    body: JSON.stringify({
      prompt_ids: promptIds,
      policy_ids: policyIds,
    }),
  });
}

export async function rollbackChanges(
  promptIds?: string[],
  policyIds?: string[]
): Promise<ApiResponse<any>> {
  return apiCall('/v2/autopilot/rollback', {
    method: 'POST',
    body: JSON.stringify({
      prompt_ids: promptIds,
      policy_ids: policyIds,
    }),
  });
}

// Knowledge Base
export async function getKnowledgeStats(): Promise<ApiResponse<AutopilotKnowledgeStats>> {
  return apiCall<AutopilotKnowledgeStats>('/v2/autopilot/kb/stats');
}

export async function ingestKnowledge(
  docsPath: string = 'docs',
  resultsPath: string = 'data/results'
): Promise<ApiResponse<any>> {
  return apiCall('/v2/autopilot/kb/ingest', {
    method: 'POST',
    body: JSON.stringify({
      docs_path: docsPath,
      results_path: resultsPath,
    }),
  });
}

// Scheduler
export async function getSchedulerStatus(): Promise<ApiResponse<any>> {
  return apiCall('/v2/autopilot/scheduler/status');
}

export async function runJobManually(jobId: string): Promise<ApiResponse<any>> {
  return apiCall(`/v2/autopilot/scheduler/jobs/${jobId}/run`, {
    method: 'POST',
  });
}

// Utility functions
export function formatTimestamp(timestamp: string): string {
  return new Date(timestamp).toLocaleString('de-DE');
}

export function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  } else if (seconds < 3600) {
    return `${Math.round(seconds / 60)}m`;
  } else {
    return `${Math.round(seconds / 3600)}h`;
  }
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'healthy':
    case 'active':
    case 'running':
    case 'completed':
      return 'text-green-600';
    case 'degraded':
    case 'warning':
    case 'stopped':
      return 'text-yellow-600';
    case 'error':
    case 'failed':
    case 'stopped':
      return 'text-red-600';
    default:
      return 'text-gray-600';
  }
}

export function getStatusBadgeVariant(status: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (status) {
    case 'healthy':
    case 'active':
    case 'running':
    case 'completed':
      return 'default';
    case 'degraded':
    case 'warning':
      return 'secondary';
    case 'error':
    case 'failed':
      return 'destructive';
    default:
      return 'outline';
  }
}
