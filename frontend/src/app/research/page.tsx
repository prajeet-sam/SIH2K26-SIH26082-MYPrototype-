'use client'

import { useMemo, useState } from 'react'
import { useQueries } from '@tanstack/react-query'
import { Download } from 'lucide-react'
import { toView, useEnvQuery } from '@/lib/hooks'
import {
  getCorrelations,
  getCurrentConditions,
  getObservationHistory,
  getWeatherHistory,
} from '@/lib/api'
import { SectionCard } from '@/components/common/SectionCard'
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton'
import { EmptyState } from '@/components/common/EmptyState'
import { ProvenanceChip } from '@/components/common/Chips'
import { CorrelationHeatmap } from '@/components/charts/CorrelationHeatmap'
import { downloadCsv } from '@/lib/csv'
import type { ApiResult } from '@/lib/api'
import type { ObservationPoint, WeatherPoint } from '@/types/api'

const MAX_STATIONS = 6

export default function ResearchPage() {
  const stationsQ = toView(useEnvQuery(['research-stations'], getCurrentConditions))
  const [selected, setSelected] = useState<string[]>(['anand-vihar'])
  const [days, setDays] = useState<number>(30)
  const [corrSlug, setCorrSlug] = useState('anand-vihar')

  const corrQ = toView(
    useEnvQuery(['research-corr', corrSlug, days], () => getCorrelations(corrSlug, days)),
  )

  const results = useQueries({
    queries: selected.flatMap((slug) => [
      {
        queryKey: ['research-obs', slug],
        queryFn: () => getObservationHistory(slug, days * 24),
        staleTime: 60_000,
      },
      {
        queryKey: ['research-weather', slug],
        queryFn: () => getWeatherHistory(slug, days * 24),
        staleTime: 60_000,
      },
    ]),
  })

  const obsResults = results.filter((_, i) => i % 2 === 0)
  const weatherResults = results.filter((_, i) => i % 2 === 1)

  const exportReady = useMemo(
    () =>
      obsResults.every((r) => r.data !== undefined) &&
      weatherResults.every((r) => r.data !== undefined),
    [obsResults, weatherResults],
  )

  const buildExportRows = (): Record<string, unknown>[] => {
    if (!exportReady) return []
    const rows: Record<string, unknown>[] = []
    selected.forEach((slug, idx) => {
      const obs = (obsResults[idx].data as ApiResult<ObservationPoint[]> | undefined)?.data ?? []
      const weather =
        (weatherResults[idx].data as ApiResult<WeatherPoint[]> | undefined)?.data ?? []
      const weatherByHour = new Map(weather.map((w) => [w.time.slice(0, 13), w]))
      for (const o of obs) {
        const w = weatherByHour.get(o.time.slice(0, 13))
        rows.push({
          station_slug: slug,
          timestamp_utc: o.time,
          aqi: o.aqi,
          quality_flag: o.qualityFlag,
          pm25_ugm3: o.pollutants.pm25 ?? '',
          pm10_ugm3: o.pollutants.pm10 ?? '',
          no2_ugm3: o.pollutants.no2 ?? '',
          so2_ugm3: o.pollutants.so2 ?? '',
          co_mgm3: o.pollutants.co ?? '',
          o3_ugm3: o.pollutants.o3 ?? '',
          temperature_c: w?.temperatureC ?? '',
          relative_humidity_pct: w?.relativeHumidityPct ?? '',
          wind_speed_ms: w?.windSpeedMs ?? '',
          wind_direction_deg: w?.windDirectionDeg ?? '',
          precipitation_mm: w?.precipitationMm ?? '',
          pressure_hpa: w?.pressureHpa ?? '',
          provenance: o.qualityFlag === 'interpolated' ? 'interpolated' : 'demo',
        })
      }
    })
    return rows
  }

  const toggleStation = (slug: string) => {
    setSelected((prev) => {
      if (prev.includes(slug)) {
        const next = prev.filter((s) => s !== slug)
        setCorrSlug((cur) => (cur === slug ? (next[0] ?? '') : cur))
        return next
      }
      if (prev.length >= MAX_STATIONS) return prev
      return [...prev, slug]
    })
  }

  return (
    <div className="space-y-4">
      <SectionCard
        title="Research workspace"
        subtitle={`Select up to ${MAX_STATIONS} stations · trailing window · CSV export includes provenance flags`}
        actions={<ProvenanceChip source={stationsQ.source} />}
        bodyClassName="space-y-4"
      >
        <div className="flex flex-wrap items-center gap-1.5">
          {(stationsQ.data ?? []).map((s) => {
            const active = selected.includes(s.slug)
            return (
              <button
                key={s.slug}
                onClick={() => toggleStation(s.slug)}
                className={
                  active
                    ? 'rounded-full bg-emerald-500/15 px-3 py-1 text-xs font-medium text-emerald-300 ring-1 ring-inset ring-emerald-500/40'
                    : 'rounded-full px-3 py-1 text-xs text-slate-400 ring-1 ring-inset ring-slate-700 hover:text-slate-200'
                }
                aria-pressed={active}
              >
                {s.name}
              </button>
            )
          })}
        </div>

        <label className="flex w-fit items-center gap-2 text-xs text-slate-400">
          Window
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            aria-label="Window length in days"
            className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs text-slate-200 focus:border-emerald-500 focus:outline-none"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
        </label>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => downloadCsv(`airacast-research-${days}d`, buildExportRows())}
            disabled={!exportReady || selected.length === 0}
            className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-500/15 px-3 py-2 text-xs font-medium text-emerald-300 ring-1 ring-inset ring-emerald-500/40 hover:bg-emerald-500/20 disabled:opacity-40"
          >
            <Download size={13} /> Export joined dataset ({selected.length} station
            {selected.length === 1 ? '' : 's'})
          </button>
          <span className="text-[11px] text-slate-500">
            Columns include pollutant concentrations, weather variables and per-row quality flags.
          </span>
        </div>
      </SectionCard>

      <SectionCard
        title="Correlation explorer"
        subtitle="Weather × pollutant Pearson correlations over the selected window"
        actions={<ProvenanceChip source={corrQ.source === 'live' ? 'observed' : 'demo'} />}
        bodyClassName="space-y-3"
      >
        <label className="flex w-fit items-center gap-2 text-xs text-slate-400">
          Station for matrix
          <select
            value={corrSlug}
            onChange={(e) => setCorrSlug(e.target.value)}
            aria-label="Correlation station"
            className="max-w-[220px] rounded-lg border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-slate-200 focus:border-emerald-500 focus:outline-none disabled:opacity-50"
            disabled={selected.length === 0}
          >
            {selected.map((slug) => (
              <option key={slug} value={slug}>
                {stationsQ.data?.find((s) => s.slug === slug)?.name ?? slug}
              </option>
            ))}
          </select>
        </label>
        {corrQ.isLoading && <LoadingSkeleton rows={6} />}
        {corrQ.isError && <EmptyState message="Correlation data unavailable." />}
        {corrQ.data && <CorrelationHeatmap {...corrQ.data} />}
      </SectionCard>

      <SectionCard title="Selected stations" subtitle="Snapshot of current conditions">
        {selected.length === 0 ? (
          <EmptyState message="Select at least one station above." />
        ) : (
          <ResearchTable slugs={selected} />
        )}
      </SectionCard>
    </div>
  )
}

