import type { Pollutant } from '@/types/api'

export type AqiCategoryName =
  | 'Good'
  | 'Satisfactory'
  | 'Moderate'
  | 'Poor'
  | 'Very Poor'
  | 'Severe'

interface Breakpoint {
  cLow: number
  cHigh: number
  iLow: number
  iHigh: number
}

const BP_PM25_24H: Breakpoint[] = [
  { cLow: 0, cHigh: 30, iLow: 0, iHigh: 50 },
  { cLow: 30, cHigh: 60, iLow: 50, iHigh: 100 },
  { cLow: 60, cHigh: 90, iLow: 100, iHigh: 200 },
  { cLow: 90, cHigh: 120, iLow: 200, iHigh: 300 },
  { cLow: 120, cHigh: 250, iLow: 300, iHigh: 400 },
  { cLow: 250, cHigh: Infinity, iLow: 400, iHigh: 500 },
]

const BP_PM10_24H: Breakpoint[] = [
  { cLow: 0, cHigh: 50, iLow: 0, iHigh: 50 },
  { cLow: 50, cHigh: 100, iLow: 50, iHigh: 100 },
  { cLow: 100, cHigh: 250, iLow: 100, iHigh: 200 },
  { cLow: 250, cHigh: 350, iLow: 200, iHigh: 300 },
  { cLow: 350, cHigh: 430, iLow: 300, iHigh: 400 },
  { cLow: 430, cHigh: Infinity, iLow: 400, iHigh: 500 },
]

const BP_NO2_24H: Breakpoint[] = [
  { cLow: 0, cHigh: 40, iLow: 0, iHigh: 50 },
  { cLow: 40, cHigh: 80, iLow: 50, iHigh: 100 },
  { cLow: 80, cHigh: 180, iLow: 100, iHigh: 200 },
  { cLow: 180, cHigh: 280, iLow: 200, iHigh: 300 },
  { cLow: 280, cHigh: 400, iLow: 300, iHigh: 400 },
  { cLow: 400, cHigh: Infinity, iLow: 400, iHigh: 500 },
]

const BP_SO2_24H: Breakpoint[] = [
  { cLow: 0, cHigh: 40, iLow: 0, iHigh: 50 },
  { cLow: 40, cHigh: 80, iLow: 50, iHigh: 100 },
  { cLow: 80, cHigh: 380, iLow: 100, iHigh: 200 },
  { cLow: 380, cHigh: 800, iLow: 200, iHigh: 300 },
  { cLow: 800, cHigh: 1600, iLow: 300, iHigh: 400 },
  { cLow: 1600, cHigh: Infinity, iLow: 400, iHigh: 500 },
]

const BP_CO8H_MGM3: Breakpoint[] = [
  { cLow: 0, cHigh: 1, iLow: 0, iHigh: 50 },
  { cLow: 1, cHigh: 2, iLow: 50, iHigh: 100 },
  { cLow: 2, cHigh: 10, iLow: 100, iHigh: 200 },
  { cLow: 10, cHigh: 17, iLow: 200, iHigh: 300 },
  { cLow: 17, cHigh: 34, iLow: 300, iHigh: 400 },
  { cLow: 34, cHigh: Infinity, iLow: 400, iHigh: 500 },
]

const BP_O3_8H: Breakpoint[] = [
  { cLow: 0, cHigh: 50, iLow: 0, iHigh: 50 },
  { cLow: 50, cHigh: 100, iLow: 50, iHigh: 100 },
  { cLow: 100, cHigh: 168, iLow: 100, iHigh: 200 },
  { cLow: 168, cHigh: 208, iLow: 200, iHigh: 300 },
  { cLow: 208, cHigh: 748, iLow: 300, iHigh: 400 },
  { cLow: 748, cHigh: Infinity, iLow: 400, iHigh: 500 },
]

