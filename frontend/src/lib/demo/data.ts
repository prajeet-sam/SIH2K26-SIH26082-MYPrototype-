import type {
  AlertContributor,
  AlertItem,
  CityName,
  ConfidenceLevel,
  CorrelationMatrix,
  CurrentConditions,
  DataQualityIncident,
  ExplanationContribution,
  ExplanationResponse,
  ForecastPoint,
  ForecastResponse,
  ForecastTarget,
  GlobalImportanceItem,
  ModelMetricRow,
  ModelName,
  ObservationPoint,
  Pollutant,
  Station,
  StationAvailability,
  WeatherPoint,
} from '@/types/api'
import { ALL_POLLUTANTS, overallAqi } from '@/lib/aqi'

export const DEMO_DISCLAIMER = 'Demo data — not real-time observations.'
export const DEMO_MODEL_NOTICE =
  'Illustrative demo metrics — not produced by trained models yet. Real numbers will appear after training runs populate the registry.'

function hashStr(s: string): number {
  let h = 2166136261
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return h >>> 0
}

function mulberry32(seed: number): () => number {
  let a = seed >>> 0
  return () => {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

export interface RawStationDef {
  slug: string
  name: string
  city: CityName
  lat: number
  lon: number
}

export const STATION_DEFS: RawStationDef[] = [
  { slug: 'anand-vihar', name: 'Anand Vihar', city: 'Delhi', lat: 28.6469, lon: 77.3162 },
  { slug: 'ashok-vihar', name: 'Ashok Vihar', city: 'Delhi', lat: 28.6954, lon: 77.1817 },
  { slug: 'aya-nagar', name: 'Aya Nagar', city: 'Delhi', lat: 28.4706, lon: 77.1099 },
  { slug: 'bawana', name: 'Bawana', city: 'Delhi', lat: 28.7762, lon: 77.0512 },
  { slug: 'burari-crossing', name: 'Burari Crossing', city: 'Delhi', lat: 28.7256, lon: 77.2011 },
  { slug: 'crri-mathura-road', name: 'CRRI Mathura Road', city: 'Delhi', lat: 28.5512, lon: 77.2735 },
  { slug: 'chandni-chowk', name: 'Chandni Chowk', city: 'Delhi', lat: 28.6562, lon: 77.23 },
  { slug: 'dtu', name: 'DTU', city: 'Delhi', lat: 28.75, lon: 77.1112 },
  { slug: 'karni-singh-range', name: 'Dr. Karni Singh Shooting Range', city: 'Delhi', lat: 28.4986, lon: 77.2648 },
  { slug: 'dwarka-sector-8', name: 'Dwarka Sector 8', city: 'Delhi', lat: 28.571, lon: 77.0719 },
  { slug: 'igi-airport-t3', name: 'IGI Airport T3', city: 'Delhi', lat: 28.5628, lon: 77.118 },
  { slug: 'ihbas-dilshad-garden', name: 'IHBAS Dilshad Garden', city: 'Delhi', lat: 28.6811, lon: 77.3025 },
  { slug: 'ito', name: 'ITO', city: 'Delhi', lat: 28.6285, lon: 77.241 },
  { slug: 'jahangirpuri', name: 'Jahangirpuri', city: 'Delhi', lat: 28.7328, lon: 77.1707 },
  { slug: 'jn-stadium', name: 'Jawaharlal Nehru Stadium', city: 'Delhi', lat: 28.58, lon: 77.2337 },
  { slug: 'lodhi-road', name: 'Lodhi Road', city: 'Delhi', lat: 28.5918, lon: 77.2273 },
  { slug: 'dhyan-chand-stadium', name: 'Major Dhyan Chand Stadium', city: 'Delhi', lat: 28.6129, lon: 77.2373 },
  { slug: 'mandir-marg', name: 'Mandir Marg', city: 'Delhi', lat: 28.6365, lon: 77.2011 },
  { slug: 'mundka', name: 'Mundka', city: 'Delhi', lat: 28.6825, lon: 77.0768 },
  { slug: 'najafgarh', name: 'Najafgarh', city: 'Delhi', lat: 28.57, lon: 76.9337 },
  { slug: 'narela', name: 'Narela', city: 'Delhi', lat: 28.8227, lon: 77.1018 },
  { slug: 'nehru-nagar', name: 'Nehru Nagar', city: 'Delhi', lat: 28.5677, lon: 77.2508 },
  { slug: 'new-moti-bagh', name: 'New Moti Bagh', city: 'Delhi', lat: 28.5718, lon: 77.183 },
  { slug: 'north-campus-du', name: 'North Campus DU', city: 'Delhi', lat: 28.6573, lon: 77.1585 },
  { slug: 'nsit-dwarka', name: 'NSIT Dwarka', city: 'Delhi', lat: 28.609, lon: 77.0325 },
  { slug: 'okhla-phase-2', name: 'Okhla Phase-2', city: 'Delhi', lat: 28.5307, lon: 77.2712 },
  { slug: 'patparganj', name: 'Patparganj', city: 'Delhi', lat: 28.6236, lon: 77.2872 },
  { slug: 'punjabi-bagh', name: 'Punjabi Bagh', city: 'Delhi', lat: 28.674, lon: 77.131 },
  { slug: 'pusa', name: 'Pusa', city: 'Delhi', lat: 28.6398, lon: 77.1462 },
  { slug: 'rk-puram', name: 'R K Puram', city: 'Delhi', lat: 28.5646, lon: 77.167 },
  { slug: 'rohini', name: 'Rohini', city: 'Delhi', lat: 28.7325, lon: 77.1198 },
  { slug: 'shadipur', name: 'Shadipur', city: 'Delhi', lat: 28.6514, lon: 77.1473 },
  { slug: 'sirifort', name: 'Sirifort', city: 'Delhi', lat: 28.5504, lon: 77.2159 },
  { slug: 'sonia-vihar', name: 'Sonia Vihar', city: 'Delhi', lat: 28.7106, lon: 77.2497 },
  { slug: 'sri-aurobindo-marg', name: 'Sri Aurobindo Marg', city: 'Delhi', lat: 28.5312, lon: 77.1904 },
  { slug: 'vivek-vihar', name: 'Vivek Vihar', city: 'Delhi', lat: 28.6725, lon: 77.3153 },
  { slug: 'wazirpur', name: 'Wazirpur', city: 'Delhi', lat: 28.6997, lon: 77.1653 },
  { slug: 'noida-sector-116', name: 'Noida Sector 116', city: 'Noida', lat: 28.5833, lon: 77.34 },
  { slug: 'noida-sector-125', name: 'Noida Sector 125', city: 'Noida', lat: 28.545, lon: 77.333 },
  { slug: 'noida-sector-1', name: 'Noida Sector 1', city: 'Noida', lat: 28.571, lon: 77.326 },
  { slug: 'knowledge-park-v', name: 'Knowledge Park V', city: 'Greater Noida', lat: 28.475, lon: 77.503 },
  { slug: 'indirapuram', name: 'Indirapuram', city: 'Ghaziabad', lat: 28.646, lon: 77.356 },
  { slug: 'loni', name: 'Loni', city: 'Ghaziabad', lat: 28.751, lon: 77.271 },
  { slug: 'sanjay-nagar', name: 'Sanjay Nagar', city: 'Ghaziabad', lat: 28.672, lon: 77.42 },
  { slug: 'vasundhara', name: 'Vasundhara', city: 'Ghaziabad', lat: 28.66, lon: 77.372 },
  { slug: 'gwal-pahari', name: 'Gwal Pahari', city: 'Gurugram', lat: 28.394, lon: 77.156 },
  { slug: 'gurugram-sector-51', name: 'Gurugram Sector 51', city: 'Gurugram', lat: 28.42, lon: 77.065 },
  { slug: 'vikas-sadan', name: 'Vikas Sadan', city: 'Gurugram', lat: 28.459, lon: 77.023 },
  { slug: 'teri-gram', name: 'Teri Gram', city: 'Gurugram', lat: 28.409, lon: 77.15 },
  { slug: 'faridabad-sector-11', name: 'Faridabad Sector 11', city: 'Faridabad', lat: 28.365, lon: 77.316 },
  { slug: 'faridabad-sector-16a', name: 'Faridabad Sector 16A', city: 'Faridabad', lat: 28.334, lon: 77.291 },
  { slug: 'nit-faridabad', name: 'NIT Faridabad', city: 'Faridabad', lat: 28.313, lon: 77.287 },
  { slug: 'bahadurgarh', name: 'Bahadurgarh', city: 'Other NCR', lat: 28.693, lon: 76.938 },
  { slug: 'ballabgarh', name: 'Ballabgarh', city: 'Other NCR', lat: 28.339, lon: 77.305 },
]

const CITY_FACTOR: Record<CityName, number> = {
  Delhi: 1,
  Noida: 0.96,
  'Greater Noida': 0.9,
  Ghaziabad: 1.03,
  Gurugram: 0.93,
  Faridabad: 0.99,
  'Other NCR': 0.86,
}

const HOTSPOT_FACTOR: Record<string, number> = {
  'anand-vihar': 1.42,
  wazirpur: 1.38,
  bawana: 1.33,
  mundka: 1.36,
  jahangirpuri: 1.27,
  narela: 1.22,
  rohini: 1.12,
  'burari-crossing': 1.15,
  'sonia-vihar': 1.08,
  indirapuram: 1.16,
  vasundhara: 1.1,
  loni: 1.14,
  'okhla-phase-2': 1.12,
  'patparganj': 1.06,
  ito: 1.18,
  'chandni-chowk': 1.14,
  'lodhi-road': 0.82,
  'aya-nagar': 0.85,
  'gwal-pahari': 0.78,
  'teri-gram': 0.8,
  'nsit-dwarka': 0.88,
  'najafgarh': 0.87,
}

const HOUR_MS = 3600000

export interface HourSample {
  hourIndex: number
  pm25: number
  pm10: number
  no2: number
  so2: number
  co: number
  o3: number
  temperatureC: number
  relativeHumidityPct: number
  windSpeedMs: number
  windDirectionDeg: number
  precipitationMm: number
  pressureHpa: number
}

const sampleCache = new Map<string, HourSample>()

function monthFactor(month: number): number {
  switch (month) {
    case 0:
    case 1:
      return 2.1
    case 9:
      return 1.35
    case 10:
      return 2.3
    case 11:
      return 2.2
    case 2:
      return 1.4
    case 3:
      return 1.1
    case 5:
    case 6:
    case 7:
      return 0.62
    case 8:
      return 0.68
    default:
      return 0.9
  }
}

function diurnalFactor(hour: number): number {
  const morningPeak = Math.exp(-((hour - 8.5) ** 2) / 6)
  const nightPeak = Math.exp(-((hour - 22.5) ** 2) / 10)
  const afternoonDip = Math.exp(-((hour - 15) ** 2) / 8)
  return 1 + 0.38 * morningPeak + 0.42 * nightPeak - 0.3 * afternoonDip
}

export function sampleHour(slug: string, hourIndex: number): HourSample {
  const key = `${slug}:${hourIndex}`
  const cached = sampleCache.get(key)
  if (cached) return cached
  if (sampleCache.size > 20000) sampleCache.clear()

  const def = STATION_DEFS.find((d) => d.slug === slug)
  const city: CityName = def?.city ?? 'Delhi'
  const hotspot = HOTSPOT_FACTOR[slug] ?? 1

  const rngW = mulberry32(hashStr(`${slug}:w:${hourIndex}`))
  const rngP = mulberry32(hashStr(`${slug}:p:${hourIndex}`))
  const date = new Date(hourIndex * HOUR_MS)
  const hod = date.getUTCHours() + 5.5 >= 24 ? date.getUTCHours() - 18.5 : date.getUTCHours() + 5.5
  const month = date.getUTCMonth()

  let rainRecent = 0
  for (let k = 1; k <= 8; k++) {
    const prev = mulberry32(hashStr(`${slug}:w:${hourIndex - k}`))()
    if (prev < 0.07) rainRecent += 1
  }

  const calmNight = hod >= 22 || hod <= 6 ? 0.55 : 1
  const gustyDay = hod >= 12 && hod <= 17 ? 1.35 : 1
  const windSpeedMs = Math.max(
    0.3,
    2.9 * calmNight * gustyDay * monthFactor(month) ** 0.25 * (0.6 + rngW() * 0.9),
  )
  const temperatureC =
    31 - 4 * monthFactor(month) ** 0.3 + 6.5 * Math.sin(((hod - 14) / 24) * 2 * Math.PI) + (rngW() - 0.5) * 3
  const relativeHumidityPct = Math.min(
    98,
    Math.max(22, 74 - (temperatureC - 29) * 3.2 + (rngW() - 0.5) * 14 + (rainRecent > 0 ? 10 : 0)),
  )
  const rainRoll = rngW()
  const precipitationMm = rainRoll < 0.07 && month >= 5 && month <= 8 ? 2 + rngW() * 14 : 0
  const windDirectionDeg = (295 + 70 * Math.sin(hourIndex / 41) + (rngW() - 0.5) * 50 + 360) % 360
  const pressureHpa = 1006 + 3 * Math.sin(hourIndex / 120) + (rngW() - 0.5) * 4

  const washout = 1 - 0.035 * Math.min(rainRecent, 8)
  const ventilation = Math.max(0.45, 1.45 - 0.22 * windSpeedMs)
  const moisture = 0.9 + ((relativeHumidityPct - 55) / 100) * 0.35

  const base =
    52 *
    (CITY_FACTOR[city] ?? 1) *
    hotspot *
    monthFactor(month) *
    diurnalFactor(hod) *
    ventilation *
    moisture *
    washout

  const traffic = 1 + 0.3 * (Math.exp(-((hod - 9) ** 2) / 4) + Math.exp(-((hod - 20) ** 2) / 5))

  const pm25 = Math.max(6, base * (0.85 + rngP() * 0.3))
  const pm10 = Math.max(12, pm25 * (1.55 + rngP() * 0.4) + 12)
  const no2 = Math.max(5, 34 * (CITY_FACTOR[city] ?? 1) * hotspot * traffic * (1.25 - 0.09 * windSpeedMs) * (0.8 + rngP() * 0.4))
  const so2 = Math.max(2, 11 * (CITY_FACTOR[city] ?? 1) * hotspot * (0.7 + rngP() * 0.6))
  const co = Math.max(0.2, 1.05 * traffic * (CITY_FACTOR[city] ?? 1) * (0.7 + rngP() * 0.6))
  const photo = Math.max(0, Math.sin(((hod - 13) / 9.5) * Math.PI))
  const o3 = Math.max(6, (18 + 62 * photo) * (0.85 + rngP() * 0.3))

  const sample: HourSample = {
    hourIndex,
    pm25: round1(pm25),
    pm10: round1(pm10),
    no2: round1(no2),
    so2: round1(so2),
    co: Math.round(co * 100) / 100,
    o3: round1(o3),
    temperatureC: round1(temperatureC),
    relativeHumidityPct: Math.round(relativeHumidityPct),
    windSpeedMs: round1(windSpeedMs),
    windDirectionDeg: Math.round(windDirectionDeg),
    precipitationMm: round1(precipitationMm),
    pressureHpa: round1(pressureHpa),
  }
  sampleCache.set(key, sample)
  return sample
}

function round1(v: number): number {
  return Math.round(v * 10) / 10
}

function currentHourIndex(): number {
  return Math.floor(Date.now() / HOUR_MS)
}

export function pollutantsOf(s: HourSample): Partial<Record<Pollutant, number>> {
  return { pm25: s.pm25, pm10: s.pm10, no2: s.no2, so2: s.so2, co: s.co, o3: s.o3 }
}

export function aqiOfSample(s: HourSample): {
  aqi: number
  category: ReturnType<typeof overallAqi>['category']
  dominant: Pollutant
} {
  const overall = overallAqi(pollutantsOf(s))
  return { aqi: overall.aqi, category: overall.category, dominant: overall.dominantPollutant ?? 'pm25' }
}

let stationsCache: Station[] | null = null

export function demoStations(): Station[] {
  if (stationsCache) return stationsCache
  stationsCache = STATION_DEFS.map((def, i) => ({
    id: `demo-st-${String(i + 1).padStart(3, '0')}`,
    slug: def.slug,
    name: def.name,
    city: def.city,
    latitude: def.lat,
    longitude: def.lon,
    pollutantsAvailable: ALL_POLLUTANTS,
    isActive: true,
  }))
  return stationsCache
}

export function demoCurrentConditions(): CurrentConditions[] {
  const now = currentHourIndex()
  return STATION_DEFS.map((def, i) => {
    const s = sampleHour(def.slug, now)
    const { aqi, category, dominant } = aqiOfSample(s)
    const trend24hAqi: number[] = []
    for (let k = 24; k >= 1; k--) {
      trend24hAqi.push(aqiOfSample(sampleHour(def.slug, now - k)).aqi)
    }
    return {
      stationId: `demo-st-${String(i + 1).padStart(3, '0')}`,
      slug: def.slug,
      name: def.name,
      city: def.city,
      latitude: def.lat,
      longitude: def.lon,
      observedAt: new Date(now * HOUR_MS).toISOString(),
      aqi,
      category,
      dominantPollutant: dominant,
      pollutants: pollutantsOf(s),
      weather: {
        temperatureC: s.temperatureC,
        relativeHumidityPct: s.relativeHumidityPct,
        windSpeedMs: s.windSpeedMs,
        windDirectionDeg: s.windDirectionDeg,
        precipitationMm: s.precipitationMm,
      },
      freshnessMinutes: 4 + (hashStr(def.slug) % 16),
      trend24hAqi,
    }
  })
}

export function demoObservationHistory(slug: string, tailHours: number): ObservationPoint[] {
  const now = currentHourIndex()
  const out: ObservationPoint[] = []
  for (let k = tailHours; k >= 1; k--) {
    const s = sampleHour(slug, now - k)
    const flag = hashStr(`${slug}:q:${now - k}`) % 37 === 0 ? 'interpolated' : 'cleaned'
    out.push({
      time: new Date((now - k) * HOUR_MS).toISOString(),
      aqi: aqiOfSample(s).aqi,
      pollutants: pollutantsOf(s),
      qualityFlag: flag,
    })
  }
  return out
}

export function demoWeatherHistory(slug: string, tailHours: number): WeatherPoint[] {
  const now = currentHourIndex()
  const out: WeatherPoint[] = []
  for (let k = tailHours; k >= 1; k--) {
    const s = sampleHour(slug, now - k)
    out.push(weatherPointOf(s, (now - k) * HOUR_MS))
  }
  return out
}

function weatherPointOf(s: HourSample, ms: number): WeatherPoint {
  return {
    time: new Date(ms).toISOString(),
    temperatureC: s.temperatureC,
    relativeHumidityPct: s.relativeHumidityPct,
    windSpeedMs: s.windSpeedMs,
    windDirectionDeg: s.windDirectionDeg,
    precipitationMm: s.precipitationMm,
    pressureHpa: s.pressureHpa,
  }
}

export function demoWeatherForecast(slug: string, aheadHours: number): WeatherPoint[] {
  const now = currentHourIndex()
  const out: WeatherPoint[] = []
  for (let h = 1; h <= aheadHours; h++) {
    out.push(weatherPointOf(sampleHour(slug, now + h), (now + h) * HOUR_MS))
  }
  return out
}

export function valueForTarget(target: ForecastTarget, pollutants: Partial<Record<Pollutant, number>>): number {
  if (target === 'pm25') return pollutants.pm25 ?? NaN
  if (target === 'pm10') return pollutants.pm10 ?? NaN
  return overallAqi(pollutants).aqi
}

export function demoForecast(slug: string, target: ForecastTarget, horizonHours: number): ForecastResponse {
  const station = STATION_DEFS.find((d) => d.slug === slug) ?? STATION_DEFS[0]
  const now = currentHourIndex()
  const observedTail = demoObservationHistory(slug, 24)
  const points: ForecastPoint[] = []
  for (let h = 1; h <= horizonHours; h++) {
    const future = sampleHour(slug, now + h)
    const truth = valueForTarget(target, pollutantsOf(future))
    const bias = 1 + ((hashStr(`${slug}:${target}:${h}`) % 9) - 4) / 100
    const p50 = Math.max(1, truth * bias)
    const spreadPct = 0.06 + 0.0042 * h
    const half = Math.max(3, p50 * spreadPct)
    const confidence: ConfidenceLevel = h <= 6 ? 'high' : h <= 24 ? 'moderate' : 'low'
    points.push({
      targetTime: new Date((now + h) * HOUR_MS).toISOString(),
      horizonHours: h,
      p10: round1(Math.max(0, p50 - half)),
      p50: round1(p50),
      p90: round1(p50 + half),
      confidence,
    })
  }
  return {
    stationId: `demo-${station.slug}`,
    stationName: station.name,
    target,
    issuedAt: new Date(now * HOUR_MS).toISOString(),
    modelRunId: 'demo-run-0000',
    featureSetVersion: 'demo-features-v0',
    observedTail,
    weatherTail: demoWeatherHistory(slug, 24),
    weatherForecast: demoWeatherForecast(slug, horizonHours),
    points,
  }
}

const BASE_METRICS: Record<ModelName, { mae: number; rmse: number; r2: number }> = {
  Persistence: { mae: 21.4, rmse: 32.8, r2: 0.71 },
  'Seasonal Naive': { mae: 20.2, rmse: 31.2, r2: 0.73 },
  'Rolling Mean 24h': { mae: 19.8, rmse: 30.1, r2: 0.74 },
  'Ridge Regression': { mae: 18.2, rmse: 27.9, r2: 0.77 },
  'Random Forest': { mae: 16.7, rmse: 25.3, r2: 0.81 },
  XGBoost: { mae: 14.9, rmse: 22.1, r2: 0.85 },
  LightGBM: { mae: 15.2, rmse: 22.6, r2: 0.845 },
  LSTM: { mae: 13.8, rmse: 20.6, r2: 0.87 },
  Ensemble: { mae: 12.9, rmse: 19.4, r2: 0.88 },
}

export const EVAL_HORIZONS = [1, 3, 6, 12, 24, 48] as const

export function demoModelPerformance(target: ForecastTarget = 'aqi'): ModelMetricRow[] {
  const targetFactor = target === 'pm10' ? 1.15 : target === 'pm25' ? 1.02 : 1
  const rows: ModelMetricRow[] = []
  for (const [modelName, base] of Object.entries(BASE_METRICS) as [ModelName, typeof BASE_METRICS[ModelName]][]) {
    for (const h of EVAL_HORIZONS) {
      const hf = h <= 6 ? 0.72 : h === 12 ? 0.84 : h === 24 ? 1 : h === 48 ? 1.28 : 1.1
      const mae = round1(base.mae * targetFactor * hf)
      const rmse = round1(base.rmse * targetFactor * hf)
      const r2 = Math.max(0.3, Math.min(0.93, base.r2 - (hf - 1) * 0.35))
      const persistenceMae = BASE_METRICS.Persistence.mae * targetFactor * hf
      rows.push({
        modelName,
        target,
        horizonHours: h,
        mae,
        rmse,
        mape: Math.round((14 + (modelName === 'Persistence' ? 6 : 0) - (r2 - 0.7) * 20) * 10) / 10,
        r2: Math.round(r2 * 100) / 100,
        skillVsPersistence: Math.round((1 - mae / persistenceMae) * 100) / 100,
        picp80:
          modelName === 'XGBoost' || modelName === 'Ensemble' || modelName === 'LightGBM'
            ? 0.78 + ((hashStr(modelName) % 7) - 3) / 100
            : null,
        pinaw80: modelName === 'Ensemble' ? 0.34 : modelName === 'XGBoost' ? 0.36 : null,
        modelRunId: 'demo-run-0000',
      })
    }
  }
  return rows
}

export function demoGlobalImportance(): GlobalImportanceItem[] {
  return [
    { featureLabel: 'PM2.5 lag 1h', importancePct: 21.4, family: 'pollution-history' },
    { featureLabel: 'PM2.5 rolling mean 6h', importancePct: 12.8, family: 'pollution-history' },
    { featureLabel: 'Wind speed (u-component)', importancePct: 10.2, family: 'weather' },
    { featureLabel: 'Relative humidity lag 3h', importancePct: 8.6, family: 'weather' },
    { featureLabel: 'PM2.5 lag 24h', importancePct: 8.1, family: 'pollution-history' },
    { featureLabel: 'Stagnation flag (calm+dry+night)', importancePct: 7.4, family: 'weather' },
    { featureLabel: 'Hour of day (sin/cos)', importancePct: 6.9, family: 'temporal' },
    { featureLabel: 'Temperature change 24h', importancePct: 5.8, family: 'weather' },
    { featureLabel: 'Upwind neighbour PM2.5 lag 3h', importancePct: 5.2, family: 'spatial' },
    { featureLabel: 'Rainfall sum 24h', importancePct: 4.7, family: 'weather' },
    { featureLabel: 'Season (winter indicator)', importancePct: 4.1, family: 'temporal' },
    { featureLabel: 'Wind speed × PM2.5 lag 1h', importancePct: 3.3, family: 'interaction' },
  ]
}

export function demoCorrelationMatrix(slug: string, days: number): CorrelationMatrix {
  const vars = [
    'PM2.5',
    'PM10',
    'NO₂',
    'O₃',
    'Temp',
    'RH',
    'Wind',
    'Rain',
  ] as const
  const now = currentHourIndex()
  const n = Math.min(days * 24, 24 * 30)
  const series: number[][] = vars.map(() => [])
  for (let k = n; k >= 1; k--) {
    const s = sampleHour(slug, now - k)
    series[0].push(s.pm25)
    series[1].push(s.pm10)
    series[2].push(s.no2)
    series[3].push(s.o3)
    series[4].push(s.temperatureC)
    series[5].push(s.relativeHumidityPct)
    series[6].push(s.windSpeedMs)
    series[7].push(s.precipitationMm)
  }
  const pearson = (a: number[], b: number[]): number => {
    const ma = a.reduce((x, y) => x + y, 0) / a.length
    const mb = b.reduce((x, y) => x + y, 0) / b.length
    let num = 0
    let da = 0
    let dbb = 0
    for (let i = 0; i < a.length; i++) {
      num += (a[i] - ma) * (b[i] - mb)
      da += (a[i] - ma) ** 2
      dbb += (b[i] - mb) ** 2
    }
    const den = Math.sqrt(da * dbb)
    return den === 0 ? 0 : Math.round((num / den) * 100) / 100
  }
  const values = series.map((row) => series.map((col) => pearson(row, col)))
  return { rows: [...vars], cols: [...vars], values }
}

export function demoAvailability(slug: string): StationAvailability {
  const now = currentHourIndex()
  const days = 7
  const matrix = {} as StationAvailability['matrix']
  for (const p of ALL_POLLUTANTS) {
    const cells = []
    for (let d = days - 1; d >= 0; d--) {
      const r = mulberry32(hashStr(`${slug}:${p}:${now - d * 24}`))()
      cells.push({
        dayIso: new Date((now - d * 24) * HOUR_MS).toISOString().slice(0, 10),
        pctAvailable: Math.round(58 + r * 42),
      })
    }
    matrix[p] = cells
  }
  return { slug, matrix }
}

export function demoExplanation(
  slug: string,
  target: ForecastTarget,
  horizonHours: number,
): ExplanationResponse {
  const station = STATION_DEFS.find((d) => d.slug === slug) ?? STATION_DEFS[0]
  const now = currentHourIndex()
  const latest = sampleHour(slug, now)
  const upcoming = sampleHour(slug, now + horizonHours)
  const raw: Array<Omit<ExplanationContribution, 'weightPct'> & { weight: number }> = []
  if (latest.windSpeedMs < 2.0) {
    raw.push({ featureLabel: 'Wind speed', direction: 'up', weight: 26 + (hashStr(slug) % 6), phrase: 'low wind speed reducing horizontal dispersion' })
  } else if (latest.windSpeedMs > 4.5) {
    raw.push({ featureLabel: 'Wind speed', direction: 'down', weight: 18, phrase: 'brisk winds improving dispersion' })
  }
  if (latest.relativeHumidityPct > 72) {
    raw.push({ featureLabel: 'Relative humidity', direction: 'up', weight: 19, phrase: 'high humidity favouring hygroscopic growth of aerosols' })
  }
  const recentLevel = valueForTarget(target, pollutantsOf(latest))
  if (recentLevel > 100) {
    raw.push({ featureLabel: `Historical ${target.toUpperCase()} level`, direction: 'up', weight: 24, phrase: 'elevated pollution levels over the past several hours' })
  }
  if (upcoming.precipitationMm === 0 && latest.precipitationMm === 0) {
    raw.push({ featureLabel: 'Expected rainfall', direction: 'up', weight: 13, phrase: 'no rainfall expected to wash out particulates' })
  }
  const hod = new Date((now + horizonHours) * HOUR_MS).getUTCHours()
  if (hod >= 20 || hod <= 7) {
    raw.push({ featureLabel: 'Time of day', direction: 'up', weight: 10, phrase: 'night-time accumulation window with shallow mixing' })
  } else {
    raw.push({ featureLabel: 'Time of day', direction: 'down', weight: 8, phrase: 'daytime boundary-layer mixing helping dispersion' })
  }
  if (latest.windSpeedMs < 1.8 && latest.relativeHumidityPct > 65 && upcoming.precipitationMm === 0) {
    raw.push({ featureLabel: 'Atmospheric stagnation', direction: 'up', weight: 15, phrase: 'stable atmospheric conditions trapping emissions near the surface' })
  }

  const totalWeight = raw.reduce((acc, c) => acc + c.weight, 0) || 1
  const contributions: ExplanationContribution[] = raw
    .sort((a, b) => b.weight - a.weight)
    .map((c) => ({
      featureLabel: c.featureLabel,
      direction: c.direction,
      weightPct: Math.round((c.weight / totalWeight) * 100),
      phrase: c.phrase,
    }))

  const forecastValue = valueForTarget(
    target,
    pollutantsOf(upcoming),
  )
  const levelWord =
    forecastValue > 250 ? 'Very high' : forecastValue > 150 ? 'High' : forecastValue > 90 ? 'Elevated' : 'Moderate'
  const narrative = `${levelWord} ${target.toUpperCase()} expected at ${station.name} in ~${horizonHours} h. Top model-derived drivers: ${contributions
    .slice(0, 3)
    .map((c) => c.phrase)
    .join('; ')}.`

  return {
    stationId: `demo-${slug}`,
    stationName: station.name,
    target,
    generatedAt: new Date(now * HOUR_MS).toISOString(),
    narrative,
    disclaimer: `${DEMO_MODEL_NOTICE}. Explanations are model-derived associations, not causal proof.`,
    confidence: horizonHours <= 6 ? 'high' : horizonHours <= 24 ? 'moderate' : 'low',
    contributions,
  }
}

export function demoAlerts(): AlertItem[] {
  const now = currentHourIndex()
  const iso = (offsetH: number) => new Date((now - offsetH) * HOUR_MS).toISOString()
  const contributors = (...items: Array<[string, 'up' | 'down']>): AlertContributor[] =>
    items.map(([label, direction]) => ({ label, direction }))
  return [
    {
      id: 'demo-alert-001',
      alertType: 'rapid-rise',
      severity: 'critical',
      stationSlug: 'anand-vihar',
      stationName: 'Anand Vihar',
      city: 'Delhi',
      triggeredAt: iso(1),
      observedOrForecast: 'forecast',
      message: 'PM2.5 expected to rise sharply within the next 6 h at Anand Vihar.',
      context: { value: 168, threshold: 140, horizonHours: 6, contributors: contributors(['Low wind speed', 'up'], ['High humidity', 'up'], ['Elevated evening PM2.5', 'up'], ['No expected rainfall', 'up']) },
      resolvedAt: null,
    },
    {
      id: 'demo-alert-002',
      alertType: 'threshold-crossing',
      severity: 'warning',
      stationSlug: 'wazirpur',
      stationName: 'Wazirpur',
      city: 'Delhi',
      triggeredAt: iso(2),
      observedOrForecast: 'observed',
      message: 'AQI entered the Poor category at Wazirpur.',
      context: { value: 264, threshold: 200, horizonHours: null, contributors: contributors(['Industrial corridor emissions proxy', 'up'], ['Calm winds', 'up']) },
      resolvedAt: null,
    },
    {
      id: 'demo-alert-003',
      alertType: 'stagnation-advisory',
      severity: 'info',
      stationSlug: null,
      stationName: null,
      city: 'Delhi',
      triggeredAt: iso(3),
      observedOrForecast: 'forecast',
      message: 'Atmospheric stagnation conditions expected overnight across central-north Delhi.',
      context: { value: null, threshold: null, horizonHours: 12, contributors: contributors(['Wind speed below 1.5 m/s', 'up'], ['No rainfall 24h', 'up'], ['Night window', 'up']) },
      resolvedAt: null,
    },
    {
      id: 'demo-alert-101',
      alertType: 'threshold-crossing',
      severity: 'warning',
      stationSlug: 'vasundhara',
      stationName: 'Vasundhara',
      city: 'Ghaziabad',
      triggeredAt: iso(28),
      observedOrForecast: 'observed',
      message: 'AQI crossed Moderate into Poor at Vasundhara (resolved).',
      context: { value: 213, threshold: 200, horizonHours: null, contributors: contributors(['Traffic peak', 'up']) },
      resolvedAt: iso(20),
    },
    {
      id: 'demo-alert-102',
      alertType: 'data-outage',
      severity: 'warning',
      stationSlug: 'noida-sector-116',
      stationName: 'Noida Sector 116',
      city: 'Noida',
      triggeredAt: iso(31),
      observedOrForecast: 'observed',
      message: 'No observations received for more than 2 h (resolved).',
      context: { value: null, threshold: null, horizonHours: null, contributors: [] },
      resolvedAt: iso(26),
    },
    {
      id: 'demo-alert-103',
      alertType: 'extreme-forecast',
      severity: 'critical',
      stationSlug: 'bawana',
      stationName: 'Bawana',
      city: 'Delhi',
      triggeredAt: iso(52),
      observedOrForecast: 'forecast',
      message: 'Severe-category PM2.5 forecast at Bawana (resolved after winds picked up).',
      context: { value: 412, threshold: 380, horizonHours: 12, contributors: contributors(['Stagnation', 'up'], ['Elevated base level', 'up']) },
      resolvedAt: iso(44),
    },
    {
      id: 'demo-alert-104',
      alertType: 'rapid-rise',
      severity: 'info',
      stationSlug: 'ito',
      stationName: 'ITO',
      city: 'Delhi',
      triggeredAt: iso(75),
      observedOrForecast: 'observed',
      message: 'Rapid PM2.5 increase during morning traffic peak at ITO (resolved).',
      context: { value: 142, threshold: 120, horizonHours: null, contributors: contributors(['Morning rush', 'up'], ['Moderate wind', 'down']) },
      resolvedAt: iso(70),
    },
    {
      id: 'demo-alert-105',
      alertType: 'threshold-crossing',
      severity: 'info',
      stationSlug: 'lodhi-road',
      stationName: 'Lodhi Road',
      city: 'Delhi',
      triggeredAt: iso(97),
      observedOrForecast: 'observed',
      message: 'AQI improved into Satisfactory range after showers (resolved).',
      context: { value: 84, threshold: 100, horizonHours: null, contributors: contributors(['Rainfall washout', 'down']) },
      resolvedAt: iso(94),
    },
  ]
}

export function demoDataQualityIncidents(): DataQualityIncident[] {
  const now = currentHourIndex()
  const iso = (offsetH: number) => new Date((now - offsetH) * HOUR_MS).toISOString()
  return [
    { id: 'dq-1', stationSlug: 'noida-sector-116', checkType: 'station-outage', severity: 'critical', detectedAt: iso(2), resolvedAt: null, detail: 'No observations received for >2 h from primary provider.' },
    { id: 'dq-2', stationSlug: 'loni', checkType: 'frozen-values', severity: 'warning', detectedAt: iso(9), resolvedAt: iso(5), detail: 'Identical PM10 readings repeated for 6 consecutive hours.' },
    { id: 'dq-3', stationSlug: 'vivek-vihar', checkType: 'sensor-spike', severity: 'info', detectedAt: iso(14), resolvedAt: iso(14), detail: 'Single-hour PM2.5 spike >6×MAD rejected and flagged suspect.' },
    { id: 'dq-4', stationSlug: null, checkType: 'provider-delay', severity: 'info', detectedAt: iso(1), resolvedAt: null, detail: 'Primary provider feed delayed by 22 min; fallback provider used.' },
    { id: 'dq-5', stationSlug: 'bahadurgarh', checkType: 'high-gap-rate', severity: 'warning', detectedAt: iso(30), resolvedAt: null, detail: 'Gap rate 18% over trailing 24 h; interpolation flags increased.' },
  ]
}
