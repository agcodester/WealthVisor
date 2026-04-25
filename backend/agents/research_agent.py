"""
WealthVisor — Research Agent
Agent 5: Fetches macro research (RBI rates, India-specific indicators),
sector performance, and past briefs from Qdrant.
Uses Groq (Llama 3.1 70B) for sector outlook generation.
"""

import logging
import time
import requests
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from backend.tools.market_tools import get_sector_etf_return, get_benchmark_return
from backend.tools.vector_store import retrieve_past_briefs

logger = logging.getLogger(__name__)

RESEARCH_AGENT_SYSTEM_PROMPT = """You are a senior macro research analyst at a top Indian wealth management firm.
Your role is to provide sector-specific outlooks for a financial advisor preparing for a client meeting.

For each sector provided, write exactly 1 sentence of outlook that:
- References the sector's recent performance (use the data given)
- Considers the client's portfolio weight in that sector
- Mentions one forward-looking factor (RBI policy, earnings season, global cues, etc.)
- Is actionable for the advisor (e.g., "suggest trimming", "maintain overweight", "watch for entry point")

Use Indian market context: NIFTY sectors, NSE-listed companies, RBI, FII flows, rupee movement.
Format: Return as structured text with "Sector: outlook" on each line."""

# ─── Indian Sector Mapping ──────────────────────────────────────────────────
SECTOR_MAP = {
    "RELIANCE.NS": "Energy",
    "TCS.NS": "IT",
    "INFY.NS": "IT",
    "HDFCBANK.NS": "Banking",
    "ICICIBANK.NS": "Banking",
    "BHARTIARTL.NS": "Telecom",
    "ITC.NS": "FMCG",
    "KOTAKBANK.NS": "Banking",
    "LT.NS": "Infrastructure",
    "AXISBANK.NS": "Banking",
    "SBIN.NS": "Banking",
    "WIPRO.NS": "IT",
    "HCLTECH.NS": "IT",
    "MARUTI.NS": "Auto",
    "TATAMOTORS.NS": "Auto",
    "NIFTYBEES.NS": "Broad Market",
    "BANKBEES.NS": "Banking",
    "GOLDBEES.NS": "Commodities",
    "JUNIORBEES.NS": "Broad Market",
    "LIQUIDBEES.NS": "Fixed Income",
}


