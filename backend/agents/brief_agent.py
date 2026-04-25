"""
WealthVisor — Brief Agent (Final Synthesizer)
Agent 6: Synthesizes all agent outputs into a structured, professional meeting brief.
Makes 4 Groq LLM calls: executive summary, agenda, talking points, follow-up email.
Generates both structured dict and formatted markdown. Indian market context (₹, NIFTY, NSE).
"""

import logging
import time
from datetime import datetime
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from backend.database import SessionLocal
from backend.database.crud import save_brief
from backend.tools.vector_store import upsert_brief

logger = logging.getLogger(__name__)

# ─── System Prompts for each LLM call ──────────────────────────────────────

EXECUTIVE_SUMMARY_PROMPT = """You are an elite financial advisor's assistant at a top Indian wealth management firm.
Generate a 3-sentence executive summary for a client meeting brief.

Sentence 1: Portfolio status and performance (use exact ₹ amounts and % returns, compare vs NIFTY 50).
Sentence 2: The single most urgent action item — either a tax optimization opportunity, a rebalancing need, or a critical market alert. Be specific.
Sentence 3: One behavioral note the advisor absolutely must keep in mind during this meeting.

Rules:
- Use ₹ symbol and Indian number format (lakhs = L, crores = Cr)
- Reference NIFTY 50 as benchmark, not SPY
- Be specific with numbers — never be vague
- This is for the advisor to read 2 minutes before the meeting"""

AGENDA_PROMPT = """You are a senior meeting coordinator at a leading Indian wealth management firm.
Create exactly 5 meeting agenda items for an advisor-client portfolio review.

Format each as: "XX min — [Topic]: [one sentence explaining why this matters for THIS specific client]"
Total time should sum to the meeting duration. Allocate more time to urgent items.

Rules:
- Order by priority (most important first)
- Reference specific data: ticker names, ₹ amounts, tax savings, behavioral flags
- Include at least one tax-related agenda item if relevant
- Include a behavioral coaching moment if any scores are above 7
- End with action items / next steps"""

TALKING_POINTS_PROMPT = """You are a communication coach for Indian financial advisors at a premium wealth management firm.
Generate exactly 4 talking points for an advisor preparing for a client meeting.

Each talking point:
- Is exactly 2 sentences maximum
- Is grounded in specific data (actual ticker names, ₹ amounts, percentages)
- Anticipates the client's emotional state based on behavioral scores
- Uses reassuring, confident language appropriate for Indian HNI clients

Format: numbered list (1. through 4.)

Rules:
- First point should address the client's likely top concern
- Include at least one proactive recommendation
- Reference Indian market context (NIFTY, RBI, sector performance)
- If there are tax savings opportunities, always include one point about it"""

FOLLOW_UP_EMAIL_PROMPT = """You are drafting a professional follow-up email for a financial advisor in India.
The email is sent to an Indian HNI client after a portfolio review meeting.

Tone: Professional but warm. Use "Dear [Client Name]" greeting style.
Length: Exactly 150 words.
Structure: Greeting → Summary of key discussion points → Action items → Closing.

Rules:
- Reference specific items discussed (e.g., "your RELIANCE position", "the ELSS investment we discussed")
- Include 2-3 placeholder items like [INSERT AGREED ACTION] for the advisor to customize
- Use ₹ amounts where applicable
- Sign off with the advisor's name placeholder [ADVISOR NAME]
- Include a line about scheduling the next review"""


def _format_inr(amount: float) -> str:
    """Format amount in Indian style: ₹12,34,567 or ₹1.2 Cr / ₹45.5 L."""
    if abs(amount) >= 10000000:  # 1 crore+
        return f"₹{amount/10000000:.1f} Cr"
    elif abs(amount) >= 100000:  # 1 lakh+
        return f"₹{amount/100000:.1f} L"
    else:
        return f"₹{amount:,.0f}"


def _get_llm():
    """Returns a configured Groq LLM instance."""
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        max_tokens=600,
    )


def _safe_llm_call(prompt: str, user_msg: str, fallback: str) -> str:
    """Makes an LLM call with fallback on failure."""
    try:
        llm = _get_llm()
        response = llm.invoke([
            SystemMessage(content=prompt),
            HumanMessage(content=user_msg),
        ])
        return response.content.strip()
    except Exception as e:
        logger.error(f"[Brief Agent] LLM call failed: {e}")
        return fallback


