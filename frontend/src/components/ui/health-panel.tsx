'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './card'
import { Badge } from './badge'
import { Skeleton } from './skeleton'
import { CheckCircle, XCircle, AlertCircle, Clock } from 'lucide-react'

interface HealthStatus {
  provider: string
  model: string
  status: string
  latency_ms: number
  error?: string
}

interface SystemHealth {
  status: string
  latency_ms: number
  model: string
  env_source: string
  providers: HealthStatus[]
  timestamp: string
}

interface HealthPanelProps {
  health: SystemHealth | null
  isLoading: boolean
}

export function HealthPanel({ health, isLoading }: HealthPanelProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>System Health</CardTitle>
          <CardDescription>Checking system status...</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center space-x-4">
            <Skeleton className="h-4 w-4 rounded-full" />
            <Skeleton className="h-4 w-32" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-4 w-16" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!health) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>System Health</CardTitle>
          <CardDescription>Unable to load system status</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-2 text-destructive">
            <XCircle className="h-4 w-4" />
            <span>Failed to load health data</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'unhealthy':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'unknown':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-500" />
    }
  }

  const getStatusColor = (status: string) => {
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

  const getOverallStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'health-healthy'
      case 'unhealthy':
        return 'health-unhealthy'
      case 'no_providers':
        return 'health-unknown'
      default:
        return 'health-unknown'
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>System Health</CardTitle>
            <CardDescription>
              Provider status and system performance
            </CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <Badge 
              variant="outline" 
              className={`health-indicator ${getOverallStatusColor(health.status)}`}
            >
              {health.status}
            </Badge>
            <span className="text-sm text-muted-foreground">
              {health.latency_ms.toFixed(0)}ms
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Overall Status */}
          <div className="flex items-center space-x-4 p-4 border border-border rounded-lg">
            {getStatusIcon(health.status)}
            <div className="flex-1">
              <div className="flex items-center space-x-2">
                <span className="font-medium">Overall Status</span>
                <Badge 
                  variant="outline" 
                  className={`health-indicator ${getOverallStatusColor(health.status)}`}
                >
                  {health.status}
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground">
                Model: {health.model} | Environment: {health.env_source}
              </p>
            </div>
            <div className="text-right">
              <div className="text-sm font-medium">{health.latency_ms.toFixed(0)}ms</div>
              <div className="text-xs text-muted-foreground">Response Time</div>
            </div>
          </div>

          {/* Provider Status */}
          {health.providers.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-sm font-medium">Provider Status</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {health.providers.map((provider, index) => (
                  <div key={index} className="flex items-center space-x-3 p-3 border border-border rounded-lg">
                    {getStatusIcon(provider.status)}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium capitalize">{provider.provider}</span>
                        <Badge 
                          variant="outline" 
                          className={`health-indicator ${getStatusColor(provider.status)}`}
                        >
                          {provider.status}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground truncate">
                        {provider.model}
                      </p>
                      {provider.error && (
                        <p className="text-xs text-destructive truncate">
                          {provider.error}
                        </p>
                      )}
                    </div>
                    <div className="text-right">
                      <div className="text-xs font-medium">{provider.latency_ms.toFixed(0)}ms</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* No Providers */}
          {health.providers.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              <AlertCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No providers configured</p>
              <p className="text-sm">Configure API keys to enable providers</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
