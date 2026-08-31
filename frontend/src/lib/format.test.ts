import { describe, expect, it } from 'vitest'
import { fmtNum, freshnessLabel } from '@/lib/format'
import { toCsv } from '@/lib/csv'

describe('fmtNum', () => {
  it('formats finite numbers and dashes for missing values', () => {
    expect(fmtNum(12.34)).toBe('12.3')
    expect(fmtNum(null)).toBe('–')
    expect(fmtNum(undefined, 2)).toBe('–')
    expect(fmtNum(Number.NaN)).toBe('–')
  })
})

describe('freshnessLabel', () => {
  it('renders human-readable staleness', () => {
    expect(freshnessLabel(7)).toBe('7 min ago')
    expect(freshnessLabel(90)).toBe('1.5 h ago')
    expect(freshnessLabel(48 * 60)).toBe('2 d ago')
  })
})

describe('toCsv', () => {
  it('joins headers and rows', () => {
    const csv = toCsv([
      { a: 1, b: 'x' },
      { a: 2, b: 'y' },
    ])
    expect(csv.split('\r\n')).toEqual(['a,b', '1,x', '2,y'])
  })

  it('escapes commas and quotes', () => {
    const csv = toCsv([{ text: 'has, comma', quoted: 'say "hi"' }])
    expect(csv).toBe('text,quoted\r\n"has, comma","say ""hi"""')
  })

  it('returns empty string for no rows', () => {
    expect(toCsv([])).toBe('')
  })
})
