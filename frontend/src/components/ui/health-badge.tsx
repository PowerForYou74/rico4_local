"use client"

import React from 'react'
import { Badge } from '@/components/ui/badge'
import { CheckCircle, XCircle, AlertCircle, Clock } from 'lucide-react'

interface HealthBadgeProps {
  status: 'healthy' | 'unhealthy' | 'warning' | 'loading'
  className?: string
}

export function HealthBadge({ status, className }: HealthBadgeProps) {
  const getStatusConfig = () => {
    switch (status) {
      case 'healthy':
        return {
          icon: <CheckCircle className="h-3 w-3" />,
          variant: 'default' as const,
          text: 'Healthy'
        }
      case 'unhealthy':
        return {
          icon: <XCircle className="h-3 w-3" />,
          variant: 'destructive' as const,
          text: 'Unhealthy'
        }
      case 'warning':
        return {
          icon: <AlertCircle className="h-3 w-3" />,
          variant: 'secondary' as const,
          text: 'Warning'
        }
      case 'loading':
        return {
          icon: <Clock className="h-3 w-3" />,
          variant: 'outline' as const,
          text: 'Loading'
        }
      default:
        return {
          icon: <AlertCircle className="h-3 w-3" />,
          variant: 'secondary' as const,
          text: 'Unknown'
        }
    }
  }

  const config = getStatusConfig()

  return (
    <Badge variant={config.variant} className={className}>
      {config.icon}
      <span className="ml-1">{config.text}</span>
    </Badge>
  )
}
