"""
WealthVisor — Market Agent
Agent 2: Fetches live prices + news, scores sentiment, generates market alerts.
Uses Groq (Llama 3.1 70B) for macro summary. Indian market context.
"""

import os
import logging
import time
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from backend.tools.market_tools import compute_return, compute_annualized_volatility, get_benchmark_return
from backend.tools.news_tools import fetch_ticker_news, score_articles

logger = logging.getLogger(__name__)

MARKET_AGENT_SYSTEM_PROMPT = """You are an elite Indian equity market analyst working for a top wealth management firm in Mumbai.
Your role is to provide a concise 2-sentence macroeconomic summary for a financial advisor before a client meeting.

Context:
- You analyze the Indian stock market (NSE/BSE)
- Your benchmark is the NIFTY 50 index
- Key macro factors: RBI monetary policy, GDP growth, FII/DII flows, rupee movement, global commodity prices
- Your audience is a financial advisor, not the end client
- Be specific with numbers and percentages
- Use Indian market terminology (NIFTY, Sensex, FII, DII, RBI, rupee)

Format: Exactly 2 sentences. Sentence 1: Current market regime and recent performance.
Sentence 2: One key macro factor that could impact the client's portfolio in the next 30 days."""


def market_node(state: dict) -> dict:
    """
    LangGraph node: Market Agent.
    Fetches news, scores sentiment, generates price/volatility alerts,
    and produces a 2-sentence macro summary using Groq LLM.
    """
    start_time = time.time()
    logger.info("[Market Agent] Starting")
    errors = list(state.get("errors", []))

    market_alerts = []
    relevant_news = []
    market_summary = ""

    try:
        portfolio = state.get("portfolio_summary", {})
        holdings = portfolio.get("holdings", [])
        tickers = list(set(h["ticker"] for h in holdings))

        # ─── Step 1 & 2: Fetch and score news ───────────────────────────
        all_articles = []
        seen_urls = set()

        for ticker in tickers[:8]:  # limit to avoid rate limits
            articles = fetch_ticker_news(ticker, days_back=7, max_articles=5)
            for a in articles:
                url = a.get("url", "")
                if url not in seen_urls:
                    seen_urls.add(url)
                    a["related_ticker"] = ticker
                    all_articles.append(a)

        # Score sentiment
        scored_articles = score_articles(all_articles)

        # Top 10 by absolute sentiment
        relevant_news = sorted(scored_articles, key=lambda x: abs(x.get("sentiment_score", 0)), reverse=True)[:10]

        # ─── Step 3: Generate price-based alerts −────────────────────────
        for h in holdings:
            ticker = h["ticker"]
            ret_30d = h.get("return_30d", 0)
            vol = compute_annualized_volatility(ticker, 30)

            # Price drop alerts
            if ret_30d < -10:
                market_alerts.append({
                    "ticker": ticker,
                    "alert_type": "price_drop",
                    "description": f"{ticker.replace('.NS','')} has fallen {ret_30d:.1f}% in the last 30 days",
                    "severity": "high",
                    "value": ret_30d,
                })
            elif ret_30d < -5:
                market_alerts.append({
                    "ticker": ticker,
                    "alert_type": "price_drop",
                    "description": f"{ticker.replace('.NS','')} has declined {ret_30d:.1f}% in 30 days",
                    "severity": "medium",
                    "value": ret_30d,
                })

            # Volatility alerts
            if vol > 40:
                market_alerts.append({
                    "ticker": ticker,
                    "alert_type": "high_volatility",
                    "description": f"{ticker.replace('.NS','')} showing elevated volatility at {vol:.0f}% annualized",
                    "severity": "high" if vol > 60 else "medium",
                    "value": vol,
                })

        # News sentiment alerts
        for article in scored_articles:
            if article.get("sentiment_score", 0) < -0.4:
                ticker = article.get("related_ticker", "Market")
                market_alerts.append({
                    "ticker": ticker,
                    "alert_type": "negative_news",
                    "description": article.get("title", "Negative news detected")[:100],
                    "severity": "high" if article["sentiment_score"] < -0.7 else "medium",
                    "value": article["sentiment_score"],
                })

        # Sort by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        market_alerts.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 3))
        market_alerts = market_alerts[:10]  # cap at 10

        # ─── Step 4: Generate macro summary with Groq ────────────────────
        try:
            nifty_30d = get_benchmark_return(30)
            nifty_7d = get_benchmark_return(7)

            llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                temperature=0.3,
                max_tokens=200,
            )

            user_msg = (
                f"NIFTY 50 performance: 30-day return = {nifty_30d:+.1f}%, 7-day return = {nifty_7d:+.1f}%. "
                f"Number of high-severity alerts in client portfolio: {sum(1 for a in market_alerts if a['severity']=='high')}. "
                f"Client has {len(tickers)} holdings across NSE. "
                f"Generate the 2-sentence macro summary for the advisor."
            )

            response = llm.invoke([
                SystemMessage(content=MARKET_AGENT_SYSTEM_PROMPT),
                HumanMessage(content=user_msg),
            ])
            market_summary = response.content.strip()
        except Exception as e:
            logger.error(f"[Market Agent] LLM call failed: {e}")
            errors.append(f"Market agent LLM failed: {str(e)}")
            market_summary = (
                f"NIFTY 50 has moved {nifty_30d:+.1f}% over the past 30 days. "
                f"Monitor RBI policy signals and global risk appetite for near-term direction."
            )

    except Exception as e:
        logger.error(f"[Market Agent] FAILED: {e}")
        errors.append(f"Market agent error: {str(e)}")

    elapsed = time.time() - start_time
    logger.info(f"[Market Agent] Completed in {elapsed:.1f}s — {len(market_alerts)} alerts, {len(relevant_news)} articles")

    return {
        "market_alerts": market_alerts,
        "relevant_news": relevant_news,
        "market_summary": market_summary,
        "errors": errors,
    }
