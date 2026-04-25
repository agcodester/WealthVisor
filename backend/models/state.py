"""
WealthVisor — VisorState
Shared TypedDict passed through every LangGraph node.
Every agent reads from and writes to this object.
All monetary values are in INR (₹).

Uses Annotated keys with reducer functions so that
parallel agents can write to the same state without conflict.
"""

import operator
from typing import TypedDict, Optional, List, Dict, Any, Annotated
from datetime import datetime


def _last_value(a, b):
    """Reducer: takes the latest non-None value."""
    return b if b is not None else a


def _merge_dict(a: dict, b: dict) -> dict:
    """Reducer: merges two dicts (b overwrites a on conflicting keys)."""
    merged = {**(a or {}), **(b or {})}
    return merged


class VisorState(TypedDict):
    # ─── Input (set by orchestrator before graph starts) ────────────────
    meeting_id: Annotated[int, _last_value]
    client_id: Annotated[int, _last_value]
    meeting_scheduled_at: Annotated[datetime, _last_value]
    meeting_type: Annotated[str, _last_value]

    # ─── Populated by portfolio_agent ───────────────────────────────────
    client_profile: Annotated[Dict[str, Any], _merge_dict]
    portfolio_summary: Annotated[Dict[str, Any], _merge_dict]
    portfolio_performance: Annotated[Dict[str, Any], _merge_dict]

    # ─── Populated by market_agent ──────────────────────────────────────
    market_alerts: Annotated[List[Dict[str, Any]], operator.add]
    relevant_news: Annotated[List[Dict[str, Any]], operator.add]
    market_summary: Annotated[str, _last_value]

    # ─── Populated by tax_agent ─────────────────────────────────────────
    ltcg_opportunities: Annotated[List[Dict[str, Any]], operator.add]
    stcg_items: Annotated[List[Dict[str, Any]], operator.add]
    elss_recommendation: Annotated[Optional[Dict], _last_value]
    tax_summary: Annotated[str, _last_value]

    # ─── Populated by behavioral_agent ──────────────────────────────────
    behavioral_scores: Annotated[Dict[str, float], _merge_dict]
    behavioral_flags: Annotated[List[str], operator.add]
    coaching_points: Annotated[List[str], operator.add]

    # ─── Populated by research_agent ────────────────────────────────────
    macro_research: Annotated[List[Dict[str, Any]], operator.add]
    sector_outlook: Annotated[Dict[str, str], _merge_dict]

    # ─── Populated by brief_agent (final output) ───────────────────────
    meeting_brief: Annotated[Optional[Dict], _last_value]
    brief_markdown: Annotated[Optional[str], _last_value]

    # ─── Control flags ──────────────────────────────────────────────────
    errors: Annotated[List[str], operator.add]
    generation_time_sec: Annotated[Optional[float], _last_value]
