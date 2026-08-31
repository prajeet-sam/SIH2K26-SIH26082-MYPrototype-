'use client'

import { useMemo, useState } from 'react'
import { toView, useEnvQuery } from '@/lib/hooks'
import {
  getCurrentConditions,
  getCorrelations,
  getObservationHistory,
  getWeatherHistory,
} from '@/lib/api'
import { SectionCard } from '@/components/common/SectionCard'
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton'
import { EmptyState } from '@/components/common/EmptyState'
import { ProvenanceChip } from '@/components/common/Chips'
import { ScatterPlot } from '@/components/charts/ScatterPlot'
import { CorrelationHeatmap } from '@/components/charts/CorrelationHeatmap'
import { TimeSeriesChart } from '@/components/charts/TimeSeriesChart'
import { istDayLabel } from '@/lib/format'

type Field =
  | 'pm25'
  | 'pm10'
  | 'no2'
  | 'o3'
  | 'windSpeedMs'
  | 'relativeHumidityPct'
  | 'temperatureC'
  | 'precipitationMm'

const FIELDS: Array<{ id: Field; label: string; unit: string }> = [
  { id: 'pm25', label: 'PM2.5', unit: 'µg/m³' },
  { id: 'pm10', label: 'PM10', unit: 'µg/m³' },
  { id: 'no2', label: 'NO₂', unit: 'µg/m³' },
  { id: 'o3', label: 'O₃', unit: 'µg/m³' },
  { id: 'windSpeedMs', label: 'Wind speed', unit: 'm/s' },
  { id: 'relativeHumidityPct', label: 'Humidity', unit: '%' },
  { id: 'temperatureC', label: 'Temperature', unit: '°C' },
  { id: 'precipitationMm', label: 'Rainfall', unit: 'mm/h' },
]

function labelOf(f: Field): string {
  return FIELDS.find((x) => x.id === f)?.label ?? f
}
function unitOf(f: Field): string {
  return FIELDS.find((x) => x.id === f)?.unit ?? ''
}

