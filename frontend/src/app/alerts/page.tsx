'use client'

import { useMemo, useState } from 'react'
import clsx from 'clsx'
import { ArrowDownRight, ArrowUpRight, BellOff } from 'lucide-react'
import { toView, useEnvQuery } from '@/lib/hooks'
import { getAlerts } from '@/lib/api'
import { SectionCard } from '@/components/common/SectionCard'
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton'
import { EmptyState } from '@/components/common/EmptyState'
import { ProvenanceChip, SeverityChip } from '@/components/common/Chips'
import { istDateTime } from '@/lib/format'
import type { AlertItem } from '@/types/api'

const TYPE_LABELS: Record<AlertItem['alertType'], string> = {
  'threshold-crossing': 'Threshold crossing',
  'rapid-rise': 'Rapid rise',
  'extreme-forecast': 'Extreme forecast',
  'stagnation-advisory': 'Stagnation advisory',
  'data-outage': 'Data outage',
  'forecast-deterioration': 'Forecast deterioration',
}

type StatusFilter = 'active' | 'resolved' | 'all'
type SeverityFilter = AlertItem['severity'] | 'all'

export default function AlertsPage() {
  const alertsQ = toView(useEnvQuery(['alerts'], getAlerts))
  const [status, setStatus] = useState<StatusFilter>('active')
  const [severity, setSeverity] = useState<SeverityFilter>('all')

  const filtered = useMemo(() => {
    let list = alertsQ.data ?? []
    if (status === 'active') list = list.filter((a) => a.resolvedAt === null)
    if (status === 'resolved') list = list.filter((a) => a.resolvedAt !== null)
    if (severity !== 'all') list = list.filter((a) => a.severity === severity)
    return [...list].sort((a, b) => b.triggeredAt.localeCompare(a.triggeredAt))
  }, [alertsQ.data, status, severity])

  return (
    <div className="space-y-4">
      <SectionCard
        title="Alert feed"
        subtitle="Rule-based detections on observed and forecast series · configurable thresholds arrive with the backend rules API"
        actions={<ProvenanceChip source={alertsQ.source} />}
        bodyClassName="space-y-3"
      >
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          <div role="tablist" aria-label="Status" className="flex rounded-lg bg-slate-900 p-0.5 ring-1 ring-inset ring-slate-700">
            {(['active', 'resolved', 'all'] as const).map((s) => (
              <button
                key={s}
                role="tab"
                aria-selected={status === s}
                onClick={() => setStatus(s)}
                className={
                  status === s
                    ? 'rounded-md bg-emerald-500/15 px-3 py-1 text-xs font-semibold capitalize text-emerald-300'
                    : 'rounded-md px-3 py-1 text-xs capitalize text-slate-400 hover:text-slate-200'
                }
              >
                {s}
              </button>
            ))}
          </div>
          <div role="group" aria-label="Severity" className="flex gap-1.5">
            {(['all', 'critical', 'warning', 'info'] as const).map((sv) => (
              <button
                key={sv}
                onClick={() => setSeverity(sv)}
                className={clsx(
                  severity === sv
                    ? 'rounded-full bg-slate-800 px-3 py-1 text-xs font-medium text-slate-200 ring-1 ring-inset ring-slate-600'
                    : 'rounded-full px-3 py-1 text-xs text-slate-400 ring-1 ring-inset ring-slate-700 hover:text-slate-200',
                )}
              >
                {sv}
              </button>
            ))}
          </div>
        </div>

        {alertsQ.isLoading && <LoadingSkeleton rows={5} />}
        {alertsQ.isError && <EmptyState message="Alert service unavailable." />}
        {!alertsQ.isLoading && filtered.length === 0 && (
          <EmptyState message="No alerts match the current filters." />
        )}

        <ul className="grid gap-3 lg:grid-cols-2">
          {filtered.map((a) => (
            <li
              key={a.id}
              className={clsx(
                'rounded-xl border bg-slate-950/40 p-4',
                a.resolvedAt !== null ? 'border-slate-800/60 opacity-70' : 'border-slate-800',
              )}
            >
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <SeverityChip severity={a.severity} />
                <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400">
                  {TYPE_LABELS[a.alertType]}
                </span>
                <span
                  className={clsx(
                    'rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider',
                    a.observedOrForecast === 'forecast'
                      ? 'bg-violet-500/10 text-violet-300'
                      : 'bg-sky-500/10 text-sky-300',
                  )}
                >
                  {a.observedOrForecast}
                </span>
                {a.resolvedAt !== null && (
                  <span className="ml-auto flex items-center gap-1 text-[11px] text-slate-500">
                    <BellOff size={12} /> resolved
                  </span>
                )}
              </div>
              <p className="text-sm leading-relaxed text-slate-200">{a.message}</p>
              <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-slate-500">
                <span>{a.stationName ?? `${a.city ?? 'NCR'} region`}</span>
                <span>{istDateTime(a.triggeredAt)} IST</span>
                {a.context.horizonHours !== null && <span>+{a.context.horizonHours} h horizon</span>}
                {a.context.value !== null && (
                  <span className="font-mono">
                    value {a.context.value}
                    {a.context.threshold !== null ? ` vs threshold ${a.context.threshold}` : ''}
                  </span>
                )}
              </div>
              {a.context.contributors.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {a.context.contributors.map((c) => (
                    <span
                      key={c.label}
                      className={clsx(
                        'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px]',
                        c.direction === 'up'
                          ? 'bg-red-500/10 text-red-300'
                          : 'bg-emerald-500/10 text-emerald-300',
                      )}
                    >
                      {c.direction === 'up' ? <ArrowUpRight size={11} /> : <ArrowDownRight size={11} />}
                      {c.label}
                    </span>
                  ))}
                </div>
              )}
            </li>
          ))}
        </ul>
      </SectionCard>
    </div>
  )
}
