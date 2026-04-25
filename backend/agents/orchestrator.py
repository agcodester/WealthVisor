"""
WealthVisor — Orchestrator
LangGraph StateGraph definition with parallel fan-out pattern.
portfolio_agent → [market, tax, behavioral, research] in parallel → brief_agent
"""

import logging
import time
import operator
from typing import Annotated
from datetime import datetime
from langgraph.graph import StateGraph, END
from backend.models.state import VisorState
from backend.agents.portfolio_agent import portfolio_node
from backend.agents.market_agent import market_node
from backend.agents.tax_agent import tax_node
from backend.agents.behavioral_agent import behavioral_node
from backend.agents.research_agent import research_node
from backend.agents.brief_agent import brief_node

logger = logging.getLogger(__name__)


def build_graph() -> StateGraph:
    """
    Builds the LangGraph pipeline:

    START
      │
      ▼
    [portfolio_agent]  ← runs FIRST and alone (superstep 1)
      │
      ├──────────┬───────────┬──────────────┐
      ▼          ▼           ▼              ▼
    [market]  [tax]  [behavioral]  [research]   ← PARALLEL (superstep 2)
      │          │           │              │
      └──────────┴───────────┴──────────────┘
                       │
                       ▼
                [brief_agent]  ← runs LAST (superstep 3)
                       │
                       ▼
                      END
    """
    graph = StateGraph(VisorState)

    # ─── Add all agent nodes ─────────────────────────────────────────────
    graph.add_node("portfolio_agent", portfolio_node)
    graph.add_node("market_agent", market_node)
    graph.add_node("tax_agent", tax_node)
    graph.add_node("behavioral_agent", behavioral_node)
    graph.add_node("research_agent", research_node)
    graph.add_node("brief_agent", brief_node)

    # ─── Define edges ────────────────────────────────────────────────────
    # Entry point: portfolio_agent runs first
    graph.set_entry_point("portfolio_agent")

    # Fan-out: portfolio → 4 agents in parallel (LangGraph handles concurrency)
    graph.add_edge("portfolio_agent", "market_agent")
    graph.add_edge("portfolio_agent", "tax_agent")
    graph.add_edge("portfolio_agent", "behavioral_agent")
    graph.add_edge("portfolio_agent", "research_agent")

    # Fan-in: all 4 → brief_agent
    graph.add_edge("market_agent", "brief_agent")
    graph.add_edge("tax_agent", "brief_agent")
    graph.add_edge("behavioral_agent", "brief_agent")
    graph.add_edge("research_agent", "brief_agent")

    # brief_agent → END
    graph.add_edge("brief_agent", END)

    return graph


# Compile the graph once at module level
_compiled_graph = None


def get_compiled_graph():
    """Returns the compiled graph. Rebuilds each time to pick up state changes."""
    global _compiled_graph
    if _compiled_graph is None:
        graph = build_graph()
        _compiled_graph = graph.compile()
        logger.info("LangGraph pipeline compiled successfully")
    return _compiled_graph


async def run_pipeline(meeting_id: int, client_id: int, scheduled_at: datetime, meeting_type: str) -> dict:
    """
    Runs the full LangGraph pipeline for a specific meeting.
    Returns the final state dict containing the generated brief.
    """
    start_time = time.time()
    logger.info(f"═══ Pipeline START — Meeting #{meeting_id}, Client #{client_id} ═══")

    # Initialize state
    initial_state: VisorState = {
        "meeting_id": meeting_id,
        "client_id": client_id,
        "meeting_scheduled_at": scheduled_at,
        "meeting_type": meeting_type or "review",
        # All agent outputs start empty
        "client_profile": {},
        "portfolio_summary": {},
        "portfolio_performance": {},
        "market_alerts": [],
        "relevant_news": [],
        "market_summary": "",
        "ltcg_opportunities": [],
        "stcg_items": [],
        "elss_recommendation": None,
        "tax_summary": "",
        "behavioral_scores": {},
        "behavioral_flags": [],
        "coaching_points": [],
        "macro_research": [],
        "sector_outlook": {},
        "meeting_brief": None,
        "brief_markdown": None,
        "errors": [],
        "generation_time_sec": None,
    }

    try:
        app = get_compiled_graph()
        # Run the graph — LangGraph handles parallel execution
        final_state = app.invoke(initial_state)

        elapsed = time.time() - start_time
        error_count = len(final_state.get("errors", []))
        logger.info(
            f"═══ Pipeline COMPLETE — Meeting #{meeting_id} — "
            f"{elapsed:.1f}s — {error_count} errors ═══"
        )

        if error_count > 0:
            for err in final_state["errors"]:
                logger.warning(f"  ⚠ {err}")

        return final_state

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"═══ Pipeline FAILED — Meeting #{meeting_id} — {elapsed:.1f}s — {e} ═══")
        initial_state["errors"].append(f"Pipeline crash: {str(e)}")
        return initial_state