export default function AnalysisPage() {
  const stationsQ = toView(useEnvQuery(['analysis-stations'], getCurrentConditions))
  const [slug, setSlug] = useState('anand-vihar')
  const [xF, setXF] = useState<Field>('windSpeedMs')
  const [yF, setYF] = useState<Field>('pm25')

  const obsQ = toView(
    useEnvQuery(['analysis-obs', slug], () => getObservationHistory(slug, 24 * 30)),
  )
  const weatherQ = toView(
    useEnvQuery(['analysis-weather', slug], () => getWeatherHistory(slug, 24 * 30)),
  )
  const corrQ = toView(
    useEnvQuery(['analysis-corr', slug], () => getCorrelations(slug, 30)),
  )

  const joined = useMemo(() => {
    const weatherByTime = new Map(
      (weatherQ.data ?? []).map((w) => [w.time.slice(0, 13), w]),
    )
    return (obsQ.data ?? [])
      .map((o) => {
        const w = weatherByTime.get(o.time.slice(0, 13))
        const hour = new Date(o.time).getUTCHours()
        return {
          time: o.time,
          hour,
          pm25: o.pollutants.pm25 ?? null,
          pm10: o.pollutants.pm10 ?? null,
          no2: o.pollutants.no2 ?? null,
          o3: o.pollutants.o3 ?? null,
          windSpeedMs: w?.windSpeedMs ?? null,
          relativeHumidityPct: w?.relativeHumidityPct ?? null,
          temperatureC: w?.temperatureC ?? null,
          precipitationMm: w?.precipitationMm ?? null,
        }
      })
      .filter(
        (r) =>
          r.windSpeedMs !== null &&
          r.relativeHumidityPct !== null &&
          r.temperatureC !== null &&
          r.precipitationMm !== null &&
          r.pm25 !== null,
      )
  }, [obsQ.data, weatherQ.data])

  const scatterPoints = useMemo(
    () =>
      joined
        .filter((r) => r[xF] !== null && r[yF] !== null)
        .map((r) => ({ x: Number(r[xF]), y: Number(r[yF]) })),
    [joined, xF, yF],
  )

  const diurnalRows = useMemo(() => {
    const byHour = new Map<number, number[]>()
    for (const r of joined) {
      const list = byHour.get(r.hour) ?? []
      list.push(Number(r.pm25))
      byHour.set(r.hour, list)
    }
    return Array.from({ length: 24 }, (_, h) => {
      const list = (byHour.get(h) ?? []).slice().sort((a, b) => a - b)
      if (list.length < 4) return { hour: `${String(h).padStart(2, '0')}:00`, p25: null, median: null, p75: null }
      const q = (p: number) => list[Math.floor(p * (list.length - 1))]
      return {
        hour: `${String(h).padStart(2, '0')}:00`,
        p25: q(0.25),
        median: q(0.5),
        p75: q(0.75),
      }
    })
  }, [joined])

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-x-6 gap-y-3">
        <label className="flex flex-col gap-1 text-xs text-slate-400">
          Station
          <select
            value={slug}
            onChange={(e) => setSlug(e.target.value)}
            aria-label="Station"
            className="max-w-[240px] rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs text-slate-200 focus:border-emerald-500 focus:outline-none"
          >
            {(stationsQ.data ?? []).map((s) => (
              <option key={s.slug} value={s.slug}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
        <p className="text-[11px] text-slate-500">
          Trailing 30 days · hourly pairs · associations shown are not causal effects.
        </p>
      </div>

      <SectionCard
        title="Weather vs pollution"
        subtitle="Each point is one hour; dashed orange line is a least-squares trend"
        actions={<ProvenanceChip source={obsQ.source === 'live' ? 'observed' : 'demo'} />}
        bodyClassName="space-y-3"
      >
        <div className="flex flex-wrap gap-3">
          <label className="flex items-center gap-2 text-xs text-slate-400">
            X variable
            <select
              value={xF}
              onChange={(e) => setXF(e.target.value as Field)}
              aria-label="X variable"
              className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-slate-200 focus:border-emerald-500 focus:outline-none"
            >
              {FIELDS.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.label}
                </option>
              ))}
            </select>
          </label>
          <label className="flex items-center gap-2 text-xs text-slate-400">
            Y variable
            <select
              value={yF}
              onChange={(e) => setYF(e.target.value as Field)}
              aria-label="Y variable"
              className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-slate-200 focus:border-emerald-500 focus:outline-none"
            >
              {FIELDS.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.label}
                </option>
              ))}
            </select>
          </label>
        </div>
        {(obsQ.isLoading || weatherQ.isLoading) && <LoadingSkeleton rows={5} />}
        {scatterPoints.length > 20 ? (
          <>
            <ScatterPlot
              points={scatterPoints}
              xLabel={`${labelOf(xF)} (${unitOf(xF)})`}
              yLabel={`${labelOf(yF)} (${unitOf(yF)})`}
            />
            <p className="text-[11px] text-slate-500">
              n = {scatterPoints.length} hours. Classic expected patterns: PM tends to fall with wind
              speed and rise with humidity in the NCR winter regime.
            </p>
          </>
        ) : (
          !obsQ.isLoading && <EmptyState message="Not enough paired observations yet." />
        )}
      </SectionCard>

      <div className="grid gap-4 xl:grid-cols-2">
        <SectionCard title="Correlation matrix" subtitle="Pearson correlations, trailing window">
          {corrQ.isLoading && <LoadingSkeleton rows={6} />}
          {corrQ.isError && <EmptyState message="Correlations unavailable." />}
          {corrQ.data && <CorrelationHeatmap {...corrQ.data} />}
        </SectionCard>

        <SectionCard
          title="Diurnal profile — PM2.5"
          subtitle="Median hour-of-day pattern with IQR band"
        >
          {diurnalRows.every((r) => r.median === null) ? (
            <LoadingSkeleton rows={5} />
          ) : (
            <>
              <TimeSeriesChart
                data={diurnalRows}
                xKey="hour"
                band={{ lowerKey: 'p25', upperKey: 'p75', label: 'IQR', color: '#38bdf8' }}
                series={[{ key: 'median', label: 'Median PM2.5 µg/m³', color: '#38bdf8' }]}
                leftUnit=""
              />
              <p className="mt-2 text-[11px] text-slate-500">
                Night-time accumulation and morning-peak signatures appear here when the coupling
                features are active in training data. Window ends{' '}
                {joined.length > 0 ? istDayLabel(joined[joined.length - 1].time) : '–'}.
              </p>
            </>
          )}
        </SectionCard>
      </div>
    </div>
  )
}
