"""
WealthVisor — Behavioral Agent
Agent 4: Scores client on 6 Kahneman-Tversky behavioral dimensions,
generates risk flags and advisor coaching points.
Uses Groq (Llama 3.1 70B) for coaching point generation.
"""

import logging
import time
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from backend.database import SessionLocal
from backend.database.crud import get_client_interactions

logger = logging.getLogger(__name__)

BEHAVIORAL_AGENT_SYSTEM_PROMPT = """You are a behavioral finance expert advising a financial advisor in India before a client meeting.
You specialize in Kahneman-Tversky behavioral frameworks applied to Indian HNI investors.

Given the client's behavioral risk scores (1-10 scale) and contextual flags, generate exactly 3 coaching points.
Each coaching point is 1-2 sentences in this format:
"If the client mentions [specific scenario], respond by [specific advisor action] because [behavioral reasoning]."

Rules:
- Do NOT give generic advice. Make each point specific to THIS client's scores, portfolio, and Indian market context.
- Reference specific behavioral biases by name (loss aversion, overconfidence, herding, recency bias, anchoring, status quo bias).
- Use Indian market examples: NIFTY drops, RBI policy changes, sector-specific events.
- Consider the client's age, risk tolerance, and investment goal.
- Address the most critical flags first — these are urgent behavioral risks.
- Be actionable and practical for the advisor."""


BEHAVIORAL_DIMENSIONS = [
    "loss_aversion",
    "overconfidence",
    "herding",
    "recency_bias",
    "anchoring",
    "status_quo",
]


