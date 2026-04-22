"""
query_builder.py — turn the 4-toggle selection into a natural-language query.

Mirrors the logic in src/10_query_construction.py but as a pure function
(no interactive prompts).
"""
from __future__ import annotations

from .schemas import ToggleSelection


_CUISINE_NO_PREF = {"No preference", "no preference", "Any", "any", None, ""}
_PRIORITY_NONE   = {"None", "none", None, ""}


def build_query(t: ToggleSelection, free_text: str | None = None) -> str:
    """
    Compose a query string from toggles + optional free text.
    Order matches 10_query_construction.py: cuisine → vibe → occasion → priority,
    with free_text prepended when provided.
    """
    parts: list[str] = []
    if t is None:
        return (free_text or "").strip()
    if t.cuisine and t.cuisine not in _CUISINE_NO_PREF:
        parts.append(t.cuisine)
    if t.vibe:
        parts.append(t.vibe)
    if t.occasion:
        parts.append(t.occasion)
    if t.priority and t.priority not in _PRIORITY_NONE:
        parts.append(t.priority)
    built = " ".join(parts).strip()
    if free_text and free_text.strip():
        return f"{free_text.strip()} {built}".strip() if built else free_text.strip()
    return built
