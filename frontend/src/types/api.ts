import type { AqiCategoryName } from '@/lib/aqi'

export type Pollutant = 'pm25' | 'pm10' | 'no2' | 'so2' | 'co' | 'o3' | 'nh3'

export type CityName =
  | 'Delhi'
  | 'Noida'
  | 'Greater Noida'
  | 'Ghaziabad'
  | 'Gurugram'
  | 'Faridabad'
  | 'Other NCR'

export type QualityFlag = 'raw' | 'cleaned' | 'interpolated' | 'suspect'

export type DataSourceKind = 'live' | 'demo'

export interface Station {
  id: string
  slug: string
  name: string
  city: CityName
  latitude: number
  longitude: number
  pollutantsAvailable: Pollutant[]
  isActive: boolean
}

export interface CurrentConditions {
  stationId: string
  slug: string
  name: string
  city: CityName
  latitude: number
  longitude: number
  observedAt: string
  aqi: number
  category: AqiCategoryName
  dominantPollutant: Pollutant
  pollutants: Partial<Record<Pollutant, number>>
  weather: {
    temperatureC: number | null
    relativeHumidityPct: number | null
    windSpeedMs: number | null
    windDirectionDeg: number | null
    precipitationMm: number | null
  }
  freshnessMinutes: number
  trend24hAqi: number[]
}

export interface ObservationPoint {
  time: string
  aqi: number
  pollutants: Partial<Record<Pollutant, number>>
  qualityFlag: QualityFlag
}

export interface WeatherPoint {
  time: string
  temperatureC: number | null
  relativeHumidityPct: number | null
  windSpeedMs: number | null
  windDirectionDeg: number | null
  precipitationMm: number | null
  pressureHpa: number | null
}

export type ForecastTarget = 'aqi' | 'pm25' | 'pm10'

export type ConfidenceLevel = 'high' | 'moderate' | 'low'

export interface ForecastPoint {
  targetTime: string
  horizonHours: number
  p10: number | null
  p50: number | null
  p90: number | null
  confidence: ConfidenceLevel
}

export interface ForecastResponse {
  stationId: string
  stationName: string
  target: ForecastTarget
  issuedAt: string
  modelRunId: string
  featureSetVersion: string
  observedTail: ObservationPoint[]
  weatherTail: WeatherPoint[]
  weatherForecast: WeatherPoint[]
  points: ForecastPoint[]
}

export interface ExplanationContribution {
  featureLabel: string
  direction: 'up' | 'down'
  weightPct: number
  phrase: string
}

export interface ExplanationResponse {
  stationId: string
  stationName: string
  target: ForecastTarget
  generatedAt: string
  narrative: string
  disclaimer: string
  confidence: ConfidenceLevel
  contributions: ExplanationContribution[]
}

export type ModelName =
  | 'Persistence'
  | 'Seasonal Naive'
  | 'Rolling Mean 24h'
  | 'Ridge Regression'
  | 'Random Forest'
  | 'XGBoost'
  | 'LightGBM'
  | 'LSTM'
  | 'Ensemble'

export interface ModelMetricRow {
  modelName: ModelName
  target: ForecastTarget
  horizonHours: number
  mae: number
  rmse: number
  mape: number
  r2: number
  skillVsPersistence: number
  picp80: number | null
  pinaw80: number | null
  modelRunId: string
}

export interface GlobalImportanceItem {
  featureLabel: string
  importancePct: number
  family: 'pollution-history' | 'weather' | 'temporal' | 'spatial' | 'interaction'
}

export interface AlertContributor {
  label: string
  direction: 'up' | 'down'
}

export interface AlertItem {
  id: string
  alertType:
    | 'threshold-crossing'
    | 'rapid-rise'
    | 'extreme-forecast'
    | 'stagnation-advisory'
    | 'data-outage'
    | 'forecast-deterioration'
  severity: 'info' | 'warning' | 'critical'
  stationSlug: string | null
  stationName: string | null
  city: CityName | null
  triggeredAt: string
  observedOrForecast: 'observed' | 'forecast'
  message: string
  context: {
    value: number | null
    threshold: number | null
    horizonHours: number | null
    contributors: AlertContributor[]
  }
  resolvedAt: string | null
}

export interface DataQualityIncident {
  id: string
  stationSlug: string | null
  checkType: string
  severity: 'info' | 'warning' | 'critical'
  detectedAt: string
  resolvedAt: string | null
  detail: string
}

export interface StationAvailabilityCell {
  dayIso: string
  pctAvailable: number
}

export interface StationAvailability {
  slug: string
  matrix: Record<Pollutant, StationAvailabilityCell[]>
}

export interface CorrelationMatrix {
  rows: string[]
  cols: string[]
  values: number[][]
}
