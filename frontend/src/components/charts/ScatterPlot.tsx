'use client'

import { useMemo } from 'react'
import {
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Scatter,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

interface ScatterPlotProps {
  points: Array<{ x: number; y: number }>
  xLabel: string
  yLabel: string
  color?: string
  height?: number
}

export function ScatterPlot({
  points,
  xLabel,
  yLabel,
  color = '#38bdf8',
  height = 260,
}: ScatterPlotProps) {
  const regression = useMemo(() => {
    const n = points.length
    if (n < 2) return null
    let sx = 0
    let sy = 0
    let sxx = 0
    let sxy = 0
    for (const p of points) {
      sx += p.x
      sy += p.y
      sxx += p.x * p.x
      sxy += p.x * p.y
    }
    const den = n * sxx - sx * sx
    if (den === 0) return null
    const slope = (n * sxy - sx * sy) / den
    const intercept = (sy - slope * sx) / n
    const xs = points.map((p) => p.x)
    const minX = Math.min(...xs)
    const maxX = Math.max(...xs)
    return [
      { x: minX, y: slope * minX + intercept },
      { x: maxX, y: slope * maxX + intercept },
    ]
  }, [points])

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart margin={{ top: 8, right: 12, bottom: 18, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" strokeOpacity={0.35} />
        <XAxis
          type="number"
          dataKey="x"
          name={xLabel}
          tick={{ fill: '#94a3b8', fontSize: 11 }}
          axisLine={{ stroke: '#334155' }}
          tickLine={false}
          label={{
            value: xLabel,
            position: 'insideBottom',
            offset: -12,
            fill: '#64748b',
            fontSize: 11,
          }}
        />
        <YAxis
          type="number"
          dataKey="y"
          name={yLabel}
          tick={{ fill: '#94a3b8', fontSize: 11 }}
          width={44}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          cursor={{ strokeDasharray: '3 3', stroke: '#475569' }}
          contentStyle={{
            backgroundColor: '#0f172a',
            border: '1px solid #334155',
            borderRadius: 8,
            fontSize: 11,
          }}
        />
        <Scatter data={points} fill={color} fillOpacity={0.55} isAnimationActive={false} />
        {regression && (
          <Line
            data={regression}
            dataKey="y"
            type="linear"
            stroke="#f59e0b"
            strokeWidth={1.5}
            strokeDasharray="6 4"
            dot={false}
            isAnimationActive={false}
          />
        )}
      </ComposedChart>
    </ResponsiveContainer>
  )
}

