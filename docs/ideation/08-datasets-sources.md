# 08 — Datasets & Sources

## Primary sources

| # | Source | What we get | Access | Licence/cost |
|---|---|---|---|---|
| 1 | **CPCB CAAQMS via data.gov.in** (`resource/*/api/3/action/datastore_search` style endpoints) | Station-level AQI + pollutants: PM2.5, PM10, NO₂, SO₂, CO, O₃, NH₃; ~40+ NCR stations; near-real-time + historical archives | API key (free) via env var `DATA_GOV_IN_API_KEY` | Govt open data, free |
| 2 | **OpenAQ v3** | Normalized multi-agency air-quality measurements incl. India reference-grade monitors | Free API key `OPENAQ_API_KEY` | CC-BY 4.0 |
| 3 | **WAQI** | Fallback AQ feed when primary providers fail | Free token `WAQI_API_TOKEN` | Attribution required |
| 4 | **Open-Meteo** | Hourly historical+forecast weather for exact station coordinates: temperature, RH, wind speed/direction/gusts, precipitation, pressure | No key required (fair use) | CC-BY 4.0 |
| 5 | **IMD / OpenWeatherMap (optional)** | Redundancy for weather; IMD gridded rainfall if accessible | Optional keys via env | Varies |
| 6 | **ERA5 / Copernicus CDS (research mode)** | Boundary-layer height, sea-level pressure, 2 m temp reanalysis → inversion/stagnation research features | Free CDS account `CDSAPI_KEY` | Copernicus licence |

All keys live ONLY in `.env` (see `.env.example`). No secret ever enters git.

## Canonical NCR station set (MVP)

Delhi: Anand Vihar, Ashok Vihar, Aya Nagar, Bawana, Burari Crossing, CRRI Mathura Road,
Chandni Chowk, DTU, Dr. Karni Singh Shooting Range, Dwarka-Sector 8, IGI Airport T3,
IHBAS Dilshad Garden, ITO, Jahangirpuri, Jawaharlal Nehru Stadium, Lodhi Road, Major Dhyan Chand
Stadium, Mandir Marg, Mundka, Najafgarh, Narela, Nehru Nagar, New Moti Bagh, North Campus DU,
NSIT Dwarka, Okhla Phase-2, Patparganj, Punjabi Bagh, Pusa, R K Puram, Rohini, Shadipur,
Sirifort, Sonia Vihar, Sri Aurobindo Marg, Vivek Vihar, Wazirpur.
Noida: Sector-116, Sector-125, Sector-1. Greater Noida: Knowledge Park-V.
Ghaziabad: Indirapuram, Loni, Sanjay Nagar, Vasundhara.
Gurugram: Gwal Pahari, Sector-51, Vikas Sadan, Teri Gram.
Faridabad: Sector-11, Sector-16A, Nit.
(+ Bahadurgarh, Ballabgarh etc. as availability permits.)

> The ingestion layer resolves provider station names → canonical slugs via a mapping table;
> mismatches are logged, never guessed silently.

## Data volumes (planning numbers)

- Stations ≈ 55 · pollutants ≤ 7 · hourly → ≈ 3.3 M pollutant rows over 5 years (with gaps).
- Weather grid points = one per station coordinate → same order of rows.
- Feature table ≈ 40–80 engineered columns per row. Postgres handles this comfortably with
  BRIN(time) + btree(station_id,time); monthly partitions planned from day one.

## Known data-quality realities (we plan for them)

- CPCB feeds have gaps (sensor calibrations), frozen values, occasional unit anomalies.
- Some stations report only some pollutants.
- Weather APIs differ slightly from on-ground IMD observations — we record source per row.

## Historical backfill strategy

1. Pull CPCB historical station data (data.gov.in archives / manual CSV where necessary).
2. Join nearest Open-Meteo historical archive for matching period.
3. Build the cleaned dataset once; store dataset hash/version; freeze as training snapshot v1.
