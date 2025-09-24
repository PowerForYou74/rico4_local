'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { 
  Settings, 
  CheckCircle, 
  AlertCircle, 
  XCircle,
  RefreshCw,
  Activity,
  Clock,
  Database,
  Brain,
  Experiment,
  FileText
} from 'lucide-react';
import { useAutopilotStore } from '@/store/autopilot-store';
import { formatTimestamp } from '@/lib/autopilot-api';

export default function HealthTab() {
  const { 
    health, 
    status,
    loading, 
    error, 
    fetchHealth,
    fetchStatus,
    runJobManually
  } = useAutopilotStore();

  const [runningJobs, setRunningJobs] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchHealth();
    fetchStatus();
  }, [fetchHealth, fetchStatus]);

  const handleRunJob = async (jobId: string) => {
    setRunningJobs(prev => new Set(prev).add(jobId));
    try {
      await runJobManually(jobId);
    } catch (error) {
      console.error('Error running job:', error);
    } finally {
      setRunningJobs(prev => {
        const newSet = new Set(prev);
        newSet.delete(jobId);
        return newSet;
      });
    }
  };

  const getComponentStatusIcon = (status: string) => {
    switch (status) {
      case 'ok':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
    }
  };

  const getComponentStatusColor = (status: string) => {
    switch (status) {
      case 'ok':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
      default:
        return 'text-yellow-600';
    }
  };

  const getOverallStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-6 w-6 text-green-500" />;
      case 'degraded':
        return <AlertCircle className="h-6 w-6 text-yellow-500" />;
      case 'error':
        return <XCircle className="h-6 w-6 text-red-500" />;
      default:
        return <Activity className="h-6 w-6 text-gray-500" />;
    }
  };

  const getOverallStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600';
      case 'degraded':
        return 'text-yellow-600';
      case 'error':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  if (loading && !health) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">System Health</h2>
          <p className="text-gray-600">
            Überwachung der Autopilot-Komponenten und System-Status
          </p>
        </div>
        
        <Button 
          variant="outline"
          onClick={() => {
            fetchHealth();
            fetchStatus();
          }}
          disabled={loading}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Aktualisieren
        </Button>
      </div>

      {/* Overall Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {getOverallStatusIcon(health?.overall_status || 'unknown')}
            Gesamtstatus
          </CardTitle>
          <CardDescription>
            Aktueller Status des Autopilot-Systems
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <div className={`text-2xl font-bold ${getOverallStatusColor(health?.overall_status || 'unknown')}`}>
                {health?.overall_status || 'Unknown'}
              </div>
              <p className="text-sm text-gray-500">
                Letzte Aktualisierung: {formatTimestamp(health?.timestamp || '')}
              </p>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-500">Komponenten</div>
              <div className="text-lg font-semibold">
                {health?.components ? Object.keys(health.components).length : 0}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <XCircle className="h-4 w-4 text-red-500" />
            <span className="text-sm text-red-700">
              Fehler beim Laden der Health-Daten: {error}
            </span>
          </div>
        </div>
      )}

      {/* Component Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {health?.components && Object.entries(health.components).map(([component, status]) => (
          <Card key={component}>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium capitalize">
                  {component.replace('_', ' ')}
                </CardTitle>
                {getComponentStatusIcon(status.status)}
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className={`text-sm ${getComponentStatusColor(status.status)}`}>
                  {status.status === 'ok' ? 'Funktioniert' : 'Fehler'}
                </div>
                <div className="text-xs text-gray-500">
                  {status.message}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Scheduler Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Scheduler Status
          </CardTitle>
          <CardDescription>
            Status der geplanten Jobs und Aufgaben
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {status?.scheduler?.jobs_count || 0}
                </div>
                <div className="text-sm text-gray-500">Gesamt Jobs</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {status?.scheduler?.enabled_jobs || 0}
                </div>
                <div className="text-sm text-gray-500">Aktive Jobs</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {status?.experiments?.running_count || 0}
                </div>
                <div className="text-sm text-gray-500">Laufende Experimente</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {status?.knowledge_base?.total_sources || 0}
                </div>
                <div className="text-sm text-gray-500">Wissensquellen</div>
              </div>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-blue-500" />
                <span className="text-sm font-medium">Scheduler Status</span>
              </div>
              <Badge variant={status?.scheduler?.running ? 'default' : 'secondary'}>
                {status?.scheduler?.running ? 'Aktiv' : 'Gestoppt'}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Manual Job Execution */}
      <Card>
        <CardHeader>
          <CardTitle>Manuelle Job-Ausführung</CardTitle>
          <CardDescription>
            Führe Jobs manuell aus für Tests und Wartung
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <h4 className="text-sm font-medium flex items-center gap-2">
                <Database className="h-4 w-4" />
                Metriken-Rollup
              </h4>
              <p className="text-xs text-gray-500">
                Stündliche Zusammenfassung der Metriken
              </p>
              <Button 
                size="sm" 
                variant="outline"
                onClick={() => handleRunJob('hourly_metrics_rollup')}
                disabled={runningJobs.has('hourly_metrics_rollup')}
              >
                {runningJobs.has('hourly_metrics_rollup') ? (
                  <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                ) : (
                  <Activity className="h-3 w-3 mr-1" />
                )}
                Jetzt ausführen
              </Button>
            </div>

            <div className="space-y-2">
              <h4 className="text-sm font-medium flex items-center gap-2">
                <Experiment className="h-4 w-4" />
                Experiment-Auswertung
              </h4>
              <p className="text-xs text-gray-500">
                Tägliche Auswertung der Experimente
              </p>
              <Button 
                size="sm" 
                variant="outline"
                onClick={() => handleRunJob('daily_experiments_tick')}
                disabled={runningJobs.has('daily_experiments_tick')}
              >
                {runningJobs.has('daily_experiments_tick') ? (
                  <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                ) : (
                  <Activity className="h-3 w-3 mr-1" />
                )}
                Jetzt ausführen
              </Button>
            </div>

            <div className="space-y-2">
              <h4 className="text-sm font-medium flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Prompt-Review
              </h4>
              <p className="text-xs text-gray-500">
                Wöchentliche Überprüfung der Prompts
              </p>
              <Button 
                size="sm" 
                variant="outline"
                onClick={() => handleRunJob('weekly_prompt_review')}
                disabled={runningJobs.has('weekly_prompt_review')}
              >
                {runningJobs.has('weekly_prompt_review') ? (
                  <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                ) : (
                  <Activity className="h-3 w-3 mr-1" />
                )}
                Jetzt ausführen
              </Button>
            </div>

            <div className="space-y-2">
              <h4 className="text-sm font-medium flex items-center gap-2">
                <Brain className="h-4 w-4" />
                Wissensaufnahme
              </h4>
              <p className="text-xs text-gray-500">
                Tägliche Wissensaufnahme und -verarbeitung
              </p>
              <Button 
                size="sm" 
                variant="outline"
                onClick={() => handleRunJob('daily_kb_ingest')}
                disabled={runningJobs.has('daily_kb_ingest')}
              >
                {runningJobs.has('daily_kb_ingest') ? (
                  <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                ) : (
                  <Activity className="h-3 w-3 mr-1" />
                )}
                Jetzt ausführen
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* System Information */}
      <Card>
        <CardHeader>
          <CardTitle>System-Informationen</CardTitle>
          <CardDescription>
            Technische Details und Konfiguration
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Autopilot Status</h4>
              <div className="text-sm text-gray-600">
                {status?.enabled ? 'Aktiviert' : 'Deaktiviert'}
              </div>
            </div>

            <div className="space-y-2">
              <h4 className="text-sm font-medium">Letzte Aktualisierung</h4>
              <div className="text-sm text-gray-600">
                {formatTimestamp(status?.timestamp || '')}
              </div>
            </div>

            <div className="space-y-2">
              <h4 className="text-sm font-medium">Scheduler Status</h4>
              <div className="text-sm text-gray-600">
                {status?.scheduler?.running ? 'Läuft' : 'Gestoppt'}
              </div>
            </div>

            <div className="space-y-2">
              <h4 className="text-sm font-medium">Aktive Jobs</h4>
              <div className="text-sm text-gray-600">
                {status?.scheduler?.enabled_jobs || 0} von {status?.scheduler?.jobs_count || 0}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
