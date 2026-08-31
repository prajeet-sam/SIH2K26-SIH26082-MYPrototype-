'use client'

import { Suspense, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Info } from 'lucide-react'
import { toView, useEnvQuery } from '@/lib/hooks'
import {
  getCurrentConditions,
  getExplanation,
  getForecast,
} from '@/lib/api'
import { SectionCard } from '@/components/common/SectionCard'
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton'
import { EmptyState } from '@/components/common/EmptyState'
import { ConfidencePill, ProvenanceChip } from '@/components/common/Chips'
import { TimeSeriesChart } from '@/components/charts/TimeSeriesChart'
import { HorizontalBars } from '@/components/charts/HorizontalBars'
import { istDateTime, istTime } from '@/lib/format'
import type { ForecastTarget } from '@/types/api'

const TARGETS: Array<{ id: ForecastTarget; label: string }> = [
  { id: 'aqi', label: 'AQI' },
  { id: 'pm25', label: 'PM2.5' },
  { id: 'pm10', label: 'PM10' },
]

const HORIZONS = [6, 24, 48] as const

const UNITS: Record<ForecastTarget, string> = {
  aqi: '',
  pm25: 'µg/m³',
  pm10: 'µg/m³',
}

function ForecastInner() {
  const searchParams = useSearchParams()
  const stationsQ = toView(useEnvQuery(['stations'], getCurrentConditions))
  const [slug, setSlug] = useState('anand-vihar')
  const [target, setTarget] = useState<ForecastTarget>('aqi')
  const [horizon, setHorizon] = useState<number>(24)

  useEffect(() => {
    const requested = searchParams.get('station')
    if (requested && stationsQ.data?.some((s) => s.slug === requested)) {
      setSlug(requested)
    }
  }, [searchParams, stationsQ.data])

  const forecastQ = toView(
    useEnvQuery(['forecast', slug, target, horizon], () => getForecast(slug, target, horizon)),
  )
  const explainQ = toView(
    useEnvQuery(['explain', slug, target, horizon], () => getExplanation(slug, target, horizon)),
  )

  const mainRows = useMemo(() => {
    const f = forecastQ.data
    if (!f) return []
    const step = horizon > 24 ? 2 : 1
    const observed = f.observedTail.map((o) => ({
      time: o.time,
      observed:
        target === 'aqi' ? o.aqi : o.pollutants[target] ?? null,
      p50: null as number | null,
      p10: null as number | null,
      p90: null as number | null,
    }))
    const future = f.points
      .filter((p) => p.horizonHours % step === 0 || p.horizonHours === 1)
      .map((p) => ({
        time: p.targetTime,
        observed: null as number | null,
        p50: p.p50,
        p10: p.p10,
        p90: p.p90,
      }))
    return [...observed, ...future]
  }, [forecastQ.data, target, horizon])

  const weatherRows = useMemo(() => {
    const f = forecastQ.data
    if (!f) return []
    const tail = f.weatherTail.map((w) => ({
      time: w.time,
      temperatureC: w.temperatureC,
      relativeHumidityPct: w.relativeHumidityPct,
      windSpeedMs: w.windSpeedMs,
      tTemp: null as number | null,
      tRh: null as number | null,
    }))
    const future = f.weatherForecast.map((w) => ({
      time: w.time,
      temperatureC: null,
      relativeHumidityPct: null,
      windSpeedMs: null,
      tTemp: w.temperatureC,
      tRh: w.relativeHumidityPct,
    }))
    return [...tail, ...future]
  }, [forecastQ.data])

  const stationName =
    stationsQ.data?.find((s) => s.slug === slug)?.name ?? slug

  return (
    <div className="space-y-4">
      <SectionCard
        title={`Forecast — ${stationName}`}
        subtitle={`Issued ${forecastQ.data ? istDateTime(forecastQ.data.issuedAt) : '–'} IST · run ${forecastQ.data?.modelRunId ?? '–'}`}
        actions={
          <>
            <ProvenanceChip source={forecastQ.source === 'demo' ? 'demo' : 'model-derived'} />
            {forecastQ.data && (
              <ConfidencePill level={forecastQ.data.points[horizon - 1]?.confidence ?? 'moderate'} />
            )}
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
          <div role="tablist" aria-label="Target" className="flex rounded-lg bg-slate-900 p-0.5 ring-1 ring-inset ring-slate-700">
            {TARGETS.map((t) => (
              <button
                key={t.id}
                role="tab"
                aria-selected={target === t.id}
                onClick={() => setTarget(t.id)}
                className={
                  target === t.id
                    ? 'rounded-md bg-emerald-500/15 px-3 py-1 text-xs font-semibold text-emerald-300'
                    : 'rounded-md px-3 py-1 text-xs text-slate-400 hover:text-slate-200'
                }
              >
                {t.label}
              </button>
            ))}
          </div>
          <div role="tablist" aria-label="Horizon" className="flex rounded-lg bg-slate-900 p-0.5 ring-1 ring-inset ring-slate-700">
            {HORIZONS.map((h) => (
              <button
                key={h}
                role="tab"
                aria-selected={horizon === h}
                onClick={() => setHorizon(h)}
                className={
                  horizon === h
                    ? 'rounded-md bg-emerald-500/15 px-3 py-1 text-xs font-semibold text-emerald-300'
                    : 'rounded-md px-3 py-1 text-xs text-slate-400 hover:text-slate-200'
                }
              >
                +{h} h
              </button>
            ))}
          </div>
        </div>

        {forecastQ.isLoading && <LoadingSkeleton rows={5} />}
        {forecastQ.isError && <EmptyState message="Forecast unavailable for this station." />}
        {mainRows.length > 0 && (
          <TimeSeriesChart
            data={mainRows}
            xKey="time"
            xTickFormatter={(t) => istTime(String(t))}
            band={{
              lowerKey: 'p10',
              upperKey: 'p90',
              label: 'P10–P90 interval',
              color: '#34d399',
            }}
            series={[
              { key: 'observed', label: `Observed ${target.toUpperCase()}`, color: '#38bdf8' },
              { key: 'p50', label: `Forecast ${target.toUpperCase()} (P50)`, color: '#34d399', dashed: true },
            ]}
            height={300}
          />
        )}
        <p className="text-[11px] leading-relaxed text-slate-500">
          Solid blue = observed · Dashed green = median forecast · Shaded green = P10–P90 prediction
          interval. Forecasts are probabilistic guidance, not guarantees.
          {UNITS[target] !== '' && ` Values in ${UNITS[target]}.`}
        </p>
      </SectionCard>

      <div className="grid gap-4 xl:grid-cols-3">
        <SectionCard
          title="Supporting weather"
          subtitle="Observed tail and forecast weather aligned on the same clock"
          className="xl:col-span-2"
        >
          {weatherRows.length > 0 ? (
            <TimeSeriesChart
              data={weatherRows}
              xKey="time"
              xTickFormatter={(t) => istTime(String(t))}
              rightUnit="%"
              series={[
                { key: 'temperatureC', label: 'Temp observed', color: '#fb923c' },
                { key: 'tTemp', label: 'Temp forecast', color: '#fb923c', dashed: true },
                { key: 'relativeHumidityPct', label: 'RH observed', color: '#7dd3fc', yAxis: 'right' },
                { key: 'tRh', label: 'RH forecast', color: '#7dd3fc', yAxis: 'right', dashed: true },
              ]}
            />
          ) : (
            <LoadingSkeleton rows={4} />
          )}
        </SectionCard>

        <SectionCard
          title="Why this forecast?"
          subtitle="Ranked model contributions"
          actions={<ProvenanceChip source={explainQ.source === 'live' ? 'model-derived' : 'demo'} />}
          bodyClassName="space-y-3"
        >
          {explainQ.isLoading && <LoadingSkeleton rows={5} />}
          {explainQ.isError && <EmptyState message="Explanation unavailable." />}
          {explainQ.data && (
            <>
              <HorizontalBars
                items={explainQ.data.contributions.map((c) => ({
                  label: c.featureLabel,
                  value: c.weightPct,
                  direction: c.direction,
                  suffix: '%',
                }))}
                max={Math.max(...explainQ.data.contributions.map((c) => c.weightPct))}
              />
              <p className="rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-2 text-xs leading-relaxed text-slate-300">
                {explainQ.data.narrative}
              </p>
              <p className="flex items-start gap-1.5 text-[11px] text-slate-500">
                <Info size={13} className="mt-0.5 shrink-0" />
                {explainQ.data.disclaimer}
              </p>
            </>
          )}
        </SectionCard>
      </div>
    </div>
  )
}

export default function ForecastPage() {
  return (
    <Suspense
      fallback={
        <div className="space-y-4">
          <LoadingSkeleton rows={8} />
          <LoadingSkeleton rows={8} />
        </div>
      }
    >
      <ForecastInner />
    </Suspense>
  )
}
