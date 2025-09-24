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
  FileText, 
  Plus, 
  Edit, 
  RotateCcw, 
  ArrowUp, 
  ArrowDown,
  Eye,
  Copy,
  CheckCircle,
  Clock,
  AlertCircle
} from 'lucide-react';
import { useAutopilotStore } from '@/store/autopilot-store';
import { formatTimestamp, getStatusBadgeVariant } from '@/lib/autopilot-api';

export default function PromptsTab() {
  const { 
    prompts, 
    policies,
    loading, 
    error, 
    fetchPrompts,
    fetchPolicies,
    proposeChanges,
    applyChanges,
    rollbackChanges
  } = useAutopilotStore();

  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showPolicyDialog, setShowPolicyDialog] = useState(false);
  const [selectedPrompt, setSelectedPrompt] = useState<string | null>(null);
  const [newPrompt, setNewPrompt] = useState({
    name: '',
    content: '',
    role: 'system',
    description: '',
    tags: ''
  });
  const [newPolicy, setNewPolicy] = useState({
    name: '',
    description: '',
    weights: { openai: 0.6, claude: 0.4 },
    conditions: { max_latency_ms: 10000 }
  });

  useEffect(() => {
    fetchPrompts();
    fetchPolicies();
  }, [fetchPrompts, fetchPolicies]);

  const handleCreatePrompt = async () => {
    try {
      const promptVariants = [{
        id: `prompt_${Date.now()}`,
        name: newPrompt.name,
        content: newPrompt.content,
        role: newPrompt.role,
        tags: newPrompt.tags.split(',').map(t => t.trim()).filter(Boolean)
      }];
      
      await proposeChanges(promptVariants);
      setShowCreateDialog(false);
      setNewPrompt({
        name: '',
        content: '',
        role: 'system',
        description: '',
        tags: ''
      });
    } catch (error) {
      console.error('Error creating prompt:', error);
    }
  };

  const handleCreatePolicy = async () => {
    try {
      const routingPolicies = [{
        id: `policy_${Date.now()}`,
        name: newPolicy.name,
        weights: newPolicy.weights,
        conditions: newPolicy.conditions
      }];
      
      await proposeChanges(undefined, routingPolicies);
      setShowPolicyDialog(false);
      setNewPolicy({
        name: '',
        description: '',
        weights: { openai: 0.6, claude: 0.4 },
        conditions: { max_latency_ms: 10000 }
      });
    } catch (error) {
      console.error('Error creating policy:', error);
    }
  };

  const handleApplyPrompt = async (promptId: string) => {
    try {
      await applyChanges([promptId]);
    } catch (error) {
      console.error('Error applying prompt:', error);
    }
  };

  const handleApplyPolicy = async (policyId: string) => {
    try {
      await applyChanges(undefined, [policyId]);
    } catch (error) {
      console.error('Error applying policy:', error);
    }
  };

  const handleRollbackPrompt = async (promptId: string) => {
    try {
      await rollbackChanges([promptId]);
    } catch (error) {
      console.error('Error rolling back prompt:', error);
    }
  };

  const handleRollbackPolicy = async (policyId: string) => {
    try {
      await rollbackChanges(undefined, [policyId]);
    } catch (error) {
      console.error('Error rolling back policy:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'candidate':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'deprecated':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <FileText className="h-4 w-4 text-gray-500" />;
    }
  };

  if (loading && prompts.length === 0) {
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
          <h2 className="text-2xl font-bold">Prompts & Policies</h2>
          <p className="text-gray-600">
            Prompt-Versionen und Routing-Policies verwalten
          </p>
        </div>
        
        <div className="flex gap-2">
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Neuer Prompt
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Neuen Prompt erstellen</DialogTitle>
                <DialogDescription>
                  Erstelle einen neuen Prompt für die Autopilot-Optimierung.
                </DialogDescription>
              </DialogHeader>
              
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="promptName">Name</Label>
                    <Input
                      id="promptName"
                      value={newPrompt.name}
                      onChange={(e) => setNewPrompt({ ...newPrompt, name: e.target.value })}
                      placeholder="Prompt Name"
                    />
                  </div>
                  <div>
                    <Label htmlFor="promptRole">Rolle</Label>
                    <select
                      id="promptRole"
                      value={newPrompt.role}
                      onChange={(e) => setNewPrompt({ ...newPrompt, role: e.target.value })}
                      className="w-full p-2 border rounded-md"
                    >
                      <option value="system">System</option>
                      <option value="user">User</option>
                      <option value="assistant">Assistant</option>
                    </select>
                  </div>
                </div>

                <div>
                  <Label htmlFor="promptDescription">Beschreibung</Label>
                  <Input
                    id="promptDescription"
                    value={newPrompt.description}
                    onChange={(e) => setNewPrompt({ ...newPrompt, description: e.target.value })}
                    placeholder="Prompt Beschreibung"
                  />
                </div>

                <div>
                  <Label htmlFor="promptContent">Inhalt</Label>
                  <Textarea
                    id="promptContent"
                    value={newPrompt.content}
                    onChange={(e) => setNewPrompt({ ...newPrompt, content: e.target.value })}
                    placeholder="Prompt Inhalt..."
                    rows={8}
                  />
                </div>

                <div>
                  <Label htmlFor="promptTags">Tags (kommagetrennt)</Label>
                  <Input
                    id="promptTags"
                    value={newPrompt.tags}
                    onChange={(e) => setNewPrompt({ ...newPrompt, tags: e.target.value })}
                    placeholder="tag1, tag2, tag3"
                  />
                </div>

                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                    Abbrechen
                  </Button>
                  <Button onClick={handleCreatePrompt}>
                    Prompt erstellen
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>

          <Dialog open={showPolicyDialog} onOpenChange={setShowPolicyDialog}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Plus className="h-4 w-4 mr-2" />
                Neue Policy
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Neue Policy erstellen</DialogTitle>
                <DialogDescription>
                  Erstelle eine neue Routing-Policy für die Autopilot-Optimierung.
                </DialogDescription>
              </DialogHeader>
              
              <div className="space-y-4">
                <div>
                  <Label htmlFor="policyName">Name</Label>
                  <Input
                    id="policyName"
                    value={newPolicy.name}
                    onChange={(e) => setNewPolicy({ ...newPolicy, name: e.target.value })}
                    placeholder="Policy Name"
                  />
                </div>

                  <div>
                    <Label htmlFor="policyDescription">Beschreibung</Label>
                    <Input
                      id="policyDescription"
                      value={newPolicy.description}
                      onChange={(e) => setNewPolicy({ ...newPolicy, description: e.target.value })}
                      placeholder="Policy Beschreibung"
                    />
                  </div>

                  <div>
                    <Label>Provider-Gewichtungen</Label>
                    <div className="grid grid-cols-3 gap-4 mt-2">
                      <div>
                        <Label htmlFor="openaiWeight">OpenAI</Label>
                        <Input
                          id="openaiWeight"
                          type="number"
                          step="0.1"
                          min="0"
                          max="1"
                          value={newPolicy.weights.openai}
                          onChange={(e) => setNewPolicy({ 
                            ...newPolicy, 
                            weights: { ...newPolicy.weights, openai: parseFloat(e.target.value) }
                          })}
                        />
                      </div>
                      <div>
                        <Label htmlFor="claudeWeight">Claude</Label>
                        <Input
                          id="claudeWeight"
                          type="number"
                          step="0.1"
                          min="0"
                          max="1"
                          value={newPolicy.weights.claude}
                          onChange={(e) => setNewPolicy({ 
                            ...newPolicy, 
                            weights: { ...newPolicy.weights, claude: parseFloat(e.target.value) }
                          })}
                        />
                      </div>
                      <div>
                        <Label htmlFor="perplexityWeight">Perplexity</Label>
                        <Input
                          id="perplexityWeight"
                          type="number"
                          step="0.1"
                          min="0"
                          max="1"
                          value={1 - newPolicy.weights.openai - newPolicy.weights.claude}
                          disabled
                        />
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-end gap-2">
                    <Button variant="outline" onClick={() => setShowPolicyDialog(false)}>
                      Abbrechen
                    </Button>
                    <Button onClick={handleCreatePolicy}>
                      Policy erstellen
                    </Button>
                  </div>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-red-500" />
            <span className="text-sm text-red-700">
              Fehler beim Laden der Prompts: {error}
            </span>
          </div>
        </div>
      )}

      {/* Prompts Section */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Prompts
        </h3>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {prompts.map((prompt) => (
            <Card key={prompt.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(prompt.status)}
                    <CardTitle className="text-lg">{prompt.name}</CardTitle>
                  </div>
                  <Badge variant={getStatusBadgeVariant(prompt.status)}>
                    {prompt.status}
                  </Badge>
                </div>
                <CardDescription>
                  {prompt.description} • v{prompt.current_version}
                </CardDescription>
              </CardHeader>
              
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Erstellt:</span>
                    <span>{formatTimestamp(prompt.created_at)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Aktualisiert:</span>
                    <span>{formatTimestamp(prompt.updated_at)}</span>
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => setSelectedPrompt(prompt.id)}
                  >
                    <Eye className="h-3 w-3 mr-1" />
                    Anzeigen
                  </Button>
                  
                  {prompt.status === 'candidate' && (
                    <Button 
                      size="sm"
                      onClick={() => handleApplyPrompt(prompt.id)}
                    >
                      <ArrowUp className="h-3 w-3 mr-1" />
                      Aktivieren
                    </Button>
                  )}
                  
                  {prompt.status === 'active' && (
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => handleRollbackPrompt(prompt.id)}
                    >
                      <RotateCcw className="h-3 w-3 mr-1" />
                      Rollback
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Policies Section */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Settings className="h-5 w-5" />
          Policies
        </h3>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {policies.map((policy) => (
            <Card key={policy.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(policy.status)}
                    <CardTitle className="text-lg">{policy.name}</CardTitle>
                  </div>
                  <Badge variant={getStatusBadgeVariant(policy.status)}>
                    {policy.status}
                  </Badge>
                </div>
                <CardDescription>
                  {policy.description} • {policy.policy_type} • v{policy.current_version}
                </CardDescription>
              </CardHeader>
              
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Erstellt:</span>
                    <span>{formatTimestamp(policy.created_at)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Aktualisiert:</span>
                    <span>{formatTimestamp(policy.updated_at)}</span>
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => setSelectedPrompt(policy.id)}
                  >
                    <Eye className="h-3 w-3 mr-1" />
                    Anzeigen
                  </Button>
                  
                  {policy.status === 'candidate' && (
                    <Button 
                      size="sm"
                      onClick={() => handleApplyPolicy(policy.id)}
                    >
                      <ArrowUp className="h-3 w-3 mr-1" />
                      Aktivieren
                    </Button>
                  )}
                  
                  {policy.status === 'active' && (
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => handleRollbackPolicy(policy.id)}
                    >
                      <RotateCcw className="h-3 w-3 mr-1" />
                      Rollback
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Empty States */}
      {prompts.length === 0 && policies.length === 0 && !loading && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <FileText className="h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Keine Prompts oder Policies vorhanden
            </h3>
            <p className="text-gray-500 text-center mb-4">
              Erstelle deinen ersten Prompt oder deine erste Policy, um mit der Autopilot-Optimierung zu beginnen.
            </p>
            <div className="flex gap-2">
              <Button onClick={() => setShowCreateDialog(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Ersten Prompt erstellen
              </Button>
              <Button variant="outline" onClick={() => setShowPolicyDialog(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Erste Policy erstellen
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
