'use client'

interface BarItem {
  label: string
  value: number
  color?: string
  suffix?: string
  direction?: 'up' | 'down' | null
}

export function HorizontalBars({
  items,
  max,
}: {
  items: BarItem[]
  max?: number
}) {
  const maxValue = max ?? Math.max(1e-9, ...items.map((i) => Math.abs(i.value)))
  return (
    <ul className="space-y-2">
      {items.map((item) => {
        const widthPct = (Math.abs(item.value) / maxValue) * 100
        const dirColor =
          item.direction === 'up' ? '#ef4444' : item.direction === 'down' ? '#22c55e' : undefined
        const barColor = item.color ?? dirColor ?? '#38bdf8'
        return (
          <li key={item.label} className="text-xs">
            <div className="mb-1 flex items-baseline justify-between gap-2">
              <span className="truncate text-slate-300">{item.label}</span>
              <span className="shrink-0 font-mono text-slate-400">
                {item.value.toFixed(item.suffix === '%' ? 0 : 1)}
                {item.suffix ?? ''}
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-800" role="presentation">
              <div
                className="h-full rounded-full"
                style={{ width: `${widthPct}%`, backgroundColor: barColor }}
              />
            </div>
          </li>
        )
      })}
    </ul>
  )
}
