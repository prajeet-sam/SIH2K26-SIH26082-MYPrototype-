# Scientific Methodology — Weather–Pollution Coupling

This document is the scientific contract the ML implementation must honour.

## 1. Physical background (why weather drives NCR pollution)

- **Dispersion:** near-surface pollutant concentration ∝ emissions / ventilation. Ventilation is
  dominated by horizontal wind speed and boundary-layer mixing depth.
- **Winter inversion:** cool, calm nights decouple surface air from aloft; mixing height collapses;
  evening traffic/biomass emissions accumulate until morning breakup.
- **Hygroscopic growth:** RH > ~70% grows secondary aerosols optically (PM readings rise); very low
  RH favors some secondary pathways — relationship is non-monotonic; models get lags+levels,
  not our assumptions.
- **Washout:** precipitation scavenges coarse particles efficiently (PM10 more than PM2.5);
  effect persists via wet surfaces suppressing dust resuspension.
- **Regional transport:** NW winds during Oct–Nov can advect smoke-affected air-masses into NCR.
  We proxy this with upwind-station lagged PM aligned by wind direction; we do NOT claim source
  apportionment.

## 2. Feature dictionary (implemented by the pipeline)

| Family | Features |
|---|---|
| Pollution history | pm2_5_lag{1,3,6,12,24}, pm10_lag{...}, no2_lag{1..}, same-hour-yesterday, 24h-mean |
| Rolling pollution | mean/std over 3,6,12,24 h windows; min/max 24 h |
| Wind raw | speed, direction, gusts |
| Wind engineered | u=speed·cos(dir), v=speed·sin(dir); u/v lag{1,3,6}; 6h-mean speed; calm-hours-count-6h (<1.54 m/s ≈ Beaufort light air) |
| Stagnation proxies | vent_proxy=rolling6h_mean_speed; stagnation_flag = speed<1.5 m/s AND no rain-24h AND (night flag) |
| Moisture | rh_lag{1,3,6,24}, rh_roll_mean_6h, temp_rh interaction |
| Thermal | t2m, t2m_change_24h, day-night amplitude, t2m_min_last_24h |
| Precipitation | precip_sum_{1,3,6,24}h, hours_since_last_rain |
| Pressure | mslp, mslp_trend_3h (if provided) |
| Temporal | hour sin/cos, dow, is_weekend, month, season(one-hot), holiday flag (India list) |
| Interactions | wind_speed×pm2_5_lag1, rh×pm2_5_lag1, u×pm10_lag1 (selected by importance, kept documented) |
| Spatial proxy | weighted upwind-station pm2_5_lag{3,6} using kernel w=alignment(speed,dir,bearing) |

Boundary-layer height / inversion indices enter ONLY from ERA5 (research mode), clearly versioned
as dataset v2 features. We never synthesize BLH from temperature alone in MVP.

## 3. AQI computation

CPCB 2014 sub-index method: piecewise-linear breakpoints per pollutant (PM2.5 24 h, PM10 24 h,
NO₂ 8 h… as applicable), overall AQI = max sub-index of available pollutants with ≥ required
substance availability (min 16 h of data for daily). Forecasted AQI uses forecasted PM2.5/PM10
sub-indices; the UI labels which pollutants drove it.

## 4. Validation doctrine

- Chronological integrity enforced in code: `FeatureBuilder(cutoff_time=t)` physically cannot read rows after t (tested).
- Walk-forward expanding window; final holdout opened exactly once before submission.
- Same folds for every candidate model — comparisons are apples-to-apples.
- Report per-season breakdown (winter monsoon summer post-monsoon): NCR models must be honest about winter-dominant performance.

## 5. Integrity statements baked into product copy

- Forecasts are probabilistic guidance, not guarantees.
- Explanations are associations from a trained model — not causal attribution.
- Interpolated map pixels are estimates between stations.
- Gaps are imputed under a documented policy and flagged `interpolated` end-to-end.
