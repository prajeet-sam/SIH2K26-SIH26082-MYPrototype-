import clsx from 'clsx'
import type { ReactNode } from 'react'
import { Sparkline } from '@/components/charts/Sparkline'

interface KpiCardProps {
  title: string
  value: ReactNode
  sub?: ReactNode
  badge?: ReactNode
  trend?: number[]
  icon?: ReactNode
  iconClassName?: string
  className?: string
}

export function KpiCard({
  title,
  value,
  sub,
  badge,
  trend,
  icon,
  iconClassName,
  className,
}: KpiCardProps) {
  return (
    <div
      className={clsx(
        'group flex min-w-0 flex-col justify-between rounded-2xl border border-slate-800/80 bg-slate-900/50 px-4 py-4 shadow-card backdrop-blur transition-all duration-200 hover:border-emerald-500/30 hover:shadow-card-hover',
        className,
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <span className="flex items-center gap-2 truncate text-xs font-medium uppercase tracking-wider text-slate-500">
          {icon && (
            <span
              className={clsx(
                'flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-slate-800/70 text-slate-300 transition-colors group-hover:bg-emerald-500/15 group-hover:text-emerald-300',
                iconClassName,
              )}
            >
              {icon}
            </span>
          )}
          <span className="truncate">{title}</span>
        </span>
        {badge}
      </div>
      <div className="mt-3 flex items-end justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate font-mono text-2xl font-semibold tracking-tight text-slate-50">
            {value}
          </div>
          {sub && <div className="mt-0.5 truncate text-xs text-slate-500">{sub}</div>}
        </div>
        {trend && trend.length > 1 && (
          <div className="w-24 shrink-0">
            <Sparkline data={trend} />
          </div>
        )}
      </div>
    </div>
  )
}
