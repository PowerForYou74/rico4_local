'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { 
  Activity, 
  TrendingUp, 
  TrendingDown, 
  Clock, 
  DollarSign,
  Target,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';
import { useAutopilotStore } from '@/store/autopilot-store';
import { formatTimestamp, getStatusColor } from '@/lib/autopilot-api';

export default function OverviewTab() {
  const { 
    status, 
    metrics, 
    loading, 
    fetchMetrics 
  } = useAutopilotStore();

  const [timeRange, setTimeRange] = useState(24);

  useEffect(() => {
    fetchMetrics(timeRange);
  }, [timeRange, fetchMetrics]);

  const getTrendIcon = (value: number, baseline: number) => {
    if (value > baseline * 1.1) return <TrendingUp className="h-4 w-4 text-green-500" />;
    if (value < baseline * 0.9) return <TrendingDown className="h-4 w-4 text-red-500" />;
    return <Activity className="h-4 w-4 text-gray-500" />;
  };

  const getTrendColor = (value: number, baseline: number) => {
    if (value > baseline * 1.1) return 'text-green-600';
    if (value < baseline * 0.9) return 'text-red-600';
    return 'text-gray-600';
  };

  if (loading && !metrics) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Time Range Selector */}
      <div className="flex items-center gap-4">
        <span className="text-sm font-medium">Zeitraum:</span>
        <div className="flex gap-2">
          {[1, 24, 168].map((hours) => (
            <Button
              key={hours}
              variant={timeRange === hours ? 'default' : 'outline'}
              size="sm"
              onClick={() => setTimeRange(hours)}
            >
              {hours === 1 ? '1h' : hours === 24 ? '24h' : '7d'}
            </Button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Qualität</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics?.avg_quality_score ? (metrics.avg_quality_score * 100).toFixed(1) : '0.0'}%
            </div>
            <div className="flex items-center gap-2 mt-2">
              {getTrendIcon(metrics?.avg_quality_score || 0, 0.7)}
              <span className={`text-sm ${getTrendColor(metrics?.avg_quality_score || 0, 0.7)}`}>
                Baseline: 70%
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Latenz</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics?.avg_latency_ms ? Math.round(metrics.avg_latency_ms) : 0}ms
            </div>
            <div className="flex items-center gap-2 mt-2">
              {getTrendIcon(5000 - (metrics?.avg_latency_ms || 0), 5000)}
              <span className={`text-sm ${getTrendColor(5000 - (metrics?.avg_latency_ms || 0), 5000)}`}>
                Ziel: &lt;5s
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Kosten</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${metrics?.total_cost ? metrics.total_cost.toFixed(4) : '0.0000'}
            </div>
            <div className="flex items-center gap-2 mt-2">
              {getTrendIcon(metrics?.total_cost || 0, 0.1)}
              <span className={`text-sm ${getTrendColor(metrics?.total_cost || 0, 0.1)}`}>
                Budget: $20/Tag
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Fehlerrate</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics?.error_rate ? (metrics.error_rate * 100).toFixed(1) : '0.0'}%
            </div>
            <div className="flex items-center gap-2 mt-2">
              {metrics?.error_rate && metrics.error_rate > 0.05 ? (
                <TrendingUp className="h-4 w-4 text-red-500" />
              ) : (
                <CheckCircle className="h-4 w-4 text-green-500" />
              )}
              <span className={`text-sm ${metrics?.error_rate && metrics.error_rate > 0.05 ? 'text-red-600' : 'text-green-600'}`}>
                Limit: 5%
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Performance-Übersicht</CardTitle>
            <CardDescription>
              Wichtige Metriken der letzten {timeRange} Stunden
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Win-Rate</span>
                <span className="font-medium">
                  {metrics?.win_rate ? (metrics.win_rate * 100).toFixed(1) : '0.0'}%
                </span>
              </div>
              <Progress 
                value={metrics?.win_rate ? metrics.win_rate * 100 : 0} 
                className="h-2"
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Qualitätsscore</span>
                <span className="font-medium">
                  {metrics?.avg_quality_score ? (metrics.avg_quality_score * 100).toFixed(1) : '0.0'}%
                </span>
              </div>
              <Progress 
                value={metrics?.avg_quality_score ? metrics.avg_quality_score * 100 : 0} 
                className="h-2"
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Fehlerrate</span>
                <span className="font-medium">
                  {metrics?.error_rate ? (metrics.error_rate * 100).toFixed(1) : '0.0'}%
                </span>
              </div>
              <Progress 
                value={metrics?.error_rate ? metrics.error_rate * 100 : 0} 
                className="h-2"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>System-Status</CardTitle>
            <CardDescription>
              Aktueller Status der Autopilot-Komponenten
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm">Scheduler</span>
              <Badge variant={status?.scheduler?.running ? 'default' : 'secondary'}>
                {status?.scheduler?.running ? 'Aktiv' : 'Gestoppt'}
              </Badge>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm">Experimente</span>
              <Badge variant="outline">
                {status?.experiments?.running_count || 0} aktiv
              </Badge>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm">Wissensbasis</span>
              <Badge variant="outline">
                {status?.knowledge_base?.total_sources || 0} Quellen
              </Badge>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm">Letzte Ingest</span>
              <span className="text-sm text-muted-foreground">
                {status?.last_ingest === 'never' ? 'Nie' : formatTimestamp(status?.last_ingest || '')}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Aktuelle Aktivität</CardTitle>
          <CardDescription>
            Letzte Ereignisse und Status-Updates
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <Activity className="h-4 w-4 text-blue-500" />
              <div className="flex-1">
                <p className="text-sm font-medium">Autopilot aktiv</p>
                <p className="text-xs text-muted-foreground">
                  {formatTimestamp(status?.timestamp || '')}
                </p>
              </div>
              <Badge variant="default">Aktiv</Badge>
            </div>

            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <TrendingUp className="h-4 w-4 text-green-500" />
              <div className="flex-1">
                <p className="text-sm font-medium">Metriken aktualisiert</p>
                <p className="text-xs text-muted-foreground">
                  {metrics?.total_runs || 0} Runs in den letzten {timeRange}h
                </p>
              </div>
              <Badge variant="outline">
                {metrics?.total_runs || 0} Runs
              </Badge>
            </div>

            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <div className="flex-1">
                <p className="text-sm font-medium">System gesund</p>
                <p className="text-xs text-muted-foreground">
                  Alle Komponenten funktionieren normal
                </p>
              </div>
              <Badge variant="default">Gesund</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
