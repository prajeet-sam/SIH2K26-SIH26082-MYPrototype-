# Demo Script — SIH judging walkthrough (~7 minutes)

**Pre-demo checklist**
- [ ] `docker compose up` stack healthy; `/api/health` returns 200
- [ ] Live ingestion heartbeat < 30 min old, OR DEMO MODE banner intentionally shown
- [ ] Browser tabs pre-loaded: Overview, Map, Forecast(Anand Vihar), Model Intelligence
- [ ] Offline fallback rehearsed once (airplane-mode toggle)

**1. Hook (30 s).** "Delhi's AQI dashboards tell you what already happened. AiraCast tells you
what happens next — and why." Show Overview page: current NCR map + headline forecast strip.

**2. Live Map (60 s).** Zoom NCR heatmap; toggle weather overlay (wind). Point out hotspot
corridors (Anand Vihar/Wazirpur) vs cleaner ridges (Lodhi Road). Hover a station → mini sparkline.

**3. Station forecast (90 s).** Open Anand Vihar detail: observed PM2.5 history + forecast curve
with P10–P90 band and confidence label. Toggle horizons 6/24/48 h. Point at data-quality badge
(station uptime) in corner.

**4. Explainability (60 s).** Click "Why this forecast?": ranked contributions — low wind speed,
high humidity, elevated evening PM2.5, no rainfall expected. Read the disclaimer aloud:
"model-derived association, not causal proof."

**5. Alert engine (45 s).** Show a triggered rapid-rise alert with contributing factors; open
Alerts history page showing past events.

**6. Model Intelligence (90 s).** Real comparison table (persistence vs RF vs XGBoost vs LSTM vs
ensemble) from the DB — walk-forward MAE/RMSE, skill-vs-persistence bars, interval coverage stats,
SHAP summary plot. Emphasize: "these numbers come from our training registry, not slides."

**7. Research mode (45 s).** Select winter 2024, scatter wind speed vs PM2.5, show negative
correlation; export CSV live.

**8. Resilience (30 s).** Kill backend container → dashboard shows graceful error state; restart →
recovers. Mention DEMO MODE banner for offline venues.

**Close (30 s).** Impact recap + pilot ask. Q&A pointers ready: leakage tests, retraining gate,
scaling plan (see docs 05/09/10).
