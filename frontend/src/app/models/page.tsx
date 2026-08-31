'use client'

import { useMemo, useState } from 'react'
import { AlertTriangle } from 'lucide-react'
import { toView, useEnvQuery } from '@/lib/hooks'
import { getModelPerformance, getGlobalImportance } from '@/lib/api'
import { SectionCard } from '@/components/common/SectionCard'
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton'
import { EmptyState } from '@/components/common/EmptyState'
import { ProvenanceChip } from '@/components/common/Chips'
import { HorizontalBars } from '@/components/charts/HorizontalBars'
import { DEMO_MODEL_NOTICE } from '@/lib/demo/data'
import type { ForecastTarget } from '@/types/api'

const TARGETS: Array<{ id: ForecastTarget; label: string }> = [
  { id: 'aqi', label: 'AQI' },
  { id: 'pm25', label: 'PM2.5' },
  { id: 'pm10', label: 'PM10' },
]

const HORIZONS = [1, 3, 6, 12, 24, 48] as const

export default function ModelsPage() {
  const [target, setTarget] = useState<ForecastTarget>('aqi')
  const [horizon, setHorizon] = useState<number>(24)

  const perfQ = toView(useEnvQuery(['perf', target], () => getModelPerformance(target)))
  const importanceQ = toView(useEnvQuery(['importance'], getGlobalImportance))

  const rowsForHorizon = useMemo(
    () => (perfQ.data ?? []).filter((r) => r.horizonHours === horizon),
    [perfQ.data, horizon],
  )

  const champion = useMemo(
    () =>
      [...rowsForHorizon].sort((a, b) => a.mae - b.mae)[0] ?? null,
    [rowsForHorizon],
  )

  return (
    <div className="space-y-4">
      <div className="flex items-start gap-2 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-xs text-amber-300">
        <AlertTriangle size={15} className="mt-0.5 shrink-0" />
        <span>{DEMO_MODEL_NOTICE}</span>
      </div>

      <SectionCard
        title="Model comparison"
        subtitle="Walk-forward validation · identical folds across all models"
        actions={<ProvenanceChip source={perfQ.source === 'live' ? 'model-derived' : 'demo'} />}
        bodyClassName="space-y-3"
      >
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
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
          <div role="tablist" aria-label="Horizon" className="flex flex-wrap rounded-lg bg-slate-900 p-0.5 ring-1 ring-inset ring-slate-700">
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

        {perfQ.isLoading && <LoadingSkeleton rows={7} />}
        {perfQ.isError && <EmptyState message="Performance data unavailable." />}
        {rowsForHorizon.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-left text-[11px] uppercase tracking-wider text-slate-500">
                  <th className="py-2 pr-3">Model</th>
                  <th className="py-2 pr-3">MAE ↓</th>
                  <th className="py-2 pr-3">RMSE</th>
                  <th className="py-2 pr-3">MAPE %</th>
                  <th className="py-2 pr-3">R²</th>
                  <th className="py-2 pr-3">Skill vs persistence</th>
                  <th className="py-2 pr-3">PICP-80 / PINAW</th>
                </tr>
              </thead>
              <tbody>
                {[...rowsForHorizon]
                  .sort((a, b) => a.mae - b.mae)
                  .map((r) => (
                    <tr
                      key={r.modelName}
                      className={
                        champion?.modelName === r.modelName
                          ? 'border-b border-slate-800/60 bg-emerald-500/5'
                          : 'border-b border-slate-800/60'
                      }
                    >
                      <td className="py-2 pr-3 font-medium text-slate-200">
                        {r.modelName}
                        {champion?.modelName === r.modelName && (
                          <span className="ml-2 rounded bg-emerald-500/15 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-emerald-300">
                            Champion
                          </span>
                        )}
                      </td>
                      <td className="py-2 pr-3 font-mono text-xs text-slate-200">{r.mae.toFixed(1)}</td>
                      <td className="py-2 pr-3 font-mono text-xs text-slate-400">{r.rmse.toFixed(1)}</td>
                      <td className="py-2 pr-3 font-mono text-xs text-slate-400">{r.mape.toFixed(1)}</td>
                      <td className="py-2 pr-3 font-mono text-xs text-slate-400">{r.r2.toFixed(2)}</td>
                      <td className="py-2 pr-3">
                        <span
                          className={
                            r.skillVsPersistence > 0
                              ? 'font-mono text-xs text-emerald-300'
                              : 'font-mono text-xs text-red-400'
                          }
                        >
                          {(r.skillVsPersistence * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td className="py-2 pr-3 font-mono text-xs text-slate-400">
                        {r.picp80 !== null ? `${Math.round(r.picp80 * 100)}% / ${(r.pinaw80 ?? 0).toFixed(2)}` : '–'}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
            <p className="mt-2 text-[11px] text-slate-500">
              MAE/RMSE in AQI index points (or µg/m³ for pollutant targets). Skill &gt; 0 means the
              model beats persistence on MAE. PICP-80 = share of outcomes inside the P10–P90 band;
              PINAW = mean band width relative to level.
            </p>
          </div>
        )}
      </SectionCard>

      <div className="grid gap-4 xl:grid-cols-2">
        <SectionCard title="Skill vs persistence" subtitle={`+${horizon} h horizon`}>
          {rowsForHorizon.length > 0 ? (
            <HorizontalBars
              items={[...rowsForHorizon]
                .sort((a, b) => b.skillVsPersistence - a.skillVsPersistence)
                .map((r) => ({
                  label: r.modelName,
                  value: r.skillVsPersistence * 100,
                  suffix: '%',
                  color: '#34d399',
                }))}
              max={45}
            />
          ) : (
            <LoadingSkeleton rows={6} />
          )}
        </SectionCard>

        <SectionCard
          title="Global feature importance"
          subtitle={`Champion model (${champion?.modelName ?? '–'}) · permutation importance`}
        >
          {importanceQ.isLoading && <LoadingSkeleton rows={8} />}
          {importanceQ.isError && <EmptyState message="Importance unavailable." />}
          {importanceQ.data && (
            <>
              <HorizontalBars
                items={importanceQ.data.map((i) => ({
                  label: i.featureLabel,
                  value: i.importancePct,
                  suffix: '%',
                }))}
              />
              <p className="mt-2 text-[11px] text-slate-500">
                Weather-coupled families (wind vectors, humidity memory, stagnation flags) carry a
                large share of importance — this is the weather–pollution coupling at work.
              </p>
            </>
          )}
        </SectionCard>
      </div>

      <SectionCard title="Run lineage" subtitle="Every number on this page traces to a model run">
        <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-xs md:grid-cols-4">
          <div>
            <dt className="text-slate-500">Validation scheme</dt>
            <dd className="font-mono text-slate-300">walk-forward/expanding-v1</dd>
          </div>
          <div>
            <dt className="text-slate-500">Feature set</dt>
            <dd className="font-mono text-slate-300">weather-coupling-v0</dd>
          </div>
          <div>
            <dt className="text-slate-500">Dataset hash</dt>
            <dd className="font-mono text-slate-300">demo-dataset-v0</dd>
          </div>
          <div>
            <dt className="text-slate-500">Run ID</dt>
            <dd className="font-mono text-slate-300">{champion?.modelRunId ?? '–'}</dd>
          </div>
        </dl>
      </SectionCard>
    </div>
  )
}
