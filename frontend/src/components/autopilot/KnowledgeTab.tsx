'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { 
  Brain, 
  FileText, 
  Database, 
  RefreshCw, 
  Upload,
  Search,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import { useAutopilotStore } from '@/store/autopilot-store';
import { formatTimestamp } from '@/lib/autopilot-api';

export default function KnowledgeTab() {
  const { 
    knowledgeStats, 
    loading, 
    error, 
    fetchKnowledgeStats,
    ingestKnowledge
  } = useAutopilotStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [isIngesting, setIsIngesting] = useState(false);
  const [ingestProgress, setIngestProgress] = useState(0);

  useEffect(() => {
    fetchKnowledgeStats();
  }, [fetchKnowledgeStats]);

  const handleIngest = async () => {
    setIsIngesting(true);
    setIngestProgress(0);
    
    try {
      // Simuliere Progress
      const interval = setInterval(() => {
        setIngestProgress(prev => {
          if (prev >= 90) {
            clearInterval(interval);
            return prev;
          }
          return prev + Math.random() * 10;
        });
      }, 200);

      await ingestKnowledge();
      
      clearInterval(interval);
      setIngestProgress(100);
      
      // Reset nach 2 Sekunden
      setTimeout(() => {
        setIsIngesting(false);
        setIngestProgress(0);
      }, 2000);
    } catch (error) {
      console.error('Error ingesting knowledge:', error);
      setIsIngesting(false);
      setIngestProgress(0);
    }
  };

  const getSourceTypeColor = (type: string) => {
    switch (type) {
      case 'file': return 'bg-blue-100 text-blue-800';
      case 'web': return 'bg-green-100 text-green-800';
      case 'api': return 'bg-purple-100 text-purple-800';
      case 'manual': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getChunkTypeColor = (type: string) => {
    switch (type) {
      case 'markdown': return 'bg-blue-100 text-blue-800';
      case 'code': return 'bg-green-100 text-green-800';
      case 'text': return 'bg-gray-100 text-gray-800';
      case 'summary': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading && !knowledgeStats) {
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
          <h2 className="text-2xl font-bold">Wissensbasis</h2>
          <p className="text-gray-600">
            Kontinuierliche Wissensaufnahme und -verarbeitung
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button 
            variant="outline"
            onClick={() => fetchKnowledgeStats()}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Aktualisieren
          </Button>
          
          <Button 
            onClick={handleIngest}
            disabled={isIngesting}
          >
            <Upload className="h-4 w-4 mr-2" />
            {isIngesting ? 'Ingest läuft...' : 'Wissensaufnahme'}
          </Button>
        </div>
      </div>

      {/* Ingest Progress */}
      {isIngesting && (
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Wissensaufnahme läuft...</span>
                <span>{Math.round(ingestProgress)}%</span>
              </div>
              <Progress value={ingestProgress} className="h-2" />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-red-500" />
            <span className="text-sm text-red-700">
              Fehler beim Laden der Wissensbasis: {error}
            </span>
          </div>
        </div>
      )}

      {/* Search */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Wissenssuche
          </CardTitle>
          <CardDescription>
            Durchsuche die Wissensbasis nach relevanten Informationen
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              placeholder="Suchbegriff eingeben..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <Button variant="outline">
              <Search className="h-4 w-4 mr-2" />
              Suchen
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Quellen</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {knowledgeStats?.total_sources || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Wissensquellen verfügbar
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Chunks</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {knowledgeStats?.total_chunks || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Verarbeitete Textblöcke
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Zusammenfassungen</CardTitle>
            <Brain className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {knowledgeStats?.total_summaries || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Erstellte Zusammenfassungen
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Source Types */}
      {knowledgeStats?.sources_by_type && Object.keys(knowledgeStats.sources_by_type).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Quellen nach Typ</CardTitle>
            <CardDescription>
              Verteilung der Wissensquellen nach Typ
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(knowledgeStats.sources_by_type).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge className={getSourceTypeColor(type)}>
                      {type}
                    </Badge>
                    <span className="text-sm capitalize">{type} Quellen</span>
                  </div>
                  <span className="text-sm font-medium">{count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Chunk Types */}
      {knowledgeStats?.chunks_by_type && Object.keys(knowledgeStats.chunks_by_type).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Chunks nach Typ</CardTitle>
            <CardDescription>
              Verteilung der Textblöcke nach Typ
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(knowledgeStats.chunks_by_type).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge className={getChunkTypeColor(type)}>
                      {type}
                    </Badge>
                    <span className="text-sm capitalize">{type} Chunks</span>
                  </div>
                  <span className="text-sm font-medium">{count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Aktuelle Aktivität</CardTitle>
          <CardDescription>
            Letzte Wissensaufnahme und Verarbeitung
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <Upload className="h-4 w-4 text-blue-500" />
              <div className="flex-1">
                <p className="text-sm font-medium">Wissensaufnahme geplant</p>
                <p className="text-xs text-muted-foreground">
                  Tägliche automatische Wissensaufnahme läuft
                </p>
              </div>
              <Badge variant="outline">
                <Clock className="h-3 w-3 mr-1" />
                Geplant
              </Badge>
            </div>

            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <div className="flex-1">
                <p className="text-sm font-medium">Wissensbasis aktuell</p>
                <p className="text-xs text-muted-foreground">
                  {knowledgeStats?.total_sources || 0} Quellen, {knowledgeStats?.total_chunks || 0} Chunks verfügbar
                </p>
              </div>
              <Badge variant="default">
                <CheckCircle className="h-3 w-3 mr-1" />
                Aktiv
              </Badge>
            </div>

            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <TrendingUp className="h-4 w-4 text-green-500" />
              <div className="flex-1">
                <p className="text-sm font-medium">Wachstum der Wissensbasis</p>
                <p className="text-xs text-muted-foreground">
                  Kontinuierliche Erweiterung durch neue Quellen
                </p>
              </div>
              <Badge variant="outline">
                <TrendingUp className="h-3 w-3 mr-1" />
                Wachsend
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Empty State */}
      {(!knowledgeStats || knowledgeStats.total_sources === 0) && !loading && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Brain className="h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Wissensbasis ist leer
            </h3>
            <p className="text-gray-500 text-center mb-4">
              Starte die Wissensaufnahme, um Dokumente und Informationen zu verarbeiten.
            </p>
            <Button onClick={handleIngest}>
              <Upload className="h-4 w-4 mr-2" />
              Erste Wissensaufnahme starten
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
