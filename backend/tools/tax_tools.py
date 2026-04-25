"""
WealthVisor — Tax Tools (Indian Tax Rules)
LTCG/STCG scanner for listed equity, Section 80C / ELSS advisor.
All amounts in INR (₹).

Indian Equity Tax Rules (FY 2024-25 onwards):
- LTCG: Listed equity held >12 months → 10% on gains above ₹1,00,000 exemption
- STCG: Listed equity held ≤12 months → 15% flat
- Section 80C: Up to ₹1,50,000 deduction (ELSS mutual funds qualify)
- No wash-sale rule in India (unlike US)
"""

import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)

# ─── ELSS & 80C Constants ──────────────────────────────────────────────────
SECTION_80C_LIMIT = 150000  # ₹1.5 lakh

ELSS_FUNDS = {
    "AXIS_ELSS": "Axis Long Term Equity Fund",
    "MIRAE_ELSS": "Mirae Asset ELSS Tax Saver",
    "QUANT_ELSS": "Quant ELSS Tax Saver Fund",
    "SBI_ELSS": "SBI Long Term Equity Fund",
    "DSP_ELSS": "DSP ELSS Tax Saver Fund",
}

# ─── Indian Tax Slabs (New Regime FY 2024-25) ──────────────────────────────
TAX_SLABS_NEW_REGIME = [
    (300000, 0.00),    # Up to ₹3 lakh: 0%
    (600000, 0.05),    # ₹3-6 lakh: 5%
    (900000, 0.10),    # ₹6-9 lakh: 10%
    (1200000, 0.15),   # ₹9-12 lakh: 15%
    (1500000, 0.20),   # ₹12-15 lakh: 20%
    (float("inf"), 0.30),  # Above ₹15 lakh: 30%
]


def scan_ltcg_stcg_opportunities(
    tax_lots: list[dict],
    current_prices: dict[str, float],
    tax_bracket: float,
) -> dict:
    """
    Scans all tax lots for LTCG and STCG implications.
    Returns categorized gains/losses for tax planning.

    Returns: {
        "ltcg_items": [...],       # long-term capital gains/losses
        "stcg_items": [...],       # short-term capital gains/losses
        "total_ltcg": float,       # net long-term gain
        "total_stcg": float,       # net short-term gain
        "ltcg_tax_payable": float, # estimated LTCG tax (10% above ₹1L)
        "stcg_tax_payable": float, # estimated STCG tax (15%)
        "harvest_opportunities": [...],  # losses that can offset gains
    }
    """
    ltcg_items = []
    stcg_items = []
    harvest_opportunities = []

    for lot in tax_lots:
        ticker = lot["ticker"]
        current_price = current_prices.get(ticker, 0)
        if current_price == 0:
            continue

        cost_basis = lot["cost_basis"]
        quantity = lot["quantity"]
        purchase_date = lot["purchase_date"]

        if isinstance(purchase_date, str):
            purchase_date = date.fromisoformat(purchase_date)

        days_held = (date.today() - purchase_date).days
        is_long_term = days_held > 365

        unrealized_gain = (current_price - cost_basis) * quantity
        unrealized_return_pct = ((current_price - cost_basis) / cost_basis * 100) if cost_basis > 0 else 0

        item = {
            "ticker": ticker,
            "lot_id": lot.get("id"),
            "quantity": quantity,
            "cost_basis": cost_basis,
            "current_price": current_price,
            "unrealized_gain": round(unrealized_gain, 2),
            "unrealized_return_pct": round(unrealized_return_pct, 2),
            "days_held": days_held,
            "holding_type": "long_term" if is_long_term else "short_term",
            "purchase_date": purchase_date.isoformat(),
        }

        if is_long_term:
            ltcg_items.append(item)
        else:
            stcg_items.append(item)

        # Harvest opportunity: if there's unrealized loss > ₹5,000
        if unrealized_gain < -5000:
            tax_saving = abs(unrealized_gain) * (0.10 if is_long_term else 0.15)
            harvest_opportunities.append({
                **item,
                "loss_amount": round(abs(unrealized_gain), 2),
                "estimated_tax_saving": round(tax_saving, 2),
                "action": f"Sell to realize {'LTCL' if is_long_term else 'STCL'} of ₹{abs(unrealized_gain):,.0f}",
            })

    # Compute totals
    total_ltcg = sum(i["unrealized_gain"] for i in ltcg_items)
    total_stcg = sum(i["unrealized_gain"] for i in stcg_items)

    # LTCG tax: 10% on gains above ₹1,00,000 exemption
    ltcg_taxable = max(total_ltcg - 100000, 0) if total_ltcg > 0 else 0
    ltcg_tax = ltcg_taxable * 0.10

    # STCG tax: 15% flat (only on gains, not losses)
    stcg_tax = max(total_stcg, 0) * 0.15

    # Sort by impact
    ltcg_items.sort(key=lambda x: abs(x["unrealized_gain"]), reverse=True)
    stcg_items.sort(key=lambda x: abs(x["unrealized_gain"]), reverse=True)
    harvest_opportunities.sort(key=lambda x: x["estimated_tax_saving"], reverse=True)

    return {
        "ltcg_items": ltcg_items,
        "stcg_items": stcg_items,
        "total_ltcg": round(total_ltcg, 2),
        "total_stcg": round(total_stcg, 2),
        "ltcg_tax_payable": round(ltcg_tax, 2),
        "stcg_tax_payable": round(stcg_tax, 2),
        "total_tax_payable": round(ltcg_tax + stcg_tax, 2),
        "harvest_opportunities": harvest_opportunities[:5],  # top 5
    }


