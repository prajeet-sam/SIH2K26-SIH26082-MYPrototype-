function escapeCell(value: unknown): string {
  if (value === null || value === undefined) return ''
  const s =
    value instanceof Date ? value.toISOString() : String(value)
  if (/[",\n\r]/.test(s)) {
    return `"${s.replace(/"/g, '""')}"`
  }
  return s
}

export function toCsv(rows: Record<string, unknown>[]): string {
  if (rows.length === 0) return ''
  const headers = Array.from(
    rows.reduce((set, row) => {
      for (const key of Object.keys(row)) set.add(key)
      return set
    }, new Set<string>()),
  )
  const lines = [headers.map(escapeCell).join(',')]
  for (const row of rows) {
    lines.push(headers.map((h) => escapeCell(row[h])).join(','))
  }
  return lines.join('\r\n')
}

export function downloadCsv(filename: string, rows: Record<string, unknown>[]): void {
  const csv = toCsv(rows)
  const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename.endsWith('.csv') ? filename : `${filename}.csv`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
