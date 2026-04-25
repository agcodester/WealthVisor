"""
WealthVisor — Portfolio Agent
Agent 1: Reads SQLite, fetches live NSE prices, computes portfolio metrics.
Benchmarks against NIFTY 50. All values in INR (₹).
"""

import logging
import time
from datetime import datetime
from backend.database import SessionLocal
from backend.database.crud import get_client_with_holdings, get_cached_price, upsert_market_cache
from backend.tools.market_tools import (
    get_current_price, compute_return, get_benchmark_return,
    get_price_n_days_ago,
)

logger = logging.getLogger(__name__)


def portfolio_node(state: dict) -> dict:
    """
    LangGraph node: Portfolio Agent.
    Reads client profile + holdings from SQLite, fetches live NSE prices,
    computes portfolio metrics, performance, and drift analysis.
    """
    start_time = time.time()
    logger.info(f"[Portfolio Agent] Starting for client_id={state.get('client_id')}")
    errors = list(state.get("errors", []))

    try:
        db = SessionLocal()

        # ─── Step 1: Load client profile ─────────────────────────────────
        client_data = get_client_with_holdings(db, state["client_id"])
        if not client_data:
            errors.append(f"Client {state['client_id']} not found in database")
            db.close()
            return {"errors": errors}

        # ─── Step 2: Fetch current prices (with cache) ──────────────────
        holdings = client_data["holdings"]
        tickers = list(set(h["ticker"] for h in holdings))
        current_prices = {}

        for ticker in tickers:
            # Check cache first (15-min window)
            cached = get_cached_price(db, ticker)
            if cached and cached.current_price:
                current_prices[ticker] = cached.current_price
                logger.debug(f"  Cache hit: {ticker} = ₹{cached.current_price}")
            else:
                price = get_current_price(ticker)
                if price is not None:
                    current_prices[ticker] = price
                    # Update cache
                    upsert_market_cache(db, ticker, {"current_price": price})
                    logger.debug(f"  Live fetch: {ticker} = ₹{price}")
                else:
                    current_prices[ticker] = 0.0
                    errors.append(f"Could not fetch price for {ticker}, using ₹0")

        # ─── Step 3: Compute portfolio metrics ───────────────────────────
        enhanced_holdings = []
        total_value = 0.0
        total_unrealized_gain = 0.0
        total_unrealized_loss = 0.0
        asset_allocation = {}

        for h in holdings:
            cp = current_prices.get(h["ticker"], 0)
            current_value = h["quantity"] * cp
            cost_basis_total = h["quantity"] * h["purchase_price"]
            unrealized_gl = current_value - cost_basis_total
            unrealized_return_pct = (
                ((current_value - cost_basis_total) / cost_basis_total * 100)
                if cost_basis_total > 0 else 0
            )
            total_value += current_value

            if unrealized_gl >= 0:
                total_unrealized_gain += unrealized_gl
            else:
                total_unrealized_loss += unrealized_gl

            enhanced_holdings.append({
                **h,
                "current_price": cp,
                "current_value": round(current_value, 2),
                "cost_basis_total": round(cost_basis_total, 2),
                "unrealized_gain_loss": round(unrealized_gl, 2),
                "unrealized_return_pct": round(unrealized_return_pct, 2),
            })

            # Asset allocation
            ac = h["asset_class"]
            asset_allocation[ac] = asset_allocation.get(ac, 0) + current_value

        # Compute weights and drift
        for eh in enhanced_holdings:
            if total_value > 0:
                actual_weight = eh["current_value"] / total_value
            else:
                actual_weight = 0
            target_weight = eh.get("target_weight", 0) or 0
            drift = actual_weight - target_weight
            eh["actual_weight"] = round(actual_weight, 4)
            eh["drift"] = round(drift, 4)

        # Convert allocation to percentages
        allocation_pct = {}
        for ac, val in asset_allocation.items():
            allocation_pct[ac] = round((val / total_value * 100) if total_value > 0 else 0, 1)

        # Top 3 holdings by value
        top_holdings = sorted(enhanced_holdings, key=lambda x: x["current_value"], reverse=True)[:3]

        # Top 3 drifted holdings (rebalancing candidates)
        rebalancing_candidates = sorted(enhanced_holdings, key=lambda x: abs(x["drift"]), reverse=True)[:3]

        # ─── Step 4: Compute performance ─────────────────────────────────
        # Portfolio weighted returns
        portfolio_return_30d = 0.0
        portfolio_return_ytd = 0.0

        for eh in enhanced_holdings:
            weight = eh["actual_weight"]
            ticker = eh["ticker"]
            ret_30d = compute_return(ticker, 30)
            ret_ytd = compute_return(ticker, 365)
            eh["return_30d"] = ret_30d
            eh["return_ytd"] = ret_ytd
            portfolio_return_30d += weight * ret_30d
            portfolio_return_ytd += weight * ret_ytd

        # NIFTY 50 benchmark
        nifty_return_30d = get_benchmark_return(30)
        nifty_return_ytd = get_benchmark_return(365)

        # ─── Step 5: Write to state ──────────────────────────────────────
        portfolio_summary = {
            "total_value": round(total_value, 2),
            "asset_allocation": allocation_pct,
            "asset_allocation_values": {k: round(v, 2) for k, v in asset_allocation.items()},
            "holdings": enhanced_holdings,
            "top_holdings": top_holdings,
            "rebalancing_candidates": rebalancing_candidates,
            "total_unrealized_gain": round(total_unrealized_gain, 2),
            "total_unrealized_loss": round(total_unrealized_loss, 2),
            "current_prices": current_prices,
        }

        portfolio_performance = {
            "return_30d": round(portfolio_return_30d, 2),
            "ytd_return": round(portfolio_return_ytd, 2),
            "nifty_30d": round(nifty_return_30d, 2),
            "nifty_ytd": round(nifty_return_ytd, 2),
            "vs_nifty_30d": round(portfolio_return_30d - nifty_return_30d, 2),
            "vs_nifty_ytd": round(portfolio_return_ytd - nifty_return_ytd, 2),
        }

        db.close()
        elapsed = time.time() - start_time
        logger.info(f"[Portfolio Agent] Completed in {elapsed:.1f}s — Portfolio value: ₹{total_value:,.0f}")

        return {
            "client_profile": client_data,
            "portfolio_summary": portfolio_summary,
            "portfolio_performance": portfolio_performance,
            "errors": errors,
        }

    except Exception as e:
        logger.error(f"[Portfolio Agent] FAILED: {e}")
        errors.append(f"Portfolio agent error: {str(e)}")
        return {
            "client_profile": state.get("client_profile", {}),
            "portfolio_summary": state.get("portfolio_summary", {}),
            "portfolio_performance": state.get("portfolio_performance", {}),
            "errors": errors,
        }
