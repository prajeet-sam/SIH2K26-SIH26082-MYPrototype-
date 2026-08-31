"""Forecasting engine: features, models, training, prediction, explanation.

Integrity contract (see MASTER_OPENCODE_PROMPT.md §30):
- Forecasts are always derived from real stored observations (or a labelled
  fallback model); no fabricated numbers are emitted.
- If no trained ML model artifact is available, a transparent "persistence"
  baseline is used and the returned forecast is labelled accordingly.
"""

from __future__ import annotations
