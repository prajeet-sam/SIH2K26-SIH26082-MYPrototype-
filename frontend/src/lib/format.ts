const IST = 'Asia/Kolkata'

export function istDateTime(iso: string | Date): string {
  const d = typeof iso === 'string' ? new Date(iso) : iso
  if (Number.isNaN(d.getTime())) return '–'
  return new Intl.DateTimeFormat('en-IN', {
    timeZone: IST,
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(d)
}

export function istTime(iso: string | Date): string {
  const d = typeof iso === 'string' ? new Date(iso) : iso
  if (Number.isNaN(d.getTime())) return '–'
  return new Intl.DateTimeFormat('en-IN', {
    timeZone: IST,
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(d)
}

export function istDayLabel(iso: string | Date): string {
  const d = typeof iso === 'string' ? new Date(iso) : iso
  if (Number.isNaN(d.getTime())) return '–'
  return new Intl.DateTimeFormat('en-IN', {
    timeZone: IST,
    day: '2-digit',
    month: 'short',
  }).format(d)
}

export function fmtNum(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return '–'
  return value.toFixed(digits)
}

export function fmtPct(fraction: number | null | undefined, digits = 0): string {
  if (fraction === null || fraction === undefined || !Number.isFinite(fraction))
    return '–'
  return `${(fraction * 100).toFixed(digits)}%`
}

export function freshnessLabel(minutes: number): string {
  if (!Number.isFinite(minutes)) return 'unknown'
  if (minutes < 60) return `${Math.round(minutes)} min ago`
  const hours = minutes / 60
  if (hours < 24) return `${hours.toFixed(hours < 10 ? 1 : 0)} h ago`
  return `${Math.round(hours / 24)} d ago`
}

export function toIsoHourly(date: Date): string {
  return date.toISOString().slice(0, 13) + ':00:00Z'
}