def generate_markdown(brief: dict) -> str:
    """Converts the brief dict to a professionally formatted markdown string."""
    metadata = brief.get("metadata", {})
    portfolio = brief.get("portfolio", {})
    perf = portfolio.get("performance", {})
    alloc = portfolio.get("asset_allocation", {})
    market = brief.get("market_intelligence", {})
    tax = brief.get("tax_opportunities", {})
    behavioral = brief.get("behavioral_intelligence", {})
    research = brief.get("macro_research", {})

    lines = []

    # Header
    lines.append(f"# 📋 Meeting Brief: {metadata.get('client_name', 'Client')}")
    lines.append(f"**{metadata.get('meeting_type', 'Review').replace('_', ' ').title()}** · "
                 f"{metadata.get('meeting_at', '')} · "
                 f"AUM: {_format_inr(metadata.get('advisor_aum_this_client', 0))}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Executive Summary
    lines.append("## 🔑 Executive Summary")
    lines.append(brief.get("executive_summary", "Brief generation in progress..."))
    lines.append("")
    lines.append("---")
    lines.append("")

    # Portfolio Snapshot
    lines.append("## 📊 Portfolio Snapshot")
    tv = portfolio.get("total_value", 0)
    lines.append(f"**Total Value:** {_format_inr(tv)}")
    lines.append(f"**30-Day Return:** {perf.get('return_30d', 0):+.2f}% "
                 f"(NIFTY 50: {perf.get('nifty_30d', 0):+.2f}%)")
    lines.append(f"**YTD Return:** {perf.get('ytd_return', 0):+.2f}% "
                 f"(NIFTY 50: {perf.get('nifty_ytd', 0):+.2f}%)")
    lines.append("")

    # Asset Allocation
    lines.append("**Asset Allocation:**")
    for ac, pct in alloc.items():
        lines.append(f"- {ac.title()}: {pct:.1f}%")
    lines.append("")

    # Top Holdings Table
    top_h = portfolio.get("top_holdings", [])
    if top_h:
        lines.append("**Top Holdings:**")
        lines.append("| Ticker | Value | Weight | 30d Return | Drift |")
        lines.append("|--------|-------|--------|------------|-------|")
        for h in top_h:
            ticker = h.get('ticker', '').replace('.NS', '')
            val = _format_inr(h.get('current_value', 0))
            weight = f"{h.get('actual_weight', 0)*100:.1f}%"
            ret = f"{h.get('return_30d', 0):+.1f}%"
            drift = f"{h.get('drift', 0)*100:+.1f}%"
            lines.append(f"| {ticker} | {val} | {weight} | {ret} | {drift} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Market Alerts
    alerts = market.get("alerts", [])
    lines.append(f"## ⚠️ Market Alerts ({len(alerts)} alerts)")
    if alerts:
        for a in alerts[:5]:
            sev = a.get('severity', 'low').upper()
            ticker = a.get('ticker', '').replace('.NS', '')
            desc = a.get('description', '')
            emoji = "🔴" if sev == "HIGH" else "🟡" if sev == "MEDIUM" else "🟢"
            lines.append(f"- {emoji} **[{sev}]** {ticker}: {desc}")
    else:
        lines.append("- 🟢 No significant alerts detected.")
    lines.append("")
    lines.append(f"**Macro Context:** {market.get('macro_summary', 'N/A')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Tax Opportunities
    total_saving = tax.get("total_potential_tax_saving", 0)
    lines.append(f"## 💰 Tax Opportunities (Est. Savings: {_format_inr(total_saving)})")
    lines.append("")
    lines.append(f"{tax.get('tax_summary', 'No tax summary available.')}")
    lines.append("")

    harvest = tax.get("harvest_opportunities", [])
    if harvest:
        lines.append("**Loss Harvesting Opportunities:**")
        for opp in harvest[:3]:
            ticker = opp.get('ticker', '').replace('.NS', '')
            loss = _format_inr(opp.get('loss_amount', 0))
            saving = _format_inr(opp.get('estimated_tax_saving', 0))
            htype = opp.get('holding_type', 'N/A')
            lines.append(f"- **{ticker}** ({htype}): Book {loss} loss → Tax saving: {saving}")
        lines.append("")

    elss = tax.get("elss_recommendation")
    if elss:
        amt = _format_inr(elss.get('recommended_amount', 0))
        saving = _format_inr(elss.get('estimated_tax_saving', 0))
        fund = elss.get('suggested_fund', 'ELSS Fund')
        lines.append(f"**Section 80C / ELSS:** Invest {amt} in {fund} — Est. saving: {saving}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Behavioral Profile
    scores = behavioral.get("risk_profile", {})
    lines.append("## 🧠 Behavioral Profile")
    if scores:
        lines.append("| Dimension | Score | Status |")
        lines.append("|-----------|-------|--------|")
        for dim, score in scores.items():
            dim_label = dim.replace("_", " ").title()
            if score > 7:
                status = "🔴 High Risk"
            elif score > 4:
                status = "🟡 Moderate"
            else:
                status = "🟢 Low"
            lines.append(f"| {dim_label} | {score}/10 | {status} |")
    lines.append("")

    flags = behavioral.get("flags", [])
    if flags:
        lines.append("**Flags:**")
        for f in flags:
            lines.append(f"- ⚠️ {f}")
        lines.append("")

    points = behavioral.get("coaching_points", [])
    if points:
        lines.append("**Coaching Points:**")
        for i, p in enumerate(points, 1):
            lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Sector & Macro Research
    sector = research.get("sector_outlook", {})
    lines.append("## 🔬 Sector & Macro Research")
    if sector:
        for s, outlook in sector.items():
            lines.append(f"- **{s}:** {outlook}")
    lines.append("")

    indicators = research.get("key_indicators", [])
    if indicators:
        lines.append("**Key Indicators:**")
        for ind in indicators:
            lines.append(f"- {ind.get('title', '')}: {ind.get('summary', '')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Suggested Agenda
    agenda = brief.get("suggested_agenda", [])
    lines.append("## 📅 Suggested Meeting Agenda")
    if agenda:
        for item in agenda:
            lines.append(f"- {item}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Talking Points
    tp = brief.get("talking_points", [])
    lines.append("## 💬 Talking Points")
    if tp:
        for i, point in enumerate(tp, 1):
            lines.append(f"{i}. {point}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Follow-Up Email
    lines.append("## ✉️ Draft Follow-Up Email")
    lines.append(f"**Subject:** Following Up on Our Meeting — {metadata.get('client_name', 'Client')}")
    lines.append("")
    lines.append(brief.get("draft_follow_up_email", "Draft email will be generated."))
    lines.append("")
    lines.append("---")
    lines.append(f"*Generated by WealthVisor · {metadata.get('generated_at', '')} · "
                 f"Generation time: {brief.get('generation_time_sec', 0):.1f}s*")

    return "\n".join(lines)


def brief_node(state: dict) -> dict:
    """
    LangGraph node: Brief Agent (Final Synthesizer).
    Takes all agent outputs and produces the structured meeting brief.
    """
    start_time = time.time()
    logger.info("[Brief Agent] Starting — synthesizing all agent outputs")
    errors = list(state.get("errors", []))

    try:
        client = state.get("client_profile", {})
        portfolio = state.get("portfolio_summary", {})
        performance = state.get("portfolio_performance", {})
        client_name = client.get("name", "Client")

        # Compile data context for LLM calls
        data_context = (
            f"Client: {client_name}, Age: {client.get('age')}, "
            f"Risk: {client.get('risk_tolerance')}, Goal: {client.get('investment_goal')}\n"
            f"AUM: {_format_inr(client.get('aum', 0))}\n"
            f"Portfolio 30d: {performance.get('return_30d', 0):+.1f}% | "
            f"vs NIFTY: {performance.get('vs_nifty_30d', 0):+.1f}%\n"
            f"YTD: {performance.get('ytd_return', 0):+.1f}% | "
            f"vs NIFTY YTD: {performance.get('vs_nifty_ytd', 0):+.1f}%\n"
        )

        # Market alerts summary
        alerts = state.get("market_alerts", [])
        high_alerts = [a for a in alerts if a.get("severity") == "high"]
        data_context += f"Market alerts: {len(alerts)} total, {len(high_alerts)} high-severity\n"
        if high_alerts:
            data_context += f"Top alert: {high_alerts[0].get('description', '')}\n"

        # Tax summary
        data_context += f"Tax summary: {state.get('tax_summary', 'N/A')}\n"
        harvest = []
        ltcg = state.get("ltcg_opportunities", [])
        stcg = state.get("stcg_items", [])

        # Collect harvest opportunities from the tax result
        tax_harvest = []
        for item in ltcg + stcg:
            if item.get("unrealized_gain", 0) < -5000:
                is_long_term = item.get("holding_type") == "long_term"
                tax_saving = abs(item["unrealized_gain"]) * (0.10 if is_long_term else 0.15)
                tax_harvest.append({
                    **item,
                    "loss_amount": abs(item["unrealized_gain"]),
                    "estimated_tax_saving": tax_saving
                })

        # Behavioral flags
        flags = state.get("behavioral_flags", [])
        if flags:
            data_context += f"Behavioral flags: {'; '.join(flags[:2])}\n"
        scores = state.get("behavioral_scores", {})
        high_risk_dims = [k for k, v in scores.items() if v > 7]
        if high_risk_dims:
            data_context += f"High-risk behavioral dimensions: {', '.join(high_risk_dims)}\n"

        # ─── Step 1: Generate executive summary ─────────────────────────
        exec_summary = _safe_llm_call(
            EXECUTIVE_SUMMARY_PROMPT,
            data_context + "\nGenerate the 3-sentence executive summary.",
            f"Portfolio valued at {_format_inr(portfolio.get('total_value', 0))} with "
            f"{performance.get('return_30d', 0):+.1f}% 30-day return. "
            f"Review tax optimization opportunities. "
            f"Monitor client's behavioral response to recent market movements."
        )

        # ─── Step 2: Generate suggested agenda ──────────────────────────
        meeting_duration = 60  # default
        agenda_raw = _safe_llm_call(
            AGENDA_PROMPT,
            data_context + f"\nMeeting duration: {meeting_duration} minutes.\nGenerate exactly 5 agenda items.",
            "10 min — Portfolio Review: Discuss overall performance vs NIFTY 50\n"
            "15 min — Market Outlook: Review key alerts and sector performance\n"
            "10 min — Tax Planning: Discuss LTCG/STCG optimization and ELSS\n"
            "15 min — Risk & Allocation: Review rebalancing needs and risk profile\n"
            "10 min — Action Items: Agree on next steps and follow-up timeline"
        )
        agenda = [line.strip() for line in agenda_raw.split("\n") if line.strip() and len(line.strip()) > 10][:5]

        # ─── Step 3: Generate talking points ─────────────────────────────
        tp_raw = _safe_llm_call(
            TALKING_POINTS_PROMPT,
            data_context + "\nGenerate exactly 4 talking points.",
            "1. Your portfolio continues to perform well relative to the NIFTY 50 benchmark.\n"
            "2. We have identified tax optimization opportunities worth exploring before the fiscal year end.\n"
            "3. Market conditions suggest maintaining current allocation with minor adjustments.\n"
            "4. I recommend we schedule a follow-up in 3 months to reassess."
        )
        talking_points = []
        for line in tp_raw.split("\n"):
            cleaned = line.strip().lstrip("0123456789.-) ").strip()
            if cleaned and len(cleaned) > 15:
                talking_points.append(cleaned)
        talking_points = talking_points[:4]

        # ─── Step 4: Generate follow-up email ────────────────────────────
        email = _safe_llm_call(
            FOLLOW_UP_EMAIL_PROMPT,
            f"Client name: {client_name}\n{data_context}\nGenerate the follow-up email.",
            f"Dear {client_name},\n\n"
            f"Thank you for taking the time to meet today. We discussed your portfolio performance, "
            f"tax optimization strategies, and your investment outlook.\n\n"
            f"Key action items:\n"
            f"- [INSERT AGREED ACTION 1]\n"
            f"- [INSERT AGREED ACTION 2]\n\n"
            f"I'll follow up on these items within the next week. "
            f"Let's schedule our next review for [DATE].\n\n"
            f"Warm regards,\n[ADVISOR NAME]"
        )

        # ─── Step 5: Build the complete brief dict ───────────────────────
        generation_time = time.time() - start_time

        # Prepare tax opportunities
        elss = state.get("elss_recommendation")
        tax_opportunities = {
            "ltcg_items": state.get("ltcg_opportunities", [])[:5],
            "stcg_items": state.get("stcg_items", [])[:5],
            "harvest_opportunities": tax_harvest[:5],
            "elss_recommendation": elss,
            "tax_summary": state.get("tax_summary", ""),
            "total_potential_tax_saving": sum(
                abs(i.get("unrealized_gain", 0)) * 0.10
                for i in tax_harvest
            ) + (elss.get("estimated_tax_saving", 0) if elss else 0),
        }

        meeting_brief = {
            "metadata": {
                "client_name": client_name,
                "client_id": state["client_id"],
                "meeting_at": state.get("meeting_scheduled_at", datetime.now()).isoformat()
                    if hasattr(state.get("meeting_scheduled_at", ""), "isoformat")
                    else str(state.get("meeting_scheduled_at", "")),
                "meeting_type": state.get("meeting_type", "review"),
                "generated_at": datetime.utcnow().isoformat(),
                "advisor_aum_this_client": portfolio.get("total_value", 0),
            },
            "executive_summary": exec_summary,
            "portfolio": {
                "total_value": portfolio.get("total_value", 0),
                "performance": performance,
                "asset_allocation": portfolio.get("asset_allocation", {}),
                "top_holdings": portfolio.get("top_holdings", []),
                "rebalancing_candidates": portfolio.get("rebalancing_candidates", []),
            },
            "market_intelligence": {
                "macro_summary": state.get("market_summary", ""),
                "alerts": state.get("market_alerts", [])[:5],
                "relevant_news": state.get("relevant_news", [])[:5],
            },
            "tax_opportunities": tax_opportunities,
            "behavioral_intelligence": {
                "risk_profile": state.get("behavioral_scores", {}),
                "flags": state.get("behavioral_flags", []),
                "coaching_points": state.get("coaching_points", []),
            },
            "macro_research": {
                "sector_outlook": state.get("sector_outlook", {}),
                "key_indicators": state.get("macro_research", []),
            },
            "suggested_agenda": agenda,
            "talking_points": talking_points,
            "draft_follow_up_email": email,
            "generation_time_sec": round(generation_time, 1),
            "errors": errors,
        }

        # ─── Step 6: Generate markdown ───────────────────────────────────
        brief_markdown = generate_markdown(meeting_brief)

        # ─── Step 7: Save to SQLite + Qdrant ─────────────────────────────
        try:
            db = SessionLocal()
            save_brief(db, state["meeting_id"], meeting_brief)
            db.close()
            logger.info(f"[Brief Agent] Saved brief to SQLite for meeting {state['meeting_id']}")
        except Exception as e:
            logger.error(f"[Brief Agent] Failed to save to SQLite: {e}")
            errors.append(f"Brief save to SQLite failed: {str(e)}")

        try:
            upsert_brief(state["client_id"], state["meeting_id"], brief_markdown)
            logger.info(f"[Brief Agent] Saved brief to Qdrant for meeting {state['meeting_id']}")
        except Exception as e:
            logger.error(f"[Brief Agent] Failed to save to Qdrant: {e}")
            errors.append(f"Brief save to Qdrant failed: {str(e)}")

        elapsed = time.time() - start_time
        logger.info(f"[Brief Agent] Completed in {elapsed:.1f}s — Brief generated successfully")

        return {
            "meeting_brief": meeting_brief,
            "brief_markdown": brief_markdown,
            "generation_time_sec": round(elapsed, 1),
            "errors": errors,
        }

    except Exception as e:
        logger.error(f"[Brief Agent] FAILED: {e}")
        errors.append(f"Brief agent error: {str(e)}")
        return {
            "meeting_brief": state.get("meeting_brief"),
            "brief_markdown": state.get("brief_markdown"),
            "errors": errors,
        }
