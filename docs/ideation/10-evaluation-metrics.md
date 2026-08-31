# 10 — Evaluation Metrics & Success Criteria

## Forecast quality (regression: AQI, PM2.5, PM10 per horizon)

| Metric | Formula/notes | Target (24 h, station-level) |
|---|---|---|
| MAE | primary headline metric | ≥ 15% better than persistence |
| RMSE | penalizes large misses | reported alongside MAE |
| R² | on holdout | > 0.7 for PM2.5 @24 h (winter split reported separately) |
| MAPE | with epsilon guard; suppressed near-zero truth | reported |
| Skill score vs persistence | 1 − MAE_model/MAE_persistence | > 0 at all horizons, all stations |

## Uncertainty calibration

- **PICP** (prediction-interval coverage): P10–P90 band should cover ≈ 80% of outcomes.
- **PINAW**: interval width — reported to expose over-wide "cheating" intervals.
- Winkler score at 80% as combined sharpness+coverage metric.

## Classification view (AQI categories)

Accuracy · macro-F1 · confusion matrix across 6 CPCB categories; report "adjacent-category
tolerance" accuracy too (off-by-one category is materially less harmful).

## System metrics

| Area | Criterion |
|---|---|
| Ingestion freshness | 95% of scheduled runs succeed; data age p95 < 45 min in live mode |
| API latency | p95 < 300 ms cached, < 1 s uncached single-station forecast |
| Dashboard LCP | < 2.5 s on mid-range laptop, warm cache |
| Test suite | unit+integration+ML tests green in CI; leakage tests mandatory |
| Uptime (demo) | full stack boots from clean `docker compose up` in < 5 min |

## Scientific honesty gates

- No metric appears anywhere in code/UI that was not produced by a logged MLflow run.
- Every model page displays its training window, validation scheme, and dataset version.
- Winter-only vs all-season performance both visible; cherry-picking prohibited.

## Acceptance thresholds for MVP demo

1. Persistence beaten at every evaluated horizon (aggregate).
2. Interval coverage within [0.70, 0.90] on holdout, else UI shows "intervals under-calibrated".
3. Zero critical vulnerabilities in security checklist; zero secrets in git history scan.
