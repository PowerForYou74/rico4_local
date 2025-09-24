'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger 
} from '@/components/ui/dialog';
import { 
  Play, 
  Pause, 
  Settings, 
  Plus, 
  BarChart3, 
  Clock,
  Target,
  AlertCircle,
  CheckCircle
} from 'lucide-react';
import { useAutopilotStore } from '@/store/autopilot-store';
import { formatTimestamp, getStatusBadgeVariant } from '@/lib/autopilot-api';

export default function ExperimentsTab() {
  const { 
    experiments, 
    loading, 
    error, 
    fetchExperiments,
    createExperiment,
    startExperiment,
    stopExperiment,
    evaluateExperiment
  } = useAutopilotStore();

  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newExperiment, setNewExperiment] = useState({
    name: '',
    type: 'ab',
    variants: { A: '', B: '' },
    traffic_split: { A: 0.5, B: 0.5 },
    duration_hours: 24,
    min_samples: 100
  });

  useEffect(() => {
    fetchExperiments();
  }, [fetchExperiments]);

  const handleCreateExperiment = async () => {
    try {
      await createExperiment(newExperiment);
      setShowCreateDialog(false);
      setNewExperiment({
        name: '',
        type: 'ab',
        variants: { A: '', B: '' },
        traffic_split: { A: 0.5, B: 0.5 },
        duration_hours: 24,
        min_samples: 100
      });
    } catch (error) {
      console.error('Error creating experiment:', error);
    }
  };

  const handleStartExperiment = async (experimentId: string) => {
    try {
      await startExperiment(experimentId);
    } catch (error) {
      console.error('Error starting experiment:', error);
    }
  };

  const handleStopExperiment = async (experimentId: string) => {
    try {
      await stopExperiment(experimentId);
    } catch (error) {
      console.error('Error stopping experiment:', error);
    }
  };

  const handleEvaluateExperiment = async (experimentId: string) => {
    try {
      const result = await evaluateExperiment(experimentId);
      console.log('Experiment evaluation:', result);
    } catch (error) {
      console.error('Error evaluating experiment:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Play className="h-4 w-4 text-green-500" />;
      case 'stopped':
        return <Pause className="h-4 w-4 text-yellow-500" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-blue-500" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Settings className="h-4 w-4 text-gray-500" />;
    }
  };

  if (loading && experiments.length === 0) {
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
          <h2 className="text-2xl font-bold">Experimente</h2>
          <p className="text-gray-600">
            A/B Tests und kontinuierliche Optimierung
          </p>
        </div>
        
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Neues Experiment
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Neues Experiment erstellen</DialogTitle>
              <DialogDescription>
                Erstelle ein neues A/B Test Experiment für die Autopilot-Optimierung.
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name">Name</Label>
                  <Input
                    id="name"
                    value={newExperiment.name}
                    onChange={(e) => setNewExperiment({ ...newExperiment, name: e.target.value })}
                    placeholder="Experiment Name"
                  />
                </div>
                <div>
                  <Label htmlFor="type">Typ</Label>
                  <select
                    id="type"
                    value={newExperiment.type}
                    onChange={(e) => setNewExperiment({ ...newExperiment, type: e.target.value })}
                    className="w-full p-2 border rounded-md"
                  >
                    <option value="ab">A/B Test</option>
                    <option value="prompt">Prompt-Optimierung</option>
                    <option value="routing">Routing-Optimierung</option>
                  </select>
                </div>
              </div>

              <div>
                <Label>Varianten</Label>
                <div className="grid grid-cols-2 gap-4 mt-2">
                  <div>
                    <Label htmlFor="variantA">Variante A</Label>
                    <Textarea
                      id="variantA"
                      value={newExperiment.variants.A}
                      onChange={(e) => setNewExperiment({ 
                        ...newExperiment, 
                        variants: { ...newExperiment.variants, A: e.target.value }
                      })}
                      placeholder="Variante A Beschreibung"
                      rows={3}
                    />
                  </div>
                  <div>
                    <Label htmlFor="variantB">Variante B</Label>
                    <Textarea
                      id="variantB"
                      value={newExperiment.variants.B}
                      onChange={(e) => setNewExperiment({ 
                        ...newExperiment, 
                        variants: { ...newExperiment.variants, B: e.target.value }
                      })}
                      placeholder="Variante B Beschreibung"
                      rows={3}
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="duration">Dauer (Stunden)</Label>
                  <Input
                    id="duration"
                    type="number"
                    value={newExperiment.duration_hours}
                    onChange={(e) => setNewExperiment({ 
                      ...newExperiment, 
                      duration_hours: parseInt(e.target.value) 
                    })}
                  />
                </div>
                <div>
                  <Label htmlFor="minSamples">Min. Samples</Label>
                  <Input
                    id="minSamples"
                    type="number"
                    value={newExperiment.min_samples}
                    onChange={(e) => setNewExperiment({ 
                      ...newExperiment, 
                      min_samples: parseInt(e.target.value) 
                    })}
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                  Abbrechen
                </Button>
                <Button onClick={handleCreateExperiment}>
                  Experiment erstellen
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-red-500" />
            <span className="text-sm text-red-700">
              Fehler beim Laden der Experimente: {error}
            </span>
          </div>
        </div>
      )}

      {/* Experiments List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {experiments.map((experiment) => (
          <Card key={experiment.experiment_id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {getStatusIcon(experiment.status)}
                  <CardTitle className="text-lg">{experiment.name}</CardTitle>
                </div>
                <Badge variant={getStatusBadgeVariant(experiment.status)}>
                  {experiment.status}
                </Badge>
              </div>
              <CardDescription>
                {experiment.type.toUpperCase()} • {experiment.experiment_id}
              </CardDescription>
            </CardHeader>
            
            <CardContent className="space-y-4">
              {/* Experiment Details */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Startzeit:</span>
                  <span>
                    {experiment.start_time 
                      ? formatTimestamp(experiment.start_time)
                      : 'Nicht gestartet'
                    }
                  </span>
                </div>
                
                {experiment.end_time && (
                  <div className="flex justify-between text-sm">
                    <span>Endzeit:</span>
                    <span>{formatTimestamp(experiment.end_time)}</span>
                  </div>
                )}

                <div className="flex justify-between text-sm">
                  <span>Traffic Split:</span>
                  <div className="flex gap-2">
                    {Object.entries(experiment.traffic_split).map(([variant, split]) => (
                      <Badge key={variant} variant="outline">
                        {variant}: {(split * 100).toFixed(0)}%
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                {experiment.status === 'draft' && (
                  <Button 
                    size="sm" 
                    onClick={() => handleStartExperiment(experiment.experiment_id)}
                  >
                    <Play className="h-3 w-3 mr-1" />
                    Starten
                  </Button>
                )}
                
                {experiment.status === 'running' && (
                  <>
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => handleStopExperiment(experiment.experiment_id)}
                    >
                      <Pause className="h-3 w-3 mr-1" />
                      Stoppen
                    </Button>
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => handleEvaluateExperiment(experiment.experiment_id)}
                    >
                      <BarChart3 className="h-3 w-3 mr-1" />
                      Auswerten
                    </Button>
                  </>
                )}

                {experiment.status === 'stopped' && (
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => handleEvaluateExperiment(experiment.experiment_id)}
                  >
                    <BarChart3 className="h-3 w-3 mr-1" />
                    Auswerten
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Empty State */}
      {experiments.length === 0 && !loading && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Settings className="h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Keine Experimente vorhanden
            </h3>
            <p className="text-gray-500 text-center mb-4">
              Erstelle dein erstes Experiment, um mit der Autopilot-Optimierung zu beginnen.
            </p>
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Erstes Experiment erstellen
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
