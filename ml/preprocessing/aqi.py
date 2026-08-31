"""CPCB National AQI sub-index math (Python port of frontend/src/lib/aqi.ts).

Breakpoints follow CPCB 2014 (24h averaging basis for PM/SO2/NO2/NH3,
8h for O3/CO). Values below the first breakpoint map linearly onto 0-500.
"""

from __future__ import annotations

from typing import Literal

Pollutant = Literal["pm25", "pm10", "no2", "so2", "co", "o3", "nh3"]

# pollutant -> [(conc_low, conc_high, index_low, index_high), ...]
BREAKPOINTS: dict[str, list[tuple[float, float, float, float]]] = {
    "pm25": [
        (0, 30, 0, 50),
        (30, 60, 50, 100),
        (60, 90, 100, 200),
        (90, 120, 200, 300),
        (120, 250, 300, 400),
        (250, 380, 400, 500),
    ],
    "pm10": [
        (0, 50, 0, 50),
        (50, 100, 50, 100),
        (100, 250, 100, 200),
        (250, 350, 200, 300),
        (350, 430, 300, 400),
        (430, 510, 400, 500),
    ],
    "no2": [
        (0, 40, 0, 50),
        (40, 80, 50, 100),
        (80, 180, 100, 200),
        (180, 280, 200, 300),
        (280, 400, 300, 400),
        (400, 520, 400, 500),
    ],
    "so2": [
        (0, 40, 0, 50),
        (40, 80, 50, 100),
        (80, 380, 100, 200),
        (380, 800, 200, 300),
        (800, 1600, 300, 400),
        (1600, 2400, 400, 500),
    ],
    "co": [
        (0, 1, 0, 50),
        (1, 2, 50, 100),
        (2, 10, 100, 200),
        (10, 17, 200, 300),
        (17, 34, 300, 400),
        (34, 51, 400, 500),
    ],
    "o3": [
        (0, 50, 0, 50),
        (50, 100, 50, 100),
        (100, 168, 100, 200),
        (168, 208, 200, 300),
        (208, 748, 300, 400),
        (748, 1000, 400, 500),
    ],
    "nh3": [
        (0, 200, 0, 50),
        (200, 400, 50, 100),
        (400, 800, 100, 200),
        (800, 1200, 200, 300),
        (1200, 1800, 300, 400),
        (1800, 2400, 400, 500),
    ],
}

CATEGORIES: list[tuple[float, str, str]] = [
    (0, "Good", "#00b25d"),
    (51, "Satisfactory", "#9acd32"),
    (101, "Moderate", "#ffb300"),
    (201, "Poor", "#f26c22"),
    (301, "Very Poor", "#d3212d"),
    (401, "Severe", "#7d2181"),
]


def sub_index(pollutant: Pollutant, concentration: float) -> int | None:
    bands = BREAKPOINTS.get(pollutant)
    if not bands or concentration < 0:
        return None
    if concentration > bands[-1][1]:
        return 500
    for c_lo, c_hi, i_lo, i_hi in bands:
        if c_lo <= concentration <= c_hi:
            return round(i_lo + ((i_hi - i_lo) * (concentration - c_lo)) / (c_hi - c_lo))
    return None


def overall_aqi(concentrations: dict[str, float]) -> tuple[int | None, str | None]:
    """Return (AQI, dominant_pollutant) from a dict of concentrations."""
    best: tuple[int, str] | None = None
    for pollutant, value in concentrations.items():
        idx = sub_index(pollutant, value)  # type: ignore[arg-type]
        if idx is None:
            continue
        if best is None or idx > best[0]:
            best = (idx, pollutant)
    if best is None:
        return (None, None)
    return best


def categorize(aqi: int | None) -> str:
    if aqi is None or aqi < CATEGORIES[0][0]:
        return "Unknown"
    label = "Unknown"
    for floor, name, _ in CATEGORIES:
        if aqi >= floor:
            label = name
    return label


def color_for(aqi: int | None) -> str:
    color = "#6b7280"
    for floor, _, hex_color in CATEGORIES:
        if aqi is not None and aqi >= floor:
            color = hex_color
    return color
