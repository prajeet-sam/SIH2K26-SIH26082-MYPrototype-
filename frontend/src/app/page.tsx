'use client'

import { useMemo, useState } from 'react'
import Link from 'next/link'
import {
  Activity,
  ArrowRight,
  BellRing,
  CloudSun,
  RadioTower,
  Timer,
} from 'lucide-react'
import { useEnvQuery, toView } from '@/lib/hooks'
import { getCurrentConditions, getAlerts, getForecast } from '@/lib/api'
import { AqiBadge } from '@/components/common/AqiBadge'
import { KpiCard } from '@/components/common/KpiCard'
import { SectionCard } from '@/components/common/SectionCard'
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton'
import { EmptyState } from '@/components/common/EmptyState'
import { ProvenanceChip, SeverityChip } from '@/components/common/Chips'
import { TimeSeriesChart } from '@/components/charts/TimeSeriesChart'
import { Sparkline } from '@/components/charts/Sparkline'
import { istTime } from '@/lib/format'
import type { CityName, CurrentConditions } from '@/types/api'

const CITIES: CityName[] = [
  'Delhi',
  'Noida',
  'Greater Noida',
  'Ghaziabad',
  'Gurugram',
  'Faridabad',
]

const HOTSPOTS = ['anand-vihar', 'wazirpur', 'ito', 'bawana', 'indirapuram']

function citySummary(stations: CurrentConditions[], city: CityName) {
  const list = stations.filter((s) => s.city === city)
  if (list.length === 0) return null
  const avgAqi = Math.round(list.reduce((acc, s) => acc + (Number.isFinite(s.aqi) ? s.aqi : 0), 0) / list.length)
  const worst = list.reduce((a, b) => (b.aqi > a.aqi ? b : a))
  const trendLen = Math.min(...list.map((s) => s.trend24hAqi.length), 24)
  const cityTrend: number[] = []
  for (let i = 0; i < trendLen; i++) {
    cityTrend.push(Math.round(list.reduce((acc, s) => acc + s.trend24hAqi[i], 0) / list.length))
  }
  return { avgAqi, worst, count: list.length, cityTrend }
}