const BP_NH3_24H: Breakpoint[] = [
  { cLow: 0, cHigh: 200, iLow: 0, iHigh: 50 },
  { cLow: 200, cHigh: 400, iLow: 50, iHigh: 100 },
  { cLow: 400, cHigh: 800, iLow: 100, iHigh: 200 },
  { cLow: 800, cHigh: 1200, iLow: 200, iHigh: 300 },
  { cLow: 1200, cHigh: 1800, iLow: 300, iHigh: 400 },
  { cLow: 1800, cHigh: Infinity, iLow: 400, iHigh: 500 },
]

export const BREAKPOINTS: Record<Pollutant, Breakpoint[]> = {
  pm25: BP_PM25_24H,
  pm10: BP_PM10_24H,
  no2: BP_NO2_24H,
  so2: BP_SO2_24H,
  co: BP_CO8H_MGM3,
  o3: BP_O3_8H,
  nh3: BP_NH3_24H,
}

export function subIndex(pollutant: Pollutant, concentration: number): number {
  if (!Number.isFinite(concentration) || concentration < 0) return NaN
  const bps = BREAKPOINTS[pollutant]
  for (const bp of bps) {
    if (concentration <= bp.cHigh) {
      const span = bp.cHigh === Infinity ? 1 : bp.cHigh - bp.cLow
      const ratio = (bp.iHigh - bp.iLow) / span
      const idx = Math.round(bp.iLow + ratio * Math.max(0, concentration - bp.cLow))
      return Math.min(500, Math.max(0, idx))
    }
  }
  return NaN
}

export interface OverallAqi {
  aqi: number
  category: AqiCategoryName
  dominantPollutant: Pollutant | null
  subIndices: Partial<Record<Pollutant, number>>
}

export function overallAqi(
  concentrations: Partial<Record<Pollutant, number>>,
): OverallAqi {
  const subIndices: Partial<Record<Pollutant, number>> = {}
  let best: Pollutant | null = null
  let bestVal = -1
  for (const [pollutant, value] of Object.entries(concentrations)) {
    if (typeof value !== 'number' || !Number.isFinite(value)) continue
    const si = subIndex(pollutant as Pollutant, value)
    if (Number.isNaN(si)) continue
    subIndices[pollutant as Pollutant] = si
    if (si > bestVal) {
      bestVal = si
      best = pollutant as Pollutant
    }
  }
  const aqi = Number.isFinite(bestVal) && bestVal >= 0 ? bestVal : NaN
  return { aqi, category: categorize(aqi), dominantPollutant: best, subIndices }
}

export function categorize(aqi: number): AqiCategoryName {
  if (!Number.isFinite(aqi)) return 'Moderate'
  if (aqi <= 50) return 'Good'
  if (aqi <= 100) return 'Satisfactory'
  if (aqi <= 200) return 'Moderate'
  if (aqi <= 300) return 'Poor'
  if (aqi <= 400) return 'Very Poor'
  return 'Severe'
}

export const AqiCategoryColors: Record<AqiCategoryName, string> = {
  Good: '#00b25d',
  Satisfactory: '#92d050',
  Moderate: '#ffd21e',
  Poor: '#f78104',
  'Very Poor': '#e2231a',
  Severe: '#7d2181',
}

export const AqiCategoryTextColor: Record<AqiCategoryName, string> = {
  Good: '#ffffff',
  Satisfactory: '#1a2b12',
  Moderate: '#332b00',
  Poor: '#ffffff',
  'Very Poor': '#ffffff',
  Severe: '#ffffff',
}

export const POLLUTANT_LABELS: Record<Pollutant, string> = {
  pm25: 'PM2.5',
  pm10: 'PM10',
  no2: 'NO₂',
  so2: 'SO₂',
  co: 'CO',
  o3: 'O₃',
  nh3: 'NH₃',
}

export const POLLUTANT_UNITS: Record<Pollutant, string> = {
  pm25: 'µg/m³',
  pm10: 'µg/m³',
  no2: 'µg/m³',
  so2: 'µg/m³',
  co: 'mg/m³',
  o3: 'µg/m³',
  nh3: 'µg/m³',
}

export const ALL_POLLUTANTS: Pollutant[] = ['pm25', 'pm10', 'no2', 'so2', 'co', 'o3']
