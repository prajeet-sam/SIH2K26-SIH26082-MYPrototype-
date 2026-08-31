# AiraCast Frontend

Next.js 14 (App Router) dashboard for the AiraCast air-pollution–weather coupled forecasting
platform. Built per `../MASTER_OPENCODE_PROMPT.md` §17–18.

## Stack

- Next.js 14 App Router · React 18 · **TypeScript strict**
- Tailwind CSS (dark-mode-first, class strategy)
- TanStack Query for fetching/caching/retries
- Recharts for time-series/scatter/heatmap visuals
- MapLibre GL (CARTO dark raster basemap — no API token required)
- lucide-react icons
- Vitest + React Testing Library

## Run

```bash
npm install
npm run dev        # http://localhost:3000
npm run lint       # eslint (next/core-web-vitals)
npm run typecheck  # tsc --noEmit (strict)
npm test           # vitest unit/component tests
```

## Data sources & provenance

The typed client (`src/lib/api.ts`) targets the FastAPI backend via
`NEXT_PUBLIC_API_BASE_URL`. Behaviour is controlled by env vars:

| Var | Values | Meaning |
|---|---|---|
| `NEXT_PUBLIC_DATA_SOURCE` | `auto` (default) / `live` / `demo` | `auto` tries the backend, falls back to demo on failure |
| `NEXT_PUBLIC_API_BASE_URL` | e.g. `http://localhost:8000` | Backend origin |
| `NEXT_PUBLIC_API_TIMEOUT_MS` | default `4000` | Live-fetch timeout |

Until the backend exists, every page renders **labelled demo data** from
`src/lib/demo/data.ts` — a deterministic, seeded synthetic generator whose PM2.5/PM10 respond to
generated wind/rain/humidity conditions so that the weather–pollution coupling is visible in the
UI. A persistent banner ("Demo data — not real-time observations") plus a header chip are shown
whenever demo data is active. No fabricated numbers are ever presented as real observations, and
the Model Intelligence page labels its illustrative metrics explicitly until real training runs
populate the registry.

Station coordinates in the demo dataset are **approximate** locations of the canonical CPCB NCR
monitoring network (see `../docs/ideation/08-datasets-sources.md`); the real registry will be
seeded server-side with authoritative coordinates.

## Structure

```
src/
├── app/                    # one route per dashboard page (Overview, Map, Forecast,
│                           #   Stations(+[slug]), Analysis, Models, History, Alerts, Research)
├── components/
│   ├── layout/             # AppShell, Sidebar, TopBar, DemoBanner
│   ├── common/             # AqiBadge, KpiCard, SectionCard, chips, states
│   ├── charts/             # TimeSeriesChart (band-capable), ScatterPlot,
│   │                       #   CorrelationHeatmap, HorizontalBars, Sparkline
│   └── map/NcrMap.tsx      # MapLibre station map (client-only)
├── lib/
│   ├── aqi.ts              # CPCB 2014 sub-index breakpoints + categories + colors
│   ├── api.ts              # typed client: live fetch w/ timeout → labelled demo fallback
│   ├── datasource.tsx      # live/demo provenance context driving the banners/chips
│   ├── hooks.ts            # useEnvQuery wrapper reporting data source
│   ├── csv.ts              # CSV export helpers
│   └── demo/data.ts        # deterministic synthetic generator
└── types/api.ts            # API contract types mirroring the planned FastAPI schemas
```

## Accessibility & integrity notes

- AQI categories are always distinguished by color **and** text label/badge — never color alone.
- Forecasts render dashed lines + P10–P90 shaded bands; observed series are solid.
- Explanation panels carry an explicit "associations, not causal proof" disclaimer.