export default function OverviewPage() {
  const currentQ = toView(useEnvQuery(['current'], getCurrentConditions))
  const alertsQ = toView(useEnvQuery(['alerts-preview'], getAlerts))
  const [hotspot, setHotspot] = useState(HOTSPOTS[0])
  const forecastQ = toView(
    useEnvQuery(['forecast-strip', hotspot], () => getForecast(hotspot, 'aqi', 24)),
  )

  const stations = currentQ.data
  const worstStation = useMemo(
    () =>
      stations && stations.length > 0
        ? stations.reduce((a, b) => (b.aqi > a.aqi ? b : a))
        : null,
    [stations],
  )
  const activeAlerts = useMemo(
    () => (alertsQ.data ?? []).filter((a) => a.resolvedAt === null),
    [alertsQ.data],
  )

  const forecastRows = useMemo(() => {
    const f = forecastQ.data
    if (!f) return []
    const observed = f.observedTail.slice(-8).map((o) => ({
      time: o.time,
      observed: o.aqi,
      p50: null as number | null,
      p10: null,
      p90: null,
    }))
    const forecast = f.points
      .filter((p) => p.horizonHours <= 24)
      .map((p) => ({
        time: p.targetTime,
        observed: null as number | null,
        p50: p.p50,
        p10: p.p10,
        p90: p.p90,
      }))
      .slice(0, 12)
    return [...observed, ...forecast]
  }, [forecastQ.data])

  return (
    <div className="space-y-6">
      <section className="relative overflow-hidden rounded-2xl border border-slate-800/80 bg-gradient-to-br from-slate-900/70 via-slate-900/40 to-emerald-950/20 p-6 shadow-card backdrop-blur md:p-8">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-emerald-400/40 to-transparent" />
        <div className="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full bg-emerald-500/10 blur-3xl" />
        <div className="relative flex flex-col justify-between gap-6 md:flex-row md:items-end">
          <div className="max-w-2xl">
            <p className="mb-2 inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wider text-emerald-300 ring-1 ring-inset ring-emerald-500/30">
              <CloudSun size={13} />
              Weather-coupled AQI forecasting
            </p>
            <h2 className="text-2xl font-semibold tracking-tight text-slate-50 md:text-3xl">
              Air quality across{" "}
              <span className="bg-gradient-to-r from-emerald-300 to-sky-300 bg-clip-text text-transparent">
                Delhi NCR
              </span>
              , today and ahead
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-400">
              Live station observations fused with meteorological drivers to give clearer
              PM pollution forecasts, with confidence bands and transparent explainability.
            </p>
          </div>
          {worstStation && stations && (
            <Link
              href={`/stations?station=${worstStation.slug}`}
              className="group flex shrink-0 items-center gap-3 rounded-xl border border-slate-700/60 bg-slate-950/40 px-4 py-3 transition-colors hover:border-emerald-500/40"
            >
              <div className="text-right">
                <div className="text-[11px] uppercase tracking-wider text-slate-500">
                  Worst right now
                </div>
                <div className="text-sm font-medium text-slate-200">
                  {worstStation.name}
                </div>
              </div>
              <AqiBadge value={worstStation.aqi} />
              <ArrowRight
                size={16}
                className="text-slate-500 transition-transform group-hover:translate-x-0.5 group-hover:text-emerald-300"
              />
            </Link>
          )}
        </div>
      </section>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <KpiCard
          title="Stations online"
          icon={<RadioTower size={14} />}
          value={stations ? stations.filter((s) => s.freshnessMinutes <= 90).length : '–'}
          sub={stations ? `of ${stations.length} NCR monitors` : undefined}
        />
        <KpiCard
          title="Active alerts"
          icon={<BellRing size={14} />}
          value={activeAlerts.length}
          sub={`${activeAlerts.filter((a) => a.severity === 'critical').length} critical`}
          badge={<Link href="/alerts" className="text-xs text-emerald-400 hover:text-emerald-300">View all</Link>}
        />
        <KpiCard
          title="Worst hotspot"
          icon={<Activity size={14} />}
          value={worstStation ? Math.round(worstStation.aqi) : '–'}
          sub={
            worstStation
              ? `${worstStation.name} · ${worstStation.dominantPollutant.toUpperCase()}`
              : undefined
          }
          badge={worstStation ? <AqiBadge value={worstStation.aqi} size="sm" /> : undefined}
        />
        <KpiCard
          title="Data freshness"
          icon={<Timer size={14} />}
          value={
            stations && stations.length > 0
              ? `${Math.max(...stations.map((s) => s.freshnessMinutes))} min`
              : '–'
          }
          sub="oldest station update"
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <SectionCard
          title="NCR at a glance"
          subtitle="City-average AQI with 24 h trend"
          className="xl:col-span-1"
          actions={<ProvenanceChip source={currentQ.source} />}
          bodyClassName="space-y-3"
        >
          {currentQ.isLoading && <LoadingSkeleton rows={6} />}
          {currentQ.isError && (
            <EmptyState message="Could not load current conditions." />
          )}
          {stations &&
            CITIES.map((city) => {
              const summary = citySummary(stations, city)
              if (!summary) return null
              return (
                <div key={city} className="flex items-center justify-between gap-3 rounded-lg p-1.5 transition-colors hover:bg-slate-800/30">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-baseline gap-2">
                      <span className="truncate text-sm font-medium text-slate-200">{city}</span>
                      <span className="text-[11px] text-slate-500">{summary.count} stations</span>
                    </div>
                    <div className="text-[11px] text-slate-500">
                      Worst: {summary.worst.name}
                    </div>
                    <div className="mt-1 w-full max-w-[180px]">
                      <Sparkline data={summary.cityTrend} color="#94a3b8" />
                    </div>
                  </div>
                  <AqiBadge value={summary.avgAqi} />
                </div>
              )
            })}
        </SectionCard>

        <SectionCard
          title="Next-24h AQI trajectory"
          subtitle="Model forecast with P10–P90 uncertainty band"
          className="xl:col-span-2"
          actions={
            <>
              <ProvenanceChip source={forecastQ.source} />
              <select
                value={hotspot}
                onChange={(e) => setHotspot(e.target.value)}
                aria-label="Choose station"
                className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-slate-200 focus:border-emerald-500 focus:outline-none"
              >
                {HOTSPOTS.map((slug) => (
                  <option key={slug} value={slug}>
                    {STATION_LABEL[slug] ?? slug}
                  </option>
                ))}
              </select>
            </>
          }
        >
          {forecastQ.isLoading && <LoadingSkeleton rows={5} />}
          {forecastRows.length > 0 && (
            <TimeSeriesChart
              data={forecastRows}
              xKey="time"
              xTickFormatter={(t) => istTime(String(t))}
              band={{ lowerKey: 'p10', upperKey: 'p90', label: 'P10–P90', color: '#34d399' }}
              series={[
                { key: 'observed', label: 'Observed AQI', color: '#38bdf8' },
                { key: 'p50', label: 'Forecast AQI', color: '#34d399', dashed: true },
              ]}
            />
          )}
          <Link
            href={`/forecast?station=${hotspot}`}
            className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-emerald-400 hover:text-emerald-300"
          >
            Open full forecast <ArrowRight size={13} />
          </Link>
        </SectionCard>
      </div>

      <SectionCard
        title="Active alerts"
        subtitle="Threshold crossings and rapid-rise detections"
        actions={<Link href="/alerts" className="text-xs text-emerald-400 hover:text-emerald-300">All alerts</Link>}
      >
        {alertsQ.isLoading && <LoadingSkeleton rows={3} />}
        {!alertsQ.isLoading && activeAlerts.length === 0 && (
          <EmptyState message="No active alerts — conditions are within configured thresholds." />
        )}
        <ul className="space-y-2">
          {activeAlerts.slice(0, 4).map((alert) => (
            <li
              key={alert.id}
              className="flex flex-wrap items-center gap-x-3 gap-y-1 rounded-xl border border-slate-800/80 bg-slate-950/40 px-3.5 py-2.5 transition-colors hover:border-slate-700"
            >
              <SeverityChip severity={alert.severity} />
              <span className="min-w-0 flex-1 truncate text-sm text-slate-300">{alert.message}</span>
              <span className="text-[11px] tabular-nums text-slate-500">{istTime(alert.triggeredAt)} IST</span>
            </li>
          ))}
        </ul>
      </SectionCard>
    </div>
  )
}

const STATION_LABEL: Record<string, string> = {
  'anand-vihar': 'Anand Vihar',
  wazirpur: 'Wazirpur',
  ito: 'ITO',
  bawana: 'Bawana',
  indirapuram: 'Indirapuram',
}
