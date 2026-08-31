import clsx from 'clsx'
import type { AlertItem } from '@/types/api'
import type { ConfidenceLevel } from '@/types/api'

export function SeverityChip({ severity }: { severity: AlertItem['severity'] }) {
  const styles: Record<AlertItem['severity'], string> = {
    info: 'bg-sky-500/15 text-sky-300 ring-sky-500/40',
    warning: 'bg-orange-500/15 text-orange-300 ring-orange-500/40',
    critical: 'bg-red-500/15 text-red-300 ring-red-500/40',
  }
  return (
    <span
      className={clsx(
        'rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider ring-1 ring-inset',
        styles[severity],
      )}
    >
      {severity}
    </span>
  )
}

const CONFIDENCE_LABELS: Record<ConfidenceLevel, string> = {
  high: 'High confidence',
  moderate: 'Moderate confidence',
  low: 'Low confidence',
}

const CONFIDENCE_STYLES: Record<ConfidenceLevel, string> = {
  high: 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/40',
  moderate: 'bg-amber-500/15 text-amber-300 ring-amber-500/40',
  low: 'bg-slate-500/15 text-slate-300 ring-slate-500/40',
}

export function ConfidencePill({ level }: { level: ConfidenceLevel }) {
  return (
    <span
      className={clsx(
        'rounded-full px-2 py-0.5 text-[11px] font-semibold ring-1 ring-inset',
        CONFIDENCE_STYLES[level],
      )}
      title="Derived from recent validation error at this horizon and input data freshness"
    >
      {CONFIDENCE_LABELS[level]}
    </span>
  )
}

export function ProvenanceChip({
  source,
}: {
  source: 'live' | 'demo' | 'observed' | 'forecast' | 'interpolated' | 'model-derived' | null
}) {
  if (!source) return null
  const map = {
    live: ['Live API', 'bg-emerald-500/10 text-emerald-300'],
    demo: ['Demo', 'bg-amber-500/10 text-amber-300'],
    observed: ['Observed', 'bg-sky-500/10 text-sky-300'],
    forecast: ['Forecast', 'bg-violet-500/10 text-violet-300'],
    interpolated: ['Interpolated (estimated)', 'bg-cyan-500/10 text-cyan-300'],
    'model-derived': ['Model-derived', 'bg-fuchsia-500/10 text-fuchsia-300'],
  } as const
  const [label, styles] = map[source]
  return (
    <span className={clsx('rounded-full px-2 py-0.5 text-[11px] font-medium', styles)}>
      {label}
    </span>
  )
}
