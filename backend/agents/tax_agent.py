"""
WealthVisor — Tax Agent
Agent 3: Scans for LTCG/STCG tax optimization + ELSS/80C recommendations.
Uses Indian tax rules. Groq (Llama 3.1 70B) for plain-English summary.
"""

import logging
import time
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from backend.database import SessionLocal
from backend.database.crud import get_client_tax_lots
from backend.tools.tax_tools import scan_ltcg_stcg_opportunities, estimate_elss_opportunity, compute_tax_summary_data

logger = logging.getLogger(__name__)

TAX_AGENT_SYSTEM_PROMPT = """You are an expert Indian tax advisor specializing in capital gains tax for High Net Worth Individuals (HNIs).
You work at a premier wealth management firm and prepare concise tax optimization summaries for financial advisors.

Key Indian Tax Rules you must reference:
- LTCG on listed equity (held >12 months): 10% on gains above ₹1,00,000 exemption per financial year
- STCG on listed equity (held ≤12 months): 15% flat rate
- Section 80C: Up to ₹1,50,000 deduction via ELSS mutual funds (3-year lock-in)
- Losses can be set off: LTCL against LTCG, STCL against both STCG and LTCG
- Tax harvesting: Strategically booking losses to offset gains

Format: Generate exactly 3 sentences.
- Sentence 1: Total potential tax savings across all recommended actions.
- Sentence 2: The single most impactful tax optimization opportunity.
- Sentence 3: ELSS/80C recommendation or a note on capital loss carry-forward.

Use ₹ symbol for all amounts (Indian Rupee). Use Indian number format (lakhs/crores).
Be specific with ticker names, amounts, and percentages. Never be vague."""


def tax_node(state: dict) -> dict:
    """
    LangGraph node: Tax Agent.
    Scans all tax lots for LTCG/STCG implications, identifies harvesting
    opportunities, and recommends ELSS investments for Section 80C.
    """
    start_time = time.time()
    logger.info("[Tax Agent] Starting")
    errors = list(state.get("errors", []))

    ltcg_opportunities = []
    stcg_items = []
    elss_recommendation = None
    tax_summary = ""

    try:
        client = state.get("client_profile", {})
        portfolio = state.get("portfolio_summary", {})
        current_prices = portfolio.get("current_prices", {})

        # ─── Step 1: Run LTCG/STCG scanner ──────────────────────────────
        db = SessionLocal()
        tax_lots = get_client_tax_lots(db, state["client_id"])
        db.close()

        tax_result = scan_ltcg_stcg_opportunities(
            tax_lots=tax_lots,
            current_prices=current_prices,
            tax_bracket=client.get("tax_bracket", 0.30),
        )

        ltcg_opportunities = tax_result.get("ltcg_items", [])
        stcg_items = tax_result.get("stcg_items", [])

        # ─── Step 2: Run ELSS/80C estimator ──────────────────────────────
        elss_recommendation = estimate_elss_opportunity(
            age=client.get("age", 40),
            tax_bracket=client.get("tax_bracket", 0.30),
            annual_income=client.get("annual_income", 0),
            investment_goal=client.get("investment_goal", "wealth_growth"),
        )

        # ─── Step 3: Generate plain-English summary with Groq ───────────
        try:
            llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                temperature=0.3,
                max_tokens=300,
            )

            summary_data = compute_tax_summary_data(tax_result, elss_recommendation)

            user_msg = (
                f"Client: {client.get('name', 'Unknown')}, Age: {client.get('age')}, "
                f"Tax bracket: {client.get('tax_bracket', 0.30)*100:.0f}%\n"
                f"LTCG across portfolio: ₹{tax_result['total_ltcg']:,.0f}\n"
                f"STCG across portfolio: ₹{tax_result['total_stcg']:,.0f}\n"
                f"Estimated LTCG tax payable: ₹{tax_result['ltcg_tax_payable']:,.0f}\n"
                f"Estimated STCG tax payable: ₹{tax_result['stcg_tax_payable']:,.0f}\n"
                f"Harvest opportunities (losses to book): {len(tax_result['harvest_opportunities'])}\n"
            )

            if tax_result["harvest_opportunities"]:
                top_opp = tax_result["harvest_opportunities"][0]
                user_msg += (
                    f"Biggest harvest opportunity: {top_opp['ticker'].replace('.NS','')} — "
                    f"₹{top_opp['loss_amount']:,.0f} loss, est. tax saving ₹{top_opp['estimated_tax_saving']:,.0f}\n"
                )

            if elss_recommendation:
                user_msg += (
                    f"ELSS Recommendation: Invest ₹{elss_recommendation['recommended_amount']:,.0f} "
                    f"for ₹{elss_recommendation['estimated_tax_saving']:,.0f} tax saving under Section 80C\n"
                )
            else:
                user_msg += "ELSS: Section 80C limit already utilized or not applicable.\n"

            user_msg += "\nGenerate the 3-sentence tax summary."

            response = llm.invoke([
                SystemMessage(content=TAX_AGENT_SYSTEM_PROMPT),
                HumanMessage(content=user_msg),
            ])
            tax_summary = response.content.strip()
        except Exception as e:
            logger.error(f"[Tax Agent] LLM call failed: {e}")
            errors.append(f"Tax agent LLM failed: {str(e)}")
            # Template fallback
            total_saving = sum(o.get("estimated_tax_saving", 0) for o in tax_result.get("harvest_opportunities", []))
            if elss_recommendation:
                total_saving += elss_recommendation.get("estimated_tax_saving", 0)
            tax_summary = (
                f"Total potential tax saving identified: ₹{total_saving:,.0f}. "
                f"LTCG tax payable: ₹{tax_result['ltcg_tax_payable']:,.0f}, "
                f"STCG tax: ₹{tax_result['stcg_tax_payable']:,.0f}. "
                f"Consider ELSS investment for Section 80C benefits."
            )

    except Exception as e:
        logger.error(f"[Tax Agent] FAILED: {e}")
        errors.append(f"Tax agent error: {str(e)}")

    elapsed = time.time() - start_time
    logger.info(f"[Tax Agent] Completed in {elapsed:.1f}s")

    return {
        "ltcg_opportunities": ltcg_opportunities,
        "stcg_items": stcg_items,
        "elss_recommendation": elss_recommendation,
        "tax_summary": tax_summary,
        "errors": errors,
    }