def research_node(state: dict) -> dict:
    """
    LangGraph node: Research Agent.
    Computes sector exposure, fetches sector performance data,
    retrieves macro indicators and past briefs from Qdrant.
    """
    start_time = time.time()
    logger.info("[Research Agent] Starting")
    errors = list(state.get("errors", []))

    macro_research = []
    sector_outlook = {}

    try:
        client = state.get("client_profile", {})
        portfolio = state.get("portfolio_summary", {})
        holdings = portfolio.get("holdings", [])
        total_value = portfolio.get("total_value", 0)

        # ─── Step 1: Determine sector exposure ───────────────────────────
        sector_weights = {}
        for h in holdings:
            ticker = h["ticker"]
            sector = SECTOR_MAP.get(ticker, "Other")
            val = h.get("current_value", 0)
            sector_weights[sector] = sector_weights.get(sector, 0) + val

        # Convert to percentages
        sector_pct = {}
        for s, v in sector_weights.items():
            if total_value > 0:
                sector_pct[s] = round(v / total_value * 100, 1)
            else:
                sector_pct[s] = 0

        # ─── Step 2: Fetch sector performance ────────────────────────────
        sector_performance = {}
        nifty_30d = get_benchmark_return(30)

        for sector in sector_pct:
            if sector_pct[sector] > 3:  # only meaningful sectors
                ret = get_sector_etf_return(sector, 30)
                if ret > nifty_30d + 2:
                    status = "outperforming"
                elif ret < nifty_30d - 2:
                    status = "underperforming"
                else:
                    status = "in-line"
                sector_performance[sector] = {
                    "return_30d": ret,
                    "status": status,
                    "weight": sector_pct[sector],
                }

        # ─── Step 3: Fetch RBI / Indian macro indicators ────────────────
        try:
            # RBI Repo Rate (latest known — we use a fallback since no free API)
            macro_research.append({
                "title": "RBI Repo Rate at 6.50%",
                "summary": "The Reserve Bank of India maintains the repo rate at 6.50%. The stance remains focused on withdrawal of accommodation to manage inflation while supporting growth.",
                "relevance_score": 0.85,
                "source": "RBI",
            })

            # India CPI Inflation
            macro_research.append({
                "title": "CPI Inflation trending at ~5.0%",
                "summary": "Consumer price inflation remains within RBI's tolerance band of 2-6%, providing room for potential rate action in upcoming policy meetings.",
                "relevance_score": 0.80,
                "source": "MOSPI",
            })

            # India GDP Growth
            macro_research.append({
                "title": "India GDP growth at ~6.5% YoY",
                "summary": "India remains one of the fastest-growing major economies. Strong domestic consumption and infrastructure spending continue to drive growth momentum.",
                "relevance_score": 0.75,
                "source": "NSO",
            })

        except Exception as e:
            logger.warning(f"[Research Agent] Macro data fetch failed: {e}")
            errors.append(f"Macro data fetch partial failure: {str(e)}")

        # ─── Step 4: Retrieve past briefs from Qdrant ────────────────────
        try:
            past_briefs = retrieve_past_briefs(
                client_id=state["client_id"],
                query=f"portfolio review for {client.get('name', '')} sector exposure",
                top_k=2,
            )
            if past_briefs:
                macro_research.append({
                    "title": "Previous Meeting Context",
                    "summary": f"Found {len(past_briefs)} past brief(s) for continuity reference.",
                    "relevance_score": 0.70,
                    "source": "WealthVisor History",
                })
        except Exception as e:
            logger.warning(f"[Research Agent] Qdrant query failed: {e}")

        # ─── Step 5: Generate sector outlook with Groq ───────────────────
        try:
            llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                temperature=0.3,
                max_tokens=500,
            )

            # Build sector data for prompt
            sector_info = ""
            top_sectors = sorted(sector_performance.items(), key=lambda x: x[1]["weight"], reverse=True)[:5]
            for sector, data in top_sectors:
                sector_info += (
                    f"- {sector}: 30d return = {data['return_30d']:+.1f}%, "
                    f"client weight = {data['weight']:.1f}%, "
                    f"status = {data['status']}\n"
                )

            user_msg = (
                f"Client: {client.get('name', 'Unknown')}, "
                f"Risk tolerance: {client.get('risk_tolerance', 'moderate')}\n"
                f"NIFTY 50 30d return: {nifty_30d:+.1f}%\n"
                f"\nSector exposure and performance:\n{sector_info}\n"
                f"Generate 1-sentence outlook for each sector."
            )

            response = llm.invoke([
                SystemMessage(content=RESEARCH_AGENT_SYSTEM_PROMPT),
                HumanMessage(content=user_msg),
            ])

            # Parse response into dict
            for line in response.content.strip().split("\n"):
                line = line.strip()
                if ":" in line and len(line) > 10:
                    parts = line.split(":", 1)
                    sector_name = parts[0].strip().strip("-•* ")
                    outlook = parts[1].strip()
                    if sector_name and outlook:
                        sector_outlook[sector_name] = outlook

            # If parsing failed, use defaults
            if not sector_outlook:
                for sector, data in top_sectors:
                    sector_outlook[sector] = f"{sector} has returned {data['return_30d']:+.1f}% over 30 days, {data['status']} vs NIFTY 50."

        except Exception as e:
            logger.error(f"[Research Agent] LLM call failed: {e}")
            errors.append(f"Research agent LLM failed: {str(e)}")
            for sector, data in sector_performance.items():
                sector_outlook[sector] = f"{sector}: {data['return_30d']:+.1f}% (30d), {data['status']} vs NIFTY 50. Client weight: {data['weight']:.1f}%."

    except Exception as e:
        logger.error(f"[Research Agent] FAILED: {e}")
        errors.append(f"Research agent error: {str(e)}")

    elapsed = time.time() - start_time
    logger.info(f"[Research Agent] Completed in {elapsed:.1f}s — {len(sector_outlook)} sectors analyzed")

    return {
        "macro_research": macro_research,
        "sector_outlook": sector_outlook,
        "errors": errors,
    }
