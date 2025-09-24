interface StatusDotProps {
  status: 'ok' | 'warning' | 'error' | 'unknown'
  size?: 'sm' | 'md' | 'lg'
}

export function StatusDot({ status, size = 'md' }: StatusDotProps) {
  const sizeClasses = {
    sm: 'h-2 w-2',
    md: 'h-3 w-3',
    lg: 'h-4 w-4'
  }

  const colorClasses = {
    ok: 'bg-green-500',
    warning: 'bg-yellow-500',
    error: 'bg-red-500',
    unknown: 'bg-gray-400'
  }

  return (
    <div className={`rounded-full ${sizeClasses[size]} ${colorClasses[status]}`} />
  )
}
