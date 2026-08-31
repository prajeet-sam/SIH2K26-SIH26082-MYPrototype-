'use client'

import { useMemo, useState } from 'react'
import { Download } from 'lucide-react'
import { toView, useEnvQuery } from '@/lib/hooks'
import { getCurrentConditions, getObservationHistory } from '@/lib/api'
import { SectionCard } from '@/components/common/SectionCard'
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton'
import { EmptyState } from '@/components/common/EmptyState'
import { ProvenanceChip } from '@/components/common/Chips'
import { TimeSeriesChart } from '@/components/charts/TimeSeriesChart'
import { downloadCsv } from '@/lib/csv'
import { istDateTime } from '@/lib/format'

const PRESETS = [
  { label: '24 h', hours: 24 },
  { label: '3 d', hours: 72 },
  { label: '7 d', hours: 168 },
  { label: '30 d', hours: 720 },
  { label: '90 d', hours: 2160 },
] as const

type Agg = 'hourly' | 'daily'

export default function HistoryPage() {
  const stationsQ = toView(useEnvQuery(['history-stations'], getCurrentConditions))
  const [slug, setSlug] = useState('anand-vihar')
  const [hours, setHours] = useState<number>(720)
  const [agg, setAgg] = useState<Agg>('daily')

  const obsQ = toView(
    useEnvQuery(['history-obs', slug, hours], () => getObservationHistory(slug, hours)),
  )

  const rows = useMemo(() => {
    const obs = obsQ.data ?? []
    if (agg === 'hourly') {
      return obs.map((o) => ({
        time: o.time,
        aqi: o.aqi,
        pm25: o.pollutants.pm25 ?? null,
        pm10: o.pollutants.pm10 ?? null,
        no2: o.pollutants.no2 ?? null,
        o3: o.pollutants.o3 ?? null,
      }))
    }
    const byDay = new Map<string, { sumAqi: number; n: number; sums: Record<string, number> }>()
    for (const o of obs) {
      const day = o.time.slice(0, 10)
      const entry = byDay.get(day) ?? { sumAqi: 0, n: 0, sums: {} }
      entry.sumAqi += Number.isFinite(o.aqi) ? o.aqi : 0
      entry.n += 1
      for (const key of ['pm25', 'pm10', 'no2', 'o3'] as const) {
        const v = o.pollutants[key]
        if (typeof v === 'number' && Number.isFinite(v)) {
          entry.sums[key] = (entry.sums[key] ?? 0) + v
        }
      }
      byDay.set(day, entry)
    }
    return Array.from(byDay.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([day, e]) => ({
        time: `${day}T00:00:00Z`,
        aqi: Math.round(e.sumAqi / Math.max(1, e.n)),
        pm25: roundOr((e.sums.pm25 ?? 0) / Math.max(1, e.n)),
        pm10: roundOr((e.sums.pm10 ?? 0) / Math.max(1, e.n)),
        no2: roundOr((e.sums.no2 ?? 0) / Math.max(1, e.n)),
        o3: roundOr((e.sums.o3 ?? 0) / Math.max(1, e.n)),
      }))
  }, [obsQ.data, agg])

  const exportRows = useMemo(
    () =>
      rows.map((r) => ({
        station_slug: slug,
        timestamp_utc: r.time,
        timestamp_ist: istDateTime(r.time),
        aqi: r.aqi,
        pm25_ugm3: r.pm25,
        pm10_ugm3: r.pm10,
        no2_ugm3: r.no2,
        o3_ugm3: r.o3,
      })),
    [rows, slug],
  )

  return (
    <div className="space-y-4">
      <SectionCard
        title="Historical explorer"
        subtitle="Long-range pollution patterns for a single station"
        actions={
          <>
            <ProvenanceChip source={obsQ.source === 'live' ? 'observed' : 'demo'} />
            <button
              onClick={() => downloadCsv(`airacast-history-${slug}-${agg}`, exportRows)}
              disabled={exportRows.length === 0}
              className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-500/15 px-2.5 py-1.5 text-xs font-medium text-emerald-300 ring-1 ring-inset ring-emerald-500/40 hover:bg-emerald-500/20 disabled:opacity-40"
            >
              <Download size={13} /> Export CSV
            </button>
          </>
        }
        bodyClassName="space-y-3"
      >
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          <label className="flex items-center gap-2 text-xs text-slate-400">
            Station
            <select
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
              aria-label="Station"
              className="max-w-[220px] rounded-lg border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-slate-200 focus:border-emerald-500 focus:outline-none"
            >
              {(stationsQ.data ?? []).map((s) => (
                <option key={s.slug} value={s.slug}>
                  {s.name}
                </option>
              ))}
            </select>
          </label>
          <div role="group" aria-label="Range" className="flex flex-wrap gap-1.5">
            {PRESETS.map((p) => (
              <button
                key={p.label}
                onClick={() => {
                  setHours(p.hours)
                  setAgg(p.hours > 168 ? 'daily' : 'hourly')
                }}
                className={
                  hours === p.hours
                    ? 'rounded-full bg-emerald-500/15 px-2.5 py-1 text-xs font-medium text-emerald-300 ring-1 ring-inset ring-emerald-500/40'
                    : 'rounded-full px-2.5 py-1 text-xs text-slate-400 ring-1 ring-inset ring-slate-700 hover:text-slate-200'
                }
              >
                {p.label}
              </button>
            ))}
          </div>
          <div role="tablist" aria-label="Aggregation" className="flex rounded-lg bg-slate-900 p-0.5 ring-1 ring-inset ring-slate-700">
            {(['hourly', 'daily'] as const).map((a) => (
              <button
                key={a}
                role="tab"
                aria-selected={agg === a}
                onClick={() => setAgg(a)}
                disabled={hours > 720 && a === 'hourly'}
                className={
                  agg === a
                    ? 'rounded-md bg-emerald-500/15 px-3 py-1 text-xs font-semibold text-emerald-300'
                    : 'rounded-md px-3 py-1 text-xs text-slate-400 hover:text-slate-200 disabled:opacity-30'
                }
              >
                {a === 'hourly' ? 'Hourly' : 'Daily means'}
              </button>
            ))}
          </div>
        </div>

        {obsQ.isLoading && <LoadingSkeleton rows={6} />}
        {obsQ.isError && <EmptyState message="History unavailable." />}
        {rows.length > 0 && (
          <TimeSeriesChart
            data={rows}
            xKey="time"
            xTickFormatter={(t) =>
              agg === 'daily' ? String(t).slice(0, 10) : istDateTime(String(t)).slice(0, 12)
            }
            series={[
              { key: 'aqi', label: 'AQI', color: '#34d399' },
              { key: 'pm25', label: 'PM2.5 µg/m³', color: '#38bdf8', yAxis: 'right' },
              { key: 'pm10', label: 'PM10 µg/m³', color: '#a78bfa', yAxis: 'right' },
              { key: 'no2', label: 'NO₂ µg/m³', color: '#fb923c', yAxis: 'right' },
            ]}
            height={320}
          />
        )}
      </SectionCard>
    </div>
  )
}

function roundOr(v: number): number | null {
  return Number.isFinite(v) && v > 0 ? Math.round(v * 10) / 10 : null
}
