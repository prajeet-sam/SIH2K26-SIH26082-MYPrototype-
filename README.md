# AiraCast — Air Pollution–Weather Coupled Forecasting System for Delhi NCR

> Smart India Hackathon 2026 ideation repository.
> This repo currently contains **ideation + specification artifacts** (what SIH judges evaluate).
## One-line pitch

**AiraCast** is a research-grade environmental intelligence platform that couples real-time air-quality
data with meteorology (wind, humidity, temperature, rainfall, stagnation proxies) to forecast AQI,
PM2.5 and PM10 across Delhi NCR at station level — with uncertainty bands, explainability, and
health-actionable alerts.

## Why it is not "just another AQI dashboard"

| Typical AQI dashboard | AiraCast |
|---|---|
| Shows *current* pollution | Forecasts pollution **1–72 hours ahead**, per station |
| No weather context | Explicitly models weather–pollution coupling (dispersion, accumulation, washout) |
| Single opaque number | Baseline vs advanced model comparison, honest metrics from *real* training runs |
| No explanation | SHAP/feature-importance driven "why" narratives |
| Point forecasts only | Prediction intervals + confidence labels |
| Static map | NCR-wide interpolated heatmap + weather overlays |
| No data trust layer | Data-quality monitoring, observed/forecast/interpolated labelling |

## Repository layout (current stage)

```
SIH-Ideation/
├── README.md                        <- you are here
├── .gitignore
├── MASTER_OPENCODE_PROMPT.md        <- full build spec handed to the AI coding agent
├── docs/
│   ├── ideation/                    <- SIH judge-facing documents
│   │   ├── 01-problem-statement.md
│   │   ├── 02-idea-summary.md
│   │   ├── 03-proposed-solution.md
│   │   ├── 04-tech-stack.md
│   │   ├── 05-system-architecture.md
│   │   ├── 06-feasibility-viability.md
│   │   ├── 07-impact-beneficiaries.md
│   │   ├── 08-datasets-sources.md
│   │   ├── 09-roadmap-phases.md
│   │   ├── 10-evaluation-metrics.md
│   │   └── 11-pitch-one-pager.md
│   ├── demo/
│   │   └── demo-script.md           <- judge walkthrough for the live demo
│   └── research/
│       └── scientific-methodology.md<- weather–pollution coupling rationale
```

## Quick links

- Problem statement → `docs/ideation/01-problem-statement.md`
- Proposed solution → `docs/ideation/03-proposed-solution.md`
- Architecture → `docs/ideation/05-system-architecture.md`
- Build spec for OpenCode → `MASTER_OPENCODE_PROMPT.md`

## Status

- [x] Ideation complete
- [x] Master implementation spec written
- [x] Frontend dashboard built (`frontend/` — 9 pages, labelled demo mode, tests green)
- [ ] Backend + ML engine (OpenCode phases 2–7)
- [ ] Live demo deployment
