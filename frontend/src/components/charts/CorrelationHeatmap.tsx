'use client'

import { fmtNum } from '@/lib/format'

interface CorrelationHeatmapProps {
  rows: string[]
  cols: string[]
  values: number[][]
}

function cellColor(v: number): string {
  const clamped = Math.max(-1, Math.min(1, v))
  if (clamped >= 0) {
    const t = clamped
    const r = Math.round(15 + (225 - 15) * t)
    const g = Math.round(23 + (80 - 23) * t)
    const b = Math.round(42 + (60 - 42) * t)
    return `rgb(${r},${g},${b})`
  }
  const t = -clamped
  const r = Math.round(15 + (56 - 15) * t)
  const g = Math.round(23 + (150 - 23) * t)
  const b = Math.round(42 + (230 - 42) * t)
  return `rgb(${r},${g},${b})`
}

export function CorrelationHeatmap({ rows, cols, values }: CorrelationHeatmapProps) {
  return (
    <div className="overflow-x-auto">
      <table className="border-separate border-spacing-0.5 text-[11px]">
        <thead>
          <tr>
            <th className="p-1" aria-hidden />
            {cols.map((c) => (
              <th key={c} className="p-1 text-slate-400 font-medium" scope="col">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={r}>
              <th scope="row" className="whitespace-nowrap p-1 pr-2 text-right text-slate-400 font-medium">
                {r}
              </th>
              {cols.map((c, j) => {
                const v = values[i]?.[j] ?? 0
                return (
                  <td
                    key={c}
                    className="h-9 w-14 min-w-[3rem] rounded text-center font-mono text-slate-100"
                    style={{ backgroundColor: cellColor(v), opacity: i === j ? 0.35 : 1 }}
                    title={`${r} vs ${c}: ${fmtNum(v, 2)}`}
                  >
                    {v.toFixed(2)}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-[10px] text-slate-600">
        Blue = negative association · Red = positive association. Associations, not causation.
      </p>
    </div>
  )
}
