'use client'

import { useMemo, useState } from 'react'
import dynamic from 'next/dynamic'
import { useEnvQuery, toView } from '@/lib/hooks'
import { getCurrentConditions } from '@/lib/api'
import { SectionCard } from '@/components/common/SectionCard'
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton'
import { EmptyState } from '@/components/common/EmptyState'
import { AqiBadge } from '@/components/common/AqiBadge'
import { ProvenanceChip } from '@/components/common/Chips'
import type { CityName } from '@/types/api'

const NcrMap = dynamic(() => import('@/components/map/NcrMap'), {
  ssr: false,
  loading: () => (
    <div className="flex h-[480px] items-center justify-center rounded-xl border border-slate-800 bg-slate-900/60 text-sm text-slate-500">
      Loading map…
    </div>
  ),
})

const CITY_FILTERS: Array<CityName | 'All'> = [
  'All',
  'Delhi',
  'Noida',
  'Greater Noida',
  'Ghaziabad',
  'Gurugram',
  'Faridabad',
]

export default function MapPage() {
  const currentQ = toView(useEnvQuery(['map-current'], getCurrentConditions))
  const [cityFilter, setCityFilter] = useState<CityName | 'All'>('All')

  const stations = currentQ.data
  const filtered = useMemo(
    () => (stations ?? []).filter((s) => cityFilter === 'All' || s.city === cityFilter),
    [stations, cityFilter],
  )

  return (
    <div className="space-y-4">
      <SectionCard
        title="Station map"
        subtitle="Marker shows current AQI; click a marker for details. Interpolated surfaces arrive with the backend spatial API."
        actions={<ProvenanceChip source={currentQ.source} />}
        bodyClassName="space-y-3"
      >
        <div className="flex flex-wrap gap-2">
          {CITY_FILTERS.map((c) => (
            <button
              key={c}
              onClick={() => setCityFilter(c)}
              className={
                cityFilter === c
                  ? 'rounded-full bg-emerald-500/15 px-3 py-1 text-xs font-medium text-emerald-300 ring-1 ring-inset ring-emerald-500/40'
                  : 'rounded-full px-3 py-1 text-xs text-slate-400 ring-1 ring-inset ring-slate-700 hover:text-slate-200'
              }
            >
              {c}
            </button>
          ))}
        </div>
        {currentQ.isLoading && <LoadingSkeleton rows={4} />}
        {currentQ.isError && <EmptyState message="Map data unavailable." />}
        {!currentQ.isLoading && filtered.length > 0 && <NcrMap stations={filtered} />}
      </SectionCard>

      {filtered.length > 0 && (
        <SectionCard title="Current readings" subtitle={`Top 12 by AQI · ${filtered.length} stations in view`}>
          <div className="grid grid-cols-2 gap-2 md:grid-cols-3 xl:grid-cols-4">
            {[...filtered]
              .sort((a, b) => b.aqi - a.aqi)
              .slice(0, 12)
              .map((s) => (
                <div
                  key={s.slug}
                  className="rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-2"
                >
                  <div className="truncate text-xs font-medium text-slate-300">{s.name}</div>
                  <div className="mt-1 flex items-center justify-between gap-2">
                    <span className="font-mono text-sm text-slate-100">{Math.round(s.aqi)}</span>
                    <AqiBadge value={s.aqi} size="sm" showValue={false} />
                  </div>
                </div>
              ))}
          </div>
        </SectionCard>
      )}
    </div>
  )
}