def estimate_elss_opportunity(
    age: int,
    tax_bracket: float,
    annual_income: float,
    investment_goal: str,
    existing_80c_investments: float = 0,
) -> dict | None:
    """
    Recommends ELSS investment for Section 80C tax saving.
    Returns recommendation or None if 80C is already maxed.
    """
    remaining_80c = max(SECTION_80C_LIMIT - existing_80c_investments, 0)

    if remaining_80c <= 0:
        return None

    # Recommended ELSS amount
    recommended = min(remaining_80c, 150000)
    tax_saving = recommended * tax_bracket

    # Pick ELSS fund based on risk profile
    if investment_goal == "retirement" and age > 50:
        fund = "SBI_ELSS"
        reasoning = f"Conservative ELSS fund suitable for your age ({age}) and retirement focus."
    elif investment_goal == "wealth_growth":
        fund = "QUANT_ELSS"
        reasoning = "Growth-oriented ELSS fund with strong historical returns for wealth accumulation."
    else:
        fund = "MIRAE_ELSS"
        reasoning = "Balanced ELSS fund with consistent performance across market cycles."

    return {
        "recommended_amount": recommended,
        "remaining_80c_limit": remaining_80c,
        "estimated_tax_saving": round(tax_saving, 2),
        "suggested_fund": ELSS_FUNDS[fund],
        "lock_in_period": "3 years",
        "reasoning": reasoning,
    }


def compute_tax_summary_data(
    ltcg_stcg_result: dict,
    elss_result: dict | None,
) -> dict:
    """Computes aggregate tax data for the summary."""
    total_potential_saving = 0.0

    # From loss harvesting
    for opp in ltcg_stcg_result.get("harvest_opportunities", []):
        total_potential_saving += opp.get("estimated_tax_saving", 0)

    # From ELSS
    if elss_result:
        total_potential_saving += elss_result.get("estimated_tax_saving", 0)

    return {
        "total_potential_tax_saving": round(total_potential_saving, 2),
        "ltcg_tax_payable": ltcg_stcg_result.get("ltcg_tax_payable", 0),
        "stcg_tax_payable": ltcg_stcg_result.get("stcg_tax_payable", 0),
        "harvest_count": len(ltcg_stcg_result.get("harvest_opportunities", [])),
        "elss_recommended": elss_result is not None,
    }
