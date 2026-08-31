'use client'

import type { ReactElement } from 'react'
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

export interface SeriesDef {
  key: string
  label: string
  color: string
  dashed?: boolean
  yAxis?: 'left' | 'right'
}

interface BandDef {
  lowerKey: string
  upperKey: string
  label: string
  color: string
}

interface TimeSeriesChartProps {
  data: Array<Record<string, number | string | null>>
  xKey: string
  series: SeriesDef[]
  band?: BandDef
  height?: number
  xTickFormatter?: (value: string, index: number) => string
  leftUnit?: string
  rightUnit?: string
}

function TooltipContent({
  active,
  payload,
  label,
  series,
}: {
  active?: boolean
  payload?: Array<{ dataKey?: string | number; name?: string; value?: number | string; color?: string }>
  label?: string | number
  series: SeriesDef[]
}): ReactElement | null {
  if (!active || !payload || payload.length === 0) return null
  const visible = payload.filter(
    (p) => typeof p.dataKey === 'string' && !p.dataKey.startsWith('__') && p.value !== null && p.value !== undefined && p.value !== '',
  )
  if (visible.length === 0) return null
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900/95 px-3 py-2 text-xs shadow-xl">
      <div className="mb-1 font-medium text-slate-300">{label}</div>
      {visible.map((p) => {
        const def = series.find((s) => s.key === p.dataKey)
        return (
          <div key={String(p.dataKey)} className="flex items-center gap-2 py-0.5 text-slate-200">
            <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: p.color }} />
            <span>{def?.label ?? String(p.name)}</span>
            <span className="ml-auto pl-3 font-mono">{String(p.value)}</span>
          </div>
        )
      })}
    </div>
  )
}

export function TimeSeriesChart({
  data,
  xKey,
  series,
  band,
  height = 260,
  xTickFormatter,
  leftUnit,
  rightUnit,
}: TimeSeriesChartProps) {
  const rows =
    band !== undefined
      ? data.map((row) => {
          const lower = Number(row[band.lowerKey] ?? NaN)
          const upper = Number(row[band.upperKey] ?? NaN)
          const valid = Number.isFinite(lower) && Number.isFinite(upper)
          return {
            ...row,
            __bandBase: valid ? lower : null,
            __bandSpan: valid ? Math.max(0, upper - lower) : null,
          }
        })
      : data

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={rows} margin={{ top: 8, right: rightUnit ? 4 : 12, bottom: 4, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" strokeOpacity={0.35} />
        <XAxis
          dataKey={xKey}
          tick={{ fill: '#94a3b8', fontSize: 11 }}
          tickFormatter={xTickFormatter}
          minTickGap={32}
          axisLine={{ stroke: '#334155' }}
          tickLine={false}
        />
        <YAxis
          yAxisId="left"
          tick={{ fill: '#94a3b8', fontSize: 11 }}
          width={44}
          axisLine={false}
          tickLine={false}
          unit={leftUnit ? ` ${leftUnit}` : undefined}
        />
        {series.some((s) => s.yAxis === 'right') && (
          <YAxis
            yAxisId="right"
            orientation="right"
            tick={{ fill: '#7dd3fc', fontSize: 11 }}
            width={44}
            axisLine={false}
            tickLine={false}
            unit={rightUnit ? ` ${rightUnit}` : undefined}
          />
        )}
        <Tooltip content={<TooltipContent series={series} />} />
        <Legend wrapperStyle={{ fontSize: 11, color: '#94a3b8' }} />
        {band && (
          <>
            <Area
              dataKey="__bandBase"
              stackId="__band"
              stroke="none"
              fill="transparent"
              legendType="none"
              isAnimationActive={false}
              name=""
            />
            <Area
              dataKey="__bandSpan"
              stackId="__band"
              stroke="none"
              fill={band.color}
              fillOpacity={0.22}
              legendType="none"
              isAnimationActive={false}
              name={band.label}
            />
          </>
        )}
        {series.map((s) => (
          <Line
            key={s.key}
            yAxisId={s.yAxis ?? 'left'}
            type="monotone"
            dataKey={s.key}
            name={s.label}
            stroke={s.color}
            strokeWidth={s.dashed ? 1.6 : 2}
            strokeDasharray={s.dashed ? '6 4' : undefined}
            dot={false}
            connectNulls
            isAnimationActive={false}
          />
        ))}
      </ComposedChart>
    </ResponsiveContainer>
  )
}
