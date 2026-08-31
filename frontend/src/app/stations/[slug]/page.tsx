'use client'

import { useMemo } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { ArrowLeft } from 'lucide-react'
import { toView, useEnvQuery } from '@/lib/hooks'
import {
  getAvailability,
  getCurrentConditions,
  getDataQualityIncidents,
  getObservationHistory,
  getWeatherHistory,
} from '@/lib/api'
import { SectionCard } from '@/components/common/SectionCard'
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton'
import { EmptyState } from '@/components/common/EmptyState'
import { AqiBadge } from '@/components/common/AqiBadge'
import { KpiCard } from '@/components/common/KpiCard'
import { ProvenanceChip, SeverityChip } from '@/components/common/Chips'
import { TimeSeriesChart } from '@/components/charts/TimeSeriesChart'
import { ALL_POLLUTANTS, POLLUTANT_LABELS, POLLUTANT_UNITS } from '@/lib/aqi'
import { fmtNum, freshnessLabel, istDayLabel, istDateTime } from '@/lib/format'

export default function StationDetailPage() {
  const params = useParams<{ slug: string }>()
  const slug = params?.slug ?? ''

  const currentQ = toView(useEnvQuery(['station-current', slug], getCurrentConditions))
  const historyQ = toView(
    useEnvQuery(['station-history', slug], () => getObservationHistory(slug, 24 * 14)),
  )
  const weatherQ = toView(
    useEnvQuery(['station-weather', slug], () => getWeatherHistory(slug, 24 * 14)),
  )
  const availabilityQ = toView(useEnvQuery(['station-avail', slug], () => getAvailability(slug)))
  const dqQ = toView(useEnvQuery(['station-dq', slug], getDataQualityIncidents))

  const station = currentQ.data?.find((s) => s.slug === slug)

  const historyRows = useMemo(() => {
    const obs = historyQ.data ?? []
    return obs.map((o) => ({
      time: o.time,
      aqi: o.aqi,
      pm25: o.pollutants.pm25 ?? null,
      pm10: o.pollutants.pm10 ?? null,
      no2: o.pollutants.no2 ?? null,
      flag: o.qualityFlag,
    }))
  }, [historyQ.data])

  const weatherRows = useMemo(() => {
    const w = weatherQ.data ?? []
    return w.map((p) => ({
      time: p.time,
      temperatureC: p.temperatureC,
      relativeHumidityPct: p.relativeHumidityPct,
      windSpeedMs: p.windSpeedMs,
    }))
  }, [weatherQ.data])

  if (currentQ.isLoading) {
    return (
      <div className="space-y-4">
        <LoadingSkeleton rows={4} />
        <LoadingSkeleton rows={8} />
      </div>
    )
  }
  if (!station) {
    return (
      <EmptyState message="Station not found. Pick one from the Station Explorer." />
    )
  }

  const incidents = (dqQ.data ?? []).filter((i) => i.stationSlug === slug || i.stationSlug === null)

  return (
    <div className="space-y-4">
      <Link
        href="/stations"
        className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200"
      >
        <ArrowLeft size={13} /> All stations
      </Link>

      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-800 bg-slate-900/50 px-5 py-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-100">{station.name}</h2>
          <p className="text-xs text-slate-500">
            {station.city} · {station.latitude.toFixed(4)}°N {station.longitude.toFixed(4)}°E ·
            updated {freshnessLabel(station.freshnessMinutes)}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <ProvenanceChip source={currentQ.source === 'live' ? 'observed' : 'demo'} />
          <AqiBadge value={station.aqi} size="lg" />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        {(['pm25', 'pm10', 'no2', 'so2', 'co', 'o3'] as const).map((p) => (
          <KpiCard
            key={p}
            title={POLLUTANT_LABELS[p]}
            value={fmtNum(station.pollutants[p])}
            sub={POLLUTANT_UNITS[p]}
          />
        ))}
      </div>

      <SectionCard title="Last 14 days" subtitle="Hourly AQI and particulates">
        {historyRows.length > 0 ? (
          <TimeSeriesChart
            data={historyRows}
            xKey="time"
            xTickFormatter={(t) => istDayLabel(String(t))}
            series={[
              { key: 'aqi', label: 'AQI', color: '#34d399' },
              { key: 'pm25', label: 'PM2.5 µg/m³', color: '#38bdf8', yAxis: 'right' },
              { key: 'pm10', label: 'PM10 µg/m³', color: '#a78bfa', yAxis: 'right' },
            ]}
            height={280}
          />
        ) : (
          <LoadingSkeleton rows={4} />
        )}
      </SectionCard>

      <div className="grid gap-4 xl:grid-cols-2">
        <SectionCard title="Meteorology" subtitle="Temperature, humidity, wind — trailing window">
          {weatherRows.length > 0 ? (
            <TimeSeriesChart
              data={weatherRows}
              xKey="time"
              xTickFormatter={(t) => istDayLabel(String(t))}
              rightUnit="%"
              series={[
                { key: 'temperatureC', label: 'Temp °C', color: '#fb923c' },
                { key: 'windSpeedMs', label: 'Wind m/s', color: '#38bdf8' },
                { key: 'relativeHumidityPct', label: 'RH %', color: '#7dd3fc', yAxis: 'right' },
              ]}
            />
          ) : (
            <LoadingSkeleton rows={4} />
          )}
        </SectionCard>

        <SectionCard title="Data availability" subtitle="Share of expected hourly readings per day">
          {availabilityQ.isLoading && <LoadingSkeleton rows={5} />}
          {availabilityQ.data && (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-left text-[11px] uppercase tracking-wider text-slate-500">
                    <th className="py-1.5 pr-2">Pollutant</th>
                    {(availabilityQ.data.matrix[ALL_POLLUTANTS[0]] ?? []).map((cell) => (
                      <th key={cell.dayIso} className="px-1 py-1.5 font-medium">
                        {istDayLabel(cell.dayIso)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {ALL_POLLUTANTS.map((p) => (
                    <tr key={p} className="border-b border-slate-800/50">
                      <td className="py-1.5 pr-2 font-medium text-slate-300">{POLLUTANT_LABELS[p]}</td>
                      {(availabilityQ.data?.matrix[p] ?? []).map((cell) => (
                        <td key={cell.dayIso} className="px-1 py-1.5 text-center">
                          <span
                            className={
                              cell.pctAvailable >= 90
                                ? 'rounded bg-emerald-500/15 px-1.5 py-0.5 text-emerald-300'
                                : cell.pctAvailable >= 70
                                  ? 'rounded bg-amber-500/15 px-1.5 py-0.5 text-amber-300'
                                  : 'rounded bg-red-500/15 px-1.5 py-0.5 text-red-300'
                            }
                          >
                            {cell.pctAvailable}%
                          </span>
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </SectionCard>
      </div>

      <SectionCard title="Data quality events" subtitle="For this station and network-wide notices">
        {incidents.length === 0 ? (
          <EmptyState message="No quality incidents recorded." />
        ) : (
          <ul className="space-y-2">
            {incidents.map((i) => (
              <li key={i.id} className="flex flex-wrap items-center gap-x-3 gap-y-1 rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-2">
                <SeverityChip severity={i.severity} />
                <span className="font-mono text-[11px] uppercase tracking-wide text-slate-400">
                  {i.checkType}
                </span>
                <span className="min-w-0 flex-1 truncate text-xs text-slate-300">{i.detail}</span>
                <span className="text-[11px] text-slate-500">{istDateTime(i.detectedAt)}</span>
              </li>
            ))}
          </ul>
        )}
      </SectionCard>
    </div>
  )
}