def behavioral_node(state: dict) -> dict:
    """
    LangGraph node: Behavioral Agent.
    Loads base behavioral scores, adjusts dynamically based on current
    portfolio data, generates flags and coaching points.
    """
    start_time = time.time()
    logger.info("[Behavioral Agent] Starting")
    errors = list(state.get("errors", []))

    behavioral_scores = {}
    behavioral_flags = []
    coaching_points = []

    try:
        client = state.get("client_profile", {})
        portfolio = state.get("portfolio_summary", {})
        performance = state.get("portfolio_performance", {})

        # ─── Step 1: Load base behavioral scores ────────────────────────
        base_scores = client.get("behavioral_score", {})
        scores = {dim: base_scores.get(dim, 5) for dim in BEHAVIORAL_DIMENSIONS}

        # ─── Step 2: Dynamic adjustments ─────────────────────────────────
        return_30d = performance.get("return_30d", 0)
        vs_nifty_30d = performance.get("vs_nifty_30d", 0)
        age = client.get("age", 40)
        risk_tolerance = client.get("risk_tolerance", "moderate")

        # RULE 1: Portfolio down >10% in 30 days?
        if return_30d < -10:
            scores["loss_aversion"] = min(scores["loss_aversion"] + 2, 10)
            behavioral_flags.append(
                f"Portfolio has declined {return_30d:.1f}% in 30 days — client may request defensive repositioning or panic-sell"
            )
        elif return_30d < -5:
            scores["loss_aversion"] = min(scores["loss_aversion"] + 1, 10)
            behavioral_flags.append(
                f"Portfolio down {return_30d:.1f}% in 30 days — monitor for anxiety signals"
            )

        # RULE 2: Age >60 AND aggressive?
        if age > 60 and risk_tolerance == "aggressive":
            scores["status_quo"] = min(scores["status_quo"] + 3, 10)
            behavioral_flags.append(
                f"Risk tolerance misalignment: aggressive stance at age {age} conflicts with retirement timeline"
            )

        # RULE 3: >40% concentration in single sector?
        allocation = portfolio.get("asset_allocation", {})
        for asset_class, pct in allocation.items():
            if pct > 40:
                scores["overconfidence"] = min(scores["overconfidence"] + 2, 10)
                behavioral_flags.append(
                    f"High concentration ({asset_class}: {pct:.0f}%) may indicate overconfidence in that sector"
                )

        # RULE 4: 3+ negative interactions in past 60 days?
        try:
            db = SessionLocal()
            recent_interactions = get_client_interactions(db, state["client_id"], days=60)
            db.close()
            neg_count = sum(1 for i in recent_interactions if i.get("sentiment") in ("negative", "anxious"))
            if neg_count >= 3:
                scores["recency_bias"] = min(scores["recency_bias"] + 2, 10)
                behavioral_flags.append(
                    f"Negative interaction pattern ({neg_count} negative/anxious in 60 days) — avoid leading with losses"
                )
        except Exception as e:
            logger.warning(f"Could not check interactions: {e}")

        # RULE 5: Underperformance vs NIFTY > 5%?
        if vs_nifty_30d < -5:
            scores["anchoring"] = min(scores["anchoring"] + 1, 10)
            behavioral_flags.append(
                f"Underperformance vs NIFTY 50 by {abs(vs_nifty_30d):.1f}% may trigger anchoring to previous high-water mark"
            )

        # RULE 6: Significant portfolio drift?
        rebalancing_candidates = portfolio.get("rebalancing_candidates", [])
        has_high_drift = any(abs(h.get("drift", 0)) > 0.05 for h in rebalancing_candidates)
        if has_high_drift:
            scores["status_quo"] = min(scores["status_quo"] + 2, 10)
            behavioral_flags.append(
                "Portfolio has drifted significantly from target allocation — expect resistance to recommended rebalancing"
            )

        # Cap all scores
        behavioral_scores = {k: max(1, min(v, 10)) for k, v in scores.items()}

        # ─── Step 3: Generate coaching points with Groq ──────────────────
        try:
            llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                temperature=0.4,
                max_tokens=500,
            )

            user_msg = (
                f"Client: {client.get('name', 'Unknown')}\n"
                f"Age: {age} | Risk Tolerance: {risk_tolerance} | "
                f"Investment Goal: {client.get('investment_goal', 'N/A')}\n"
                f"Portfolio 30d return: {return_30d:+.1f}% | vs NIFTY: {vs_nifty_30d:+.1f}%\n"
                f"\nBehavioral Scores (1-10):\n"
            )
            for dim, score in behavioral_scores.items():
                user_msg += f"  • {dim}: {score}/10\n"
            user_msg += f"\nFlags:\n"
            for flag in behavioral_flags:
                user_msg += f"  ⚠ {flag}\n"
            user_msg += "\nGenerate exactly 3 coaching points."

            response = llm.invoke([
                SystemMessage(content=BEHAVIORAL_AGENT_SYSTEM_PROMPT),
                HumanMessage(content=user_msg),
            ])

            # Parse coaching points
            raw = response.content.strip()
            lines = [l.strip() for l in raw.split("\n") if l.strip()]
            coaching_points = []
            for line in lines:
                # Remove numbering like "1.", "1)", etc.
                cleaned = line.lstrip("0123456789.-) ").strip()
                if cleaned and len(cleaned) > 20:
                    coaching_points.append(cleaned)

            # Ensure exactly 3
            coaching_points = coaching_points[:3]
            while len(coaching_points) < 3:
                coaching_points.append(
                    "Monitor the client's emotional state during the meeting and adjust your communication style accordingly."
                )

        except Exception as e:
            logger.error(f"[Behavioral Agent] LLM call failed: {e}")
            errors.append(f"Behavioral agent LLM failed: {str(e)}")
            coaching_points = [
                f"If the client mentions recent losses, acknowledge their concern but redirect to the long-term plan because loss aversion (score: {behavioral_scores.get('loss_aversion', 5)}/10) may drive impulsive decisions.",
                "If the client wants to follow what other investors are doing, emphasize their unique financial situation and goals because herding behavior leads to buying high and selling low.",
                "If the client resists portfolio changes, frame rebalancing as protecting gains rather than taking action, because status quo bias makes inaction feel safer.",
            ]

    except Exception as e:
        logger.error(f"[Behavioral Agent] FAILED: {e}")
        errors.append(f"Behavioral agent error: {str(e)}")

    elapsed = time.time() - start_time
    logger.info(f"[Behavioral Agent] Completed in {elapsed:.1f}s — {len(behavioral_flags)} flags")

    return {
        "behavioral_scores": behavioral_scores,
        "behavioral_flags": behavioral_flags,
        "coaching_points": coaching_points,
        "errors": errors,
    }
