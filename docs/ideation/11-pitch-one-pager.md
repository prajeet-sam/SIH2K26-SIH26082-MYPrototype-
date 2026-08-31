# 11 — Pitch One-Pager (judges' quick read)

## AiraCast — Weather-Coupled Air Pollution Forecasting for Delhi NCR

**Problem.** 30 M people in NCR get pollution information hours too late. Dashboards show today's
AQI; decisions need tomorrow's. Weather drives pollution swings (calm humid winter nights trap
emissions; rain/wind clean the air), yet no public tool models this coupling at station level.

**Solution.** A production-grade platform that fuses live CPCB/OpenAQ air-quality with weather
data, engineers physics-informed features (wind vectors, stagnation indicators, accumulation
memory), and forecasts AQI/PM2.5/PM10 for ~55 NCR stations over 1–72 h — with uncertainty bands,
SHAP-based explanations, threshold alerts, and a research workbench.

**Differentiators.**
1. Weather–pollution coupling as explicit feature science, not buzzwords.
2. Honest ML: baselines benchmarked under identical walk-forward validation; deep learning must earn its place.
3. Trust layer: observed/forecast/interpolated labels, data-quality monitoring, demo mode that admits it's demo.
4. Full-stack completeness: ingestion → DB → API → dashboard → alerts, dockerized, tested, documented.

**Tech.** FastAPI · PostgreSQL+PostGIS · Celery/Redis · XGBoost/LightGBM · PyTorch · SHAP/MLflow ·
Next.js+TypeScript · MapLibre · Docker Compose. All open data, ₹0 data cost.

**Impact.** Hours-earlier warnings for citizens, schools, hospitals; predictive support for
CAQM/GRAP enforcement; reusable open research asset for NCAP cities.

**Demo flow.** Live map of current NCR AQI → pick Anand Vihar → see tonight's PM2.5 forecast band
→ "Why?" panel shows calm winds + humidity driving it → alert fires for 6-h rapid rise → switch to
Model Intelligence: our XGBoost beats persistence by X% MAE on held-out winter weeks.

**The ask.** Pilot deployment support + CAQM/school-board introduction for a 3-month real-world
validation.
