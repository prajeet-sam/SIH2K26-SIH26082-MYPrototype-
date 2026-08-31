# 07 — Impact & Beneficiaries

## Beneficiary map

| Beneficiary | How AiraCast helps | Impact metric we track |
|---|---|---|
| **General public (NCR ≈ 30 M)** | Hours-ahead warnings to plan outdoor activity, mask use, window/ventilation timing | Forecast lead time vs current zero; alert open rate |
| **Schools & sports authorities** | Objective 6–24 h forecast for cancelling/assembling outdoor sessions | # of informed schedule decisions |
| **Hospitals / clinics** | Anticipate respiratory OPD surges 24–48 h ahead of pollution peaks | Correlation of alerts with OPD spikes (research mode) |
| **Civic bodies (CAQM, DPCC, CPCB)** | Predictive GRAP staging support; identify which stations will breach first | Station-level hit-rate for Severe-category events |
| **Vulnerable groups (asthma, elderly, children)** | Personalized threshold alerts via subscription (Phase 2) | Alert coverage |
| **Logistics/gig platforms** | Exposure-aware scheduling for delivery riders | API integrations (Phase 2) |
| **Researchers** | Clean feature store + model benchmark suite + CSV export = reusable research asset | Dataset downloads, model comparisons |

## Why the impact is credible

- Pollution forecasting is a *decision-support* problem: value scales with lead time. Even modest
  MAE improvement over persistence translates into hours of actionable warning.
- The platform's data-quality layer means authorities can trust what they see — a common failure
  of citizen-built dashboards.
- Open data in → open insights out: all methodology documented and reproducible, enabling
  government adoption without vendor lock-in.

## Alignment with national priorities

- National Clean Air Programme (NCAP): city-level PM reduction targets need predictive analytics.
- CAQM Graded Response Action Plan: stage escalation would benefit from 24–72 h forecasts.
- SDG 3 (health), SDG 11 (sustainable cities), SDG 13 (climate action).

## Social equity angle

Station-level (not city-average) forecasts protect residents of hotspot corridors
(Anand Vihar, Wazirpur, Bawana industrial belt) whose exposure is systematically worse than
the Delhi average that headline bulletins report.
