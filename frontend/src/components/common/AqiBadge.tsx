import clsx from 'clsx'
import { AqiCategoryColors, AqiCategoryTextColor, categorize } from '@/lib/aqi'
import type { AqiCategoryName } from '@/lib/aqi'

interface AqiBadgeProps {
  value: number | null | undefined
  category?: AqiCategoryName
  size?: 'sm' | 'md' | 'lg'
  showValue?: boolean
  className?: string
}

export function AqiBadge({
  value,
  category,
  size = 'md',
  showValue = true,
  className,
}: AqiBadgeProps) {
  const cat = category ?? categorize(value ?? NaN)
  const bg = AqiCategoryColors[cat]
  const fg = AqiCategoryTextColor[cat]
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 rounded-full font-semibold shadow-sm ring-1 ring-inset ring-black/10',
        size === 'sm' && 'px-2 py-0.5 text-[11px]',
        size === 'md' && 'px-2.5 py-1 text-xs',
        size === 'lg' && 'px-3.5 py-1.5 text-sm',
        className,
      )}
      style={{
        backgroundColor: bg,
        color: fg,
        boxShadow: `0 0 0 1px ${bg}55, 0 6px 16px -6px ${bg}aa`,
      }}
      title={`AQI category: ${cat}`}
    >
      <span
        aria-hidden
        className="inline-block h-1.5 w-1.5 rounded-full"
        style={{ backgroundColor: fg, boxShadow: `0 0 6px ${fg}` }}
      />
      {showValue && Number.isFinite(value) ? Math.round(value as number) : ''} {cat}
    </span>
  )
}
