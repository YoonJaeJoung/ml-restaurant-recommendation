"""
hours.py — determine whether a restaurant is open at a given local date/time.

Reuses the parsing heuristics from the Streamlit prototype (src/app.py),
cleaned up into pure functions with no Streamlit deps.

Google Local Reviews stores the `hours` column as an iterable of strings like
'Monday11AM–10PM' or 'FridayClosed'. We split on the en-dash to get open/close
times and handle overnight hours (e.g. 5PM–2AM).
"""
from __future__ import annotations

from datetime import date, datetime, time
from typing import Iterable, Optional

import numpy as np
import pandas as pd


def _parse_time(token: str, context: str | None = None) -> Optional[time]:
    """Parse tokens like '11AM', '5:30PM' → time(). Uses context for missing AM/PM."""
    t = token.strip().upper()
    if t in {"12AM", "12:00AM"}:
        return time(0, 0)
    if t in {"12PM", "12:00PM"}:
        return time(12, 0)
    try:
        if ":" in t:
            hr_s, rest = t.split(":", 1)
            hour = int(hr_s)
            minute = int("".join(ch for ch in rest if ch.isdigit()))
        else:
            hour = int("".join(ch for ch in t if ch.isdigit()))
            minute = 0
        is_pm = "PM" in t
        if not ("AM" in t or "PM" in t) and context:
            is_pm = "PM" in context.upper()
        if is_pm and hour != 12:
            hour += 12
        elif (not is_pm) and hour == 12:
            hour = 0
        if context and "PM" in context.upper() and hour < 12 and not is_pm:
            hour += 12
        return time(hour, minute)
    except Exception:
        return None


def is_open_at(hours_info: Iterable[str] | None, visit: datetime) -> Optional[bool]:
    """
    Return True/False if a decisive answer can be parsed, None otherwise.
    """
    if hours_info is None:
        return None
    if isinstance(hours_info, float) and pd.isna(hours_info):
        return None
    if isinstance(hours_info, np.ndarray):
        hours_info = hours_info.tolist()
    if not hours_info:
        return None

    day_name = visit.strftime("%A")
    visit_t = visit.time()

    for entry in hours_info:
        if not isinstance(entry, str):
            continue
        if day_name not in entry:
            continue
        if "Closed" in entry:
            return False
        if "–" not in entry:
            continue
        open_s, close_s = entry.split("–", 1)
        open_s = open_s.replace(day_name, "").strip()
        close_s = close_s.strip()
        open_t  = _parse_time(open_s, close_s)
        close_t = _parse_time(close_s)
        if not open_t or not close_t:
            continue
        # Overnight hours (close < open after parsing)
        if close_t < open_t:
            return visit_t >= open_t or visit_t < close_t
        return open_t <= visit_t <= close_t

    return None
