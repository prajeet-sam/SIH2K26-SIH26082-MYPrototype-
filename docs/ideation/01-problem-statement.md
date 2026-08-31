# 01 — Problem Statement

## The problem in one paragraph

Delhi NCR is among the most polluted urban regions on Earth. Pollution levels swing dramatically
within hours — driven by meteorology (wind speed, humidity, boundary-layer dynamics, rainfall),
traffic cycles, crop-residue burning seasonality, and festival/industrial activity. Citizens,
schools, hospitals, and authorities currently rely on **descriptive dashboards** that show what the
AQI *is right now*, but not what it will be **in the next 1–72 hours**. Decisions — school closures,
outdoor sports scheduling, N95 advisories, GRAP (Graded Response Action Plan) escalation, hospital
staffing, delivery-route planning — are made reactively, hours too late.

## Specific pain points

1. **No forward-looking intelligence at station level.** CPCB/SAFAR provide city-level or
   coarse-gridded bulletins; a resident of Sector 62 Noida cannot get "what will PM2.5 be near me
   tonight?".
2. **Weather context is ignored by public AQI tools.** A calm, humid winter night can triple
   pollution within 4 hours; existing dashboards do not model this coupling.
3. **Alerts arrive after the spike.** By the time an "AQI Severe" notification fires, exposure has
   already occurred.
4. **No trust layer.** Public tools show a single number with no uncertainty, no explanation, and no
   indication of data quality or sensor outages.
5. **Fragmented data.** Air quality (CPCB CPCB-II/OpenAQ), weather (IMD/Open-Meteo), and reanalysis
   (ERA5) live in separate silos with inconsistent formats, timezones and station naming.

## Why now

- Open APIs (CPCB via data.gov.in / OpenAQ, Open-Meteo, NASA POWER) make real-time ingestion feasible.
- Gradient-boosted trees + sequence models have proven strong performance on 1–48 h air-quality
  forecasting tasks.
- Free/low-cost hosting makes a deployable MVP achievable for a student team.

## Who bears the cost today

| Group | Cost |
|---|---|
| General public | Unplanned exposure; respiratory & cardiovascular risk |
| Schools / sports bodies | No objective basis for cancelling outdoor activity |
| Hospitals | No surge anticipation for respiratory OPD load |
| Civic bodies (CPCB/DPCC/CAQM) | Reactive, not predictive, enforcement (GRAP) |
| Logistics/gig workers | Route/scheduling decisions without exposure foresight |

## Target geography

Delhi plus the immediate National Capital Region:
**Delhi · Noida · Greater Noida · Ghaziabad · Gurugram · Faridabad** (+ surrounding stations where
data exists: e.g., Bahadurgarh, Ballabgarh, Loni, Meerut edge-stations).
