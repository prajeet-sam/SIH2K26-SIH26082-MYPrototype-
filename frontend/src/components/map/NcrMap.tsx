'use client'

import { useEffect, useRef } from 'react'
import * as maplibregl from 'maplibre-gl'
import type { StyleSpecification } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { CurrentConditions } from '@/types/api'

const NCR_CENTER: [number, number] = [77.19, 28.62]

function buildStyle(): StyleSpecification {
  return {
    version: 8,
    sources: {
      basemap: {
        type: 'raster',
        tiles: [
          'https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png',
        ],
        tileSize: 256,
        attribution: '© OpenStreetMap contributors © CARTO',
      },
    },
    layers: [{ id: 'basemap', type: 'raster', source: 'basemap' }],
  }
}

export interface NcrMapProps {
  stations: CurrentConditions[]
  onSelect?: (slug: string) => void
}

export default function NcrMap({ stations, onSelect }: NcrMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const markersRef = useRef<Map<string, maplibregl.Marker>>(new Map())
  const onSelectRef = useRef(onSelect)
  onSelectRef.current = onSelect

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: buildStyle(),
      center: NCR_CENTER,
      zoom: 9.4,
      attributionControl: { compact: true },
    })
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')
    mapRef.current = map
    const markers = markersRef.current
    return () => {
      map.remove()
      mapRef.current = null
      markers.clear()
    }
  }, [])

  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    const desired = new Set(stations.map((s) => s.slug))

    for (const [slug, marker] of markersRef.current) {
      if (!desired.has(slug)) {
        marker.remove()
        markersRef.current.delete(slug)
      }
    }

    for (const station of stations) {
      if (markersRef.current.has(station.slug)) continue
      const el = document.createElement('button')
      el.className = 'ac-station-marker'
      el.setAttribute('aria-label', `${station.name}, AQI ${station.aqi} ${station.category}`)
      el.innerHTML = `<span>${Math.round(station.aqi)}</span>`
      const cat = station.category
      const bg =
        cat === 'Good' ? '#00b25d' :
        cat === 'Satisfactory' ? '#92d050' :
        cat === 'Moderate' ? '#ffd21e' :
        cat === 'Poor' ? '#f78104' :
        cat === 'Very Poor' ? '#e2231a' : '#7d2181'
      el.style.setProperty('--marker-bg', bg)
      el.addEventListener('click', () => {
        onSelectRef.current?.(station.slug)
      })

      const popup = new maplibregl.Popup({ offset: 14, closeButton: false }).setHTML(
        `<div class="ac-popup"><strong>${station.name}</strong><br/>
         AQI <b>${Math.round(station.aqi)}</b> (${station.category}) · PM2.5 ${
           station.pollutants.pm25 ?? '–'
         } µg/m³<br/>Wind ${station.weather.windSpeedMs ?? '–'} m/s · RH ${
           station.weather.relativeHumidityPct ?? '–'
         }%</div>`,
      )

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([station.longitude, station.latitude])
        .setPopup(popup)
        .addTo(map)
      markersRef.current.set(station.slug, marker)
    }
  }, [stations])

  useEffect(() => {
    const map = mapRef.current
    if (!map || stations.length === 0) return
    const lons = stations.map((s) => s.longitude)
    const lats = stations.map((s) => s.latitude)
    map.fitBounds(
      [
        [Math.min(...lons) - 0.15, Math.min(...lats) - 0.12],
        [Math.max(...lons) + 0.15, Math.max(...lats) + 0.12],
      ],
      { padding: 40, duration: 0 },
    )
  }, [stations])

  return (
    <div className="relative h-[480px] w-full overflow-hidden rounded-xl border border-slate-800">
      <div ref={containerRef} className="absolute inset-0" />
      <div className="pointer-events-none absolute bottom-3 left-3 z-10 rounded-lg border border-slate-700 bg-slate-900/90 px-3 py-2 text-[11px] text-slate-300 shadow-lg">
        <div className="mb-1 font-semibold uppercase tracking-wider text-slate-400">AQI category</div>
        <div className="flex flex-wrap gap-x-3 gap-y-1">
          {[
            ['Good', '#00b25d'],
            ['Satisfactory', '#92d050'],
            ['Moderate', '#ffd21e'],
            ['Poor', '#f78104'],
            ['Very Poor', '#e2231a'],
            ['Severe', '#7d2181'],
          ].map(([label, color]) => (
            <span key={label} className="flex items-center gap-1.5">
              <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
              {label}
            </span>
          ))}
        </div>
        <p className="mt-1 text-[10px] text-slate-500">Marker value = current AQI at station</p>
      </div>
    </div>
  )
}
