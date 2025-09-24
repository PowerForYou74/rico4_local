'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Activity, 
  Brain, 
  FlaskConical, 
  FileText, 
  History, 
  Settings,
  Play,
  Pause,
  RotateCcw,
  TrendingUp,
  AlertCircle,
  CheckCircle
} from 'lucide-react';

// Autopilot Store
import { useAutopilotStore } from '@/store/autopilot-store';

// Components
import OverviewTab from '@/components/autopilot/OverviewTab';
import ExperimentsTab from '@/components/autopilot/ExperimentsTab';
import PromptsTab from '@/components/autopilot/PromptsTab';
import KnowledgeTab from '@/components/autopilot/KnowledgeTab';
import ChangelogTab from '@/components/autopilot/ChangelogTab';
import HealthTab from '@/components/autopilot/HealthTab';

export default function AutopilotPage() {
  const [activeTab, setActiveTab] = useState('overview');
  const { 
    status, 
    health, 
    loading, 
    error, 
    fetchStatus, 
    fetchHealth 
  } = useAutopilotStore();

  useEffect(() => {
    fetchStatus();
    fetchHealth();
    
    // Polling alle 30 Sekunden
    const interval = setInterval(() => {
      fetchStatus();
      fetchHealth();
    }, 30000);

    return () => clearInterval(interval);
  }, [fetchStatus, fetchHealth]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'bg-green-500';
      case 'degraded': return 'bg-yellow-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'degraded': return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      case 'error': return <AlertCircle className="h-4 w-4 text-red-500" />;
      default: return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  if (loading && !status) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Brain className="h-8 w-8 text-blue-600" />
            Rico V5 Autopilot
          </h1>
          <p className="text-gray-600 mt-2">
            Selbstverbessernde Orchestrierung und kontinuierliche Optimierung
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            {getStatusIcon(health?.overall_status || 'unknown')}
            <span className="text-sm font-medium">
              {health?.overall_status || 'Unknown'}
            </span>
          </div>
          
          <Badge variant="outline" className="flex items-center gap-1">
            <Activity className="h-3 w-3" />
            {status?.scheduler?.enabled_jobs || 0} Jobs
          </Badge>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Fehler beim Laden der Autopilot-Daten: {error}
          </AlertDescription>
        </Alert>
      )}

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Status</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {status?.enabled ? 'Aktiv' : 'Inaktiv'}
            </div>
            <p className="text-xs text-muted-foreground">
              {status?.scheduler?.running ? 'Scheduler läuft' : 'Scheduler gestoppt'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">FlaskConicale</CardTitle>
            <FlaskConical className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {status?.experiments?.running_count || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Laufende FlaskConicale
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Wissensbasis</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {status?.knowledge_base?.total_sources || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Quellen verfügbar
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Letzte Ingest</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {status?.last_ingest === 'never' ? 'Nie' : 'Heute'}
            </div>
            <p className="text-xs text-muted-foreground">
              Wissensaufnahme
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Übersicht
          </TabsTrigger>
          <TabsTrigger value="experiments" className="flex items-center gap-2">
            <FlaskConical className="h-4 w-4" />
            FlaskConicale
          </TabsTrigger>
          <TabsTrigger value="prompts" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Prompts
          </TabsTrigger>
          <TabsTrigger value="knowledge" className="flex items-center gap-2">
            <Brain className="h-4 w-4" />
            Wissen
          </TabsTrigger>
          <TabsTrigger value="changelog" className="flex items-center gap-2">
            <History className="h-4 w-4" />
            Changelog
          </TabsTrigger>
          <TabsTrigger value="health" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Health
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <OverviewTab />
        </TabsContent>

        <TabsContent value="experiments" className="space-y-4">
          <ExperimentsTab />
        </TabsContent>

        <TabsContent value="prompts" className="space-y-4">
          <PromptsTab />
        </TabsContent>

        <TabsContent value="knowledge" className="space-y-4">
          <KnowledgeTab />
        </TabsContent>

        <TabsContent value="changelog" className="space-y-4">
          <ChangelogTab />
        </TabsContent>

        <TabsContent value="health" className="space-y-4">
          <HealthTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
