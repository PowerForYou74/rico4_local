'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  History, 
  Plus, 
  Edit, 
  RotateCcw, 
  ArrowUp, 
  ArrowDown,
  FileText,
  Settings,
  Search,
  Filter,
  Calendar
} from 'lucide-react';
import { useAutopilotStore } from '@/store/autopilot-store';
import { formatTimestamp } from '@/lib/autopilot-api';

export default function ChangelogTab() {
  const { 
    changelog, 
    loading, 
    error, 
    fetchChangelog
  } = useAutopilotStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterAction, setFilterAction] = useState('all');

  useEffect(() => {
    fetchChangelog();
  }, [fetchChangelog]);

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'created':
        return <Plus className="h-4 w-4 text-green-500" />;
      case 'updated':
        return <Edit className="h-4 w-4 text-blue-500" />;
      case 'promoted':
        return <ArrowUp className="h-4 w-4 text-purple-500" />;
      case 'deprecated':
        return <ArrowDown className="h-4 w-4 text-yellow-500" />;
      case 'rolled_back':
        return <RotateCcw className="h-4 w-4 text-red-500" />;
      default:
        return <History className="h-4 w-4 text-gray-500" />;
    }
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case 'created':
        return 'bg-green-100 text-green-800';
      case 'updated':
        return 'bg-blue-100 text-blue-800';
      case 'promoted':
        return 'bg-purple-100 text-purple-800';
      case 'deprecated':
        return 'bg-yellow-100 text-yellow-800';
      case 'rolled_back':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getEntityIcon = (entityType: string) => {
    switch (entityType) {
      case 'prompt':
        return <FileText className="h-4 w-4 text-blue-500" />;
      case 'policy':
        return <Settings className="h-4 w-4 text-purple-500" />;
      default:
        return <History className="h-4 w-4 text-gray-500" />;
    }
  };

  const filteredChangelog = changelog.filter(entry => {
    const matchesSearch = entry.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         entry.entity_id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = filterType === 'all' || entry.entity_type === filterType;
    const matchesAction = filterAction === 'all' || entry.action === filterAction;
    
    return matchesSearch && matchesType && matchesAction;
  });

  if (loading && changelog.length === 0) {
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
          <h2 className="text-2xl font-bold">Changelog</h2>
          <p className="text-gray-600">
            Historie aller Änderungen und Deployments
          </p>
        </div>
        
        <Button 
          variant="outline"
          onClick={() => fetchChangelog()}
          disabled={loading}
        >
          <History className="h-4 w-4 mr-2" />
          Aktualisieren
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Changelog durchsuchen..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            
            <div className="flex gap-2">
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="px-3 py-2 border rounded-md text-sm"
              >
                <option value="all">Alle Typen</option>
                <option value="prompt">Prompts</option>
                <option value="policy">Policies</option>
              </select>
              
              <select
                value={filterAction}
                onChange={(e) => setFilterAction(e.target.value)}
                className="px-3 py-2 border rounded-md text-sm"
              >
                <option value="all">Alle Aktionen</option>
                <option value="created">Erstellt</option>
                <option value="updated">Aktualisiert</option>
                <option value="promoted">Befördert</option>
                <option value="deprecated">Deprecated</option>
                <option value="rolled_back">Rollback</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <History className="h-4 w-4 text-red-500" />
            <span className="text-sm text-red-700">
              Fehler beim Laden des Changelogs: {error}
            </span>
          </div>
        </div>
      )}

      {/* Changelog Entries */}
      <div className="space-y-4">
        {filteredChangelog.map((entry) => (
          <Card key={entry.id}>
            <CardContent className="pt-6">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0">
                  {getActionIcon(entry.action)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge className={getActionColor(entry.action)}>
                      {entry.action.replace('_', ' ')}
                    </Badge>
                    <Badge variant="outline">
                      {entry.entity_type}
                    </Badge>
                    <Badge variant="outline">
                      v{entry.version}
                    </Badge>
                  </div>
                  
                  <h3 className="text-sm font-medium text-gray-900 mb-1">
                    {entry.description}
                  </h3>
                  
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <div className="flex items-center gap-1">
                      {getEntityIcon(entry.entity_type)}
                      <span>{entry.entity_id}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      <span>{formatTimestamp(entry.timestamp)}</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Empty State */}
      {filteredChangelog.length === 0 && !loading && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <History className="h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {searchQuery || filterType !== 'all' || filterAction !== 'all' 
                ? 'Keine Einträge gefunden' 
                : 'Kein Changelog vorhanden'
              }
            </h3>
            <p className="text-gray-500 text-center mb-4">
              {searchQuery || filterType !== 'all' || filterAction !== 'all'
                ? 'Versuche andere Suchbegriffe oder Filter.'
                : 'Changelog-Einträge werden automatisch erstellt, wenn Änderungen vorgenommen werden.'
              }
            </p>
            {(searchQuery || filterType !== 'all' || filterAction !== 'all') && (
              <Button 
                variant="outline"
                onClick={() => {
                  setSearchQuery('');
                  setFilterType('all');
                  setFilterAction('all');
                }}
              >
                Filter zurücksetzen
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Statistics */}
      {changelog.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Changelog-Statistiken</CardTitle>
            <CardDescription>
              Übersicht über die Changelog-Aktivität
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {changelog.filter(e => e.entity_type === 'prompt').length}
                </div>
                <div className="text-sm text-gray-500">Prompt-Änderungen</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {changelog.filter(e => e.entity_type === 'policy').length}
                </div>
                <div className="text-sm text-gray-500">Policy-Änderungen</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {changelog.filter(e => e.action === 'created').length}
                </div>
                <div className="text-sm text-gray-500">Erstellt</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">
                  {changelog.filter(e => e.action === 'rolled_back').length}
                </div>
                <div className="text-sm text-gray-500">Rollbacks</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
