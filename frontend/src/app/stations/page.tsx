'use client'

import { useMemo, useState } from 'react'
import Link from 'next/link'
import { ChevronDown, Search } from 'lucide-react'
import { toView, useEnvQuery } from '@/lib/hooks'
import { getCurrentConditions } from '@/lib/api'
import { SectionCard } from '@/components/common/SectionCard'
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton'
import { EmptyState } from '@/components/common/EmptyState'
import { AqiBadge } from '@/components/common/AqiBadge'
import { ProvenanceChip } from '@/components/common/Chips'
import { POLLUTANT_LABELS } from '@/lib/aqi'

type SortKey = 'name' | 'aqi' | 'pm25' | 'freshness'

export default function StationsPage() {
  const currentQ = toView(useEnvQuery(['stations-table'], getCurrentConditions))
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState<SortKey>('aqi')
  const [sortAsc, setSortAsc] = useState(false)

  const rows = useMemo(() => {
    const data = currentQ.data ?? []
    const q = search.trim().toLowerCase()
    const filtered = data.filter(
      (s) =>
        q === '' ||
        s.name.toLowerCase().includes(q) ||
        s.city.toLowerCase().includes(q),
    )
    const sorted = [...filtered].sort((a, b) => {
      let cmp = 0
      if (sortKey === 'name') cmp = a.name.localeCompare(b.name)
      else if (sortKey === 'aqi') cmp = a.aqi - b.aqi
      else if (sortKey === 'pm25') cmp = (a.pollutants.pm25 ?? -1) - (b.pollutants.pm25 ?? -1)
      else cmp = a.freshnessMinutes - b.freshnessMinutes
      return sortAsc ? cmp : -cmp
    })
    return sorted
  }, [currentQ.data, search, sortKey, sortAsc])

  const header = (key: SortKey, label: string) => (
    <button
      onClick={() => {
        if (sortKey === key) setSortAsc((prev) => !prev)
        else {
          setSortKey(key)
          setSortAsc(key === 'name')
        }
      }}
      className="inline-flex items-center gap-1 text-left text-[11px] font-semibold uppercase tracking-wider text-slate-500 hover:text-slate-300"
    >
      {label}
      <ChevronDown
        size={12}
        className={sortKey === key && !sortAsc ? '' : 'rotate-180 opacity-40'}
        aria-hidden
      />
    </button>
  )

  return (
    <div className="space-y-4">
      <SectionCard
        title="Monitoring stations"
        subtitle="Click a row for the station detail view"
        actions={
          <>
            <ProvenanceChip source={currentQ.source} />
            <label className="relative">
              <Search size={14} className="absolute left-2.5 top-2.5 text-slate-500" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search name or city…"
                aria-label="Search stations"
                className="w-52 rounded-lg border border-slate-700 bg-slate-900 py-1.5 pl-8 pr-3 text-xs text-slate-200 placeholder:text-slate-600 focus:border-emerald-500 focus:outline-none"
              />
            </label>
          </>
        }
        bodyClassName=""
      >
        {currentQ.isLoading && (
          <div className="px-0 py-2">
            <LoadingSkeleton rows={8} />
          </div>
        )}
        {currentQ.isError && <EmptyState message="Station list unavailable." />}
        {!currentQ.isLoading && !currentQ.isError && rows.length === 0 && (
          <EmptyState message="No stations match your search." />
        )}
        {rows.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-left">
                  <th className="py-2 pr-3">{header('name', 'Station')}</th>
                  <th className="py-2 pr-3 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                    City
                  </th>
                  <th className="py-2 pr-3">{header('aqi', 'AQI')}</th>
                  <th className="py-2 pr-3">{header('pm25', `PM2.5 (${POLLUTANT_LABELS.pm25})`)}</th>
                  <th className="py-2 pr-3 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                    Dominant
                  </th>
                  <th className="py-2 pr-3">{header('freshness', 'Updated')}</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((s) => (
                  <tr key={s.slug} className="border-b border-slate-800/60 hover:bg-slate-900/60">
                    <td className="py-2 pr-3">
                      <Link
                        href={`/stations/${s.slug}`}
                        className="font-medium text-slate-200 hover:text-emerald-300"
                      >
                        {s.name}
                      </Link>
                    </td>
                    <td className="py-2 pr-3 text-xs text-slate-400">{s.city}</td>
                    <td className="py-2 pr-3">
                      <AqiBadge value={s.aqi} size="sm" />
                    </td>
                    <td className="py-2 pr-3 font-mono text-xs text-slate-300">
                      {s.pollutants.pm25 ?? '–'} µg/m³
                    </td>
                    <td className="py-2 pr-3 text-xs uppercase text-slate-400">
                      {s.dominantPollutant.replace('pm', 'PM').replace('no2', 'NO₂')}
                    </td>
                    <td className="py-2 pr-3 text-xs text-slate-500">
                      {s.freshnessMinutes <= 90 ? `${s.freshnessMinutes} min ago` : 'stale'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>
    </div>
  )
}
