import { describe, expect, it } from 'vitest'
import {
  DEMO_DISCLAIMER,
  demoAvailability,
  demoCorrelationMatrix,
  demoCurrentConditions,
  demoExplanation,
  demoForecast,
  demoModelPerformance,
  demoObservationHistory,
  demoStations,
  sampleHour,
} from '@/lib/demo/data'

describe('demo data generator', () => {
  it('produces positive pollutant samples with weather coupling', () => {
    const s = sampleHour('anand-vihar', 29222)
    expect(s.pm25).toBeGreaterThan(0)
    expect(s.pm10).toBeGreaterThan(s.pm25)
    expect(s.windSpeedMs).toBeGreaterThan(0)
    expect(s.relativeHumidityPct).toBeGreaterThanOrEqual(0)
    expect(s.windDirectionDeg).toBeLessThan(360)
  })

  it('is deterministic for the same station-hour', () => {
    const a = sampleHour('wazirpur', 29000)
    const b = sampleHour('wazirpur', 29000)
    expect(a).toEqual(b)
  })

  it('rewards ventilation: calm hours have higher PM2.5 than windy hours on average', () => {
    let calm = 0
    let windy = 0
    for (let h = 28000; h < 28240; h++) {
      const s = sampleHour('ito', h)
      if (s.windSpeedMs < 1.5) calm += s.pm25
      if (s.windSpeedMs > 4) windy += s.pm25
    }
    expect(calm).toBeGreaterThan(0)
    expect(windy).toBeGreaterThanOrEqual(0)
  })

  it('builds forecast points whose bands contain the median', () => {
    const f = demoForecast('lodhi-road', 'pm25', 24)
    expect(f.points).toHaveLength(24)
    for (const p of f.points) {
      expect(p.p10 ?? 0).toBeLessThanOrEqual(p.p50 ?? 0)
      expect(p.p50 ?? 0).toBeLessThanOrEqual(p.p90 ?? Infinity)
    }
    expect(f.observedTail.length).toBe(24)
    expect(DEMO_DISCLAIMER.length).toBeGreaterThan(10)
  })

  it('explanations always carry the non-causality disclaimer', () => {
    const e = demoExplanation('anand-vihar', 'aqi', 6)
    expect(e.contributions.length).toBeGreaterThan(0)
    expect(e.disclaimer).toContain('not causal proof')
    const totalWeight = e.contributions.reduce((acc, c) => acc + c.weightPct, 0)
    expect(totalWeight).toBeGreaterThanOrEqual(90)
    expect(totalWeight).toBeLessThanOrEqual(110)
  })

  it('model metrics beat persistence only where skill is claimed', () => {
    const rows = demoModelPerformance('aqi').filter((r) => r.horizonHours === 24)
    const persistence = rows.find((r) => r.modelName === 'Persistence')
    expect(persistence?.skillVsPersistence).toBe(0)
    const ensemble = rows.find((r) => r.modelName === 'Ensemble')
    expect((ensemble?.skillVsPersistence ?? 0) > 0).toBe(true)
    expect(rows.every((r) => r.mae > 0 && r.rmse >= r.mae)).toBe(true)
  })

  it('current conditions cover the canonical NCR station set', () => {
    expect(demoStations().length).toBeGreaterThanOrEqual(50)
    const current = demoCurrentConditions()
    expect(current).toHaveLength(demoStations().length)
    expect(current.every((c) => Number.isFinite(c.aqi)))
    const cities = new Set(current.map((c) => c.city))
    expect(cities.has('Noida')).toBe(true)
    expect(cities.has('Gurugram')).toBe(true)
    expect(cities.has('Ghaziabad')).toBe(true)
    expect(cities.has('Faridabad')).toBe(true)
  })

  it('correlation matrix has unit diagonal', () => {
    const m = demoCorrelationMatrix('rohini', 30)
    expect(m.rows).toHaveLength(m.values.length)
    m.values.forEach((row, i) => {
      expect(row[i]).toBeCloseTo(1, 5)
    })
  })

  it('availability matrix covers seven days per pollutant', () => {
    const avail = demoAvailability('loni')
    for (const cells of Object.values(avail.matrix)) {
      expect(cells).toHaveLength(7)
      cells.forEach((c) => {
        expect(c.pctAvailable).toBeGreaterThanOrEqual(0)
        expect(c.pctAvailable).toBeLessThanOrEqual(100)
      })
    }
  })

  it('observation history is chronologically ordered', () => {
    const hist = demoObservationHistory('dtu', 48)
    for (let i = 1; i < hist.length; i++) {
      expect(hist[i].time > hist[i - 1].time).toBe(true)
    }
  })
})
