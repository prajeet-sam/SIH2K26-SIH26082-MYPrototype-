'use client'

import {
  demoAlerts,
  demoAvailability,
  demoCorrelationMatrix,
  demoCurrentConditions,
  demoDataQualityIncidents,
  demoExplanation,
  demoForecast,
  demoGlobalImportance,
  demoModelPerformance,
  demoObservationHistory,
  demoStations,
  demoWeatherForecast,
  demoWeatherHistory,
} from '@/lib/demo/data'
import type {
  AlertItem,
  CorrelationMatrix,
  CurrentConditions,
  DataQualityIncident,
  DataSourceKind,
  ExplanationResponse,
  ForecastResponse,
  ForecastTarget,
  GlobalImportanceItem,
  ModelMetricRow,
  ObservationPoint,
  Station,
  StationAvailability,
  WeatherPoint,
} from '@/types/api'

export interface ApiResult<T> {
  data: T
  source: DataSourceKind
}

export class ApiUnavailableError extends Error {}

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? ''
const DATA_SOURCE = (process.env.NEXT_PUBLIC_DATA_SOURCE ?? 'auto') as
  | 'auto'
  | 'live'
  | 'demo'
const TIMEOUT_MS = Number(process.env.NEXT_PUBLIC_API_TIMEOUT_MS ?? 4000)

async function apiFetch<T>(path: string): Promise<T> {
  if (!BASE_URL) throw new ApiUnavailableError('API base URL not configured')
  let res: Response
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      signal: AbortSignal.timeout(TIMEOUT_MS),
      headers: { Accept: 'application/json' },
    })
  } catch {
    throw new ApiUnavailableError(`Request failed: ${path}`)
  }
  if (!res.ok) throw new ApiUnavailableError(`HTTP ${res.status}: ${path}`)
  return (await res.json()) as T
}

async function withFallback<T>(
  livePath: string | null,
  demoFn: () => T,
): Promise<ApiResult<T>> {
  if (DATA_SOURCE === 'live') {
    return { data: await apiFetch<T>(livePath as string), source: 'live' }
  }
  if (DATA_SOURCE === 'demo') {
    return { data: demoFn(), source: 'demo' }
  }
  try {
    return { data: await apiFetch<T>(livePath as string), source: 'live' }
  } catch (err) {
    if (err instanceof ApiUnavailableError) {
      return { data: demoFn(), source: 'demo' }
    }
    throw err
  }
}

export function getStations(): Promise<ApiResult<Station[]>> {
  return withFallback('/api/stations', demoStations)
}

export function getCurrentConditions(): Promise<ApiResult<CurrentConditions[]>> {
  return withFallback('/api/air-quality/current', demoCurrentConditions)
}

export function getObservationHistory(
  slug: string,
  tailHours: number,
): Promise<ApiResult<ObservationPoint[]>> {
  return withFallback(
    `/api/air-quality/history?station_id=${encodeURIComponent(slug)}&tail_hours=${tailHours}`,
    () => demoObservationHistory(slug, tailHours),
  )
}

export function getWeatherHistory(
  slug: string,
  tailHours: number,
): Promise<ApiResult<WeatherPoint[]>> {
  return withFallback(
    `/api/weather/history?station_id=${encodeURIComponent(slug)}&tail_hours=${tailHours}`,
    () => demoWeatherHistory(slug, tailHours),
  )
}

export function getWeatherForecast(
  slug: string,
  aheadHours: number,
): Promise<ApiResult<WeatherPoint[]>> {
  return withFallback(
    `/api/forecast/weather?station_id=${encodeURIComponent(slug)}&ahead_hours=${aheadHours}`,
    () => demoWeatherForecast(slug, aheadHours),
  )
}

export function getForecast(
  slug: string,
  target: ForecastTarget,
  horizonHours: number,
): Promise<ApiResult<ForecastResponse>> {
  return withFallback(
    `/api/forecast/${encodeURIComponent(slug)}?targets=${target}&horizons=${horizonHours}`,
    () => demoForecast(slug, target, horizonHours),
  )
}

export function getExplanation(
  slug: string,
  target: ForecastTarget,
  horizonHours: number,
): Promise<ApiResult<ExplanationResponse>> {
  return withFallback(
    `/api/forecast/explain/${encodeURIComponent(slug)}?target=${target}&horizon_hours=${horizonHours}`,
    () => demoExplanation(slug, target, horizonHours),
  )
}

export function getModelPerformance(target: ForecastTarget): Promise<ApiResult<ModelMetricRow[]>> {
  return withFallback(`/api/model/performance?target=${target}`, () =>
    demoModelPerformance(target),
  )
}

export function getGlobalImportance(): Promise<ApiResult<GlobalImportanceItem[]>> {
  return withFallback('/api/model/explanations/global-importance', demoGlobalImportance)
}

export function getAlerts(): Promise<ApiResult<AlertItem[]>> {
  return withFallback('/api/alerts', demoAlerts)
}

export function getDataQualityIncidents(): Promise<ApiResult<DataQualityIncident[]>> {
  return withFallback('/api/data-quality/status', demoDataQualityIncidents)
}

export function getAvailability(slug: string): Promise<ApiResult<StationAvailability>> {
  return withFallback(
    `/api/stations/${encodeURIComponent(slug)}/availability`,
    () => demoAvailability(slug),
  )
}

export function getCorrelations(slug: string, days: number): Promise<ApiResult<CorrelationMatrix>> {
  return withFallback(
    `/api/research/correlations?station_id=${encodeURIComponent(slug)}&days=${days}`,
    () => demoCorrelationMatrix(slug, days),
  )
}
