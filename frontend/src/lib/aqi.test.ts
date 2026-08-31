import { describe, expect, it } from 'vitest'
import { categorize, overallAqi, subIndex } from '@/lib/aqi'

describe('CPCB sub-index', () => {
  it('maps PM2.5 concentrations to expected sub-indices', () => {
    expect(subIndex('pm25', 0)).toBe(0)
    expect(subIndex('pm25', 30)).toBe(50)
    expect(subIndex('pm25', 45)).toBe(75)
    expect(subIndex('pm25', 90)).toBe(200)
    expect(subIndex('pm25', 120)).toBe(300)
    expect(subIndex('pm25', 250)).toBe(400)
    expect(subIndex('pm25', 380)).toBe(500)
  })

  it('clamps beyond the severe ceiling', () => {
    expect(subIndex('pm10', 9999)).toBe(500)
  })

  it('rejects invalid inputs', () => {
    expect(Number.isNaN(subIndex('pm25', -5))).toBe(true)
    expect(Number.isNaN(subIndex('pm25', Number.NaN))).toBe(true)
  })

  it('computes CO sub-index in mg/m³ scale', () => {
    expect(subIndex('co', 0.5)).toBe(25)
    expect(subIndex('co', 2)).toBe(100)
  })
})

describe('overall AQI', () => {
  it('takes the maximum sub-index and reports the dominant pollutant', () => {
    const result = overallAqi({ pm25: 120, no2: 40 })
    expect(result.dominantPollutant).toBe('pm25')
    expect(result.aqi).toBe(300)
    expect(result.category).toBe('Poor')
  })

  it('categorizes boundary values correctly', () => {
    expect(categorize(50)).toBe('Good')
    expect(categorize(51)).toBe('Satisfactory')
    expect(categorize(200)).toBe('Moderate')
    expect(categorize(201)).toBe('Poor')
    expect(categorize(401)).toBe('Severe')
  })

  it('handles missing pollutants gracefully', () => {
    const result = overallAqi({})
    expect(Number.isNaN(result.aqi)).toBe(true)
  })
})
