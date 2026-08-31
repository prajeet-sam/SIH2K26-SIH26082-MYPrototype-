'use client'

import { LineChart, Line, ResponsiveContainer } from 'recharts'

export function Sparkline({
  data,
  color = '#34d399',
}: {
  data: number[]
  color?: string
}) {
  const points = data.map((v, i) => ({ i, v }))
  return (
    <ResponsiveContainer width="100%" height={30}>
      <LineChart data={points} margin={{ top: 4, right: 0, bottom: 0, left: 0 }}>
        <Line type="monotone" dataKey="v" stroke={color} strokeWidth={1.5} dot={false} isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  )
}