function ResearchTable({ slugs }: { slugs: string[] }) {
  const stationsQ = toView(useEnvQuery(['research-stations'], getCurrentConditions))
  const rows = useMemo(
    () => (stationsQ.data ?? []).filter((s) => slugs.includes(s.slug)),
    [stationsQ.data, slugs],
  )
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] text-sm">
        <thead>
          <tr className="border-b border-slate-800 text-left text-[11px] uppercase tracking-wider text-slate-500">
            <th className="py-2 pr-3">Station</th>
            <th className="py-2 pr-3">City</th>
            <th className="py-2 pr-3">AQI</th>
            <th className="py-2 pr-3">PM2.5</th>
            <th className="py-2 pr-3">Wind m/s</th>
            <th className="py-2 pr-3">RH %</th>
            <th className="py-2 pr-3">Temp °C</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((s) => (
            <tr key={s.slug} className="border-b border-slate-800/60">
              <td className="py-2 pr-3 font-medium text-slate-200">{s.name}</td>
              <td className="py-2 pr-3 text-xs text-slate-400">{s.city}</td>
              <td className="py-2 pr-3 font-mono text-xs">{Math.round(s.aqi)}</td>
              <td className="py-2 pr-3 font-mono text-xs">{s.pollutants.pm25 ?? '–'}</td>
              <td className="py-2 pr-3 font-mono text-xs">{s.weather.windSpeedMs ?? '–'}</td>
              <td className="py-2 pr-3 font-mono text-xs">{s.weather.relativeHumidityPct ?? '–'}</td>
              <td className="py-2 pr-3 font-mono text-xs">{s.weather.temperatureC ?? '–'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
