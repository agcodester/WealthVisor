"""
WealthVisor — News Tools
NewsAPI fetcher + sentiment scoring.
Primary: VADER + Loughran-McDonald financial lexicon (lightweight, no torch).
Optional: FinBERT if USE_FINBERT=true in .env.

NewsAPI free tier: https://newsapi.org/register (100 requests/day)
"""

import os
import logging
from datetime import datetime, timedelta
import requests

logger = logging.getLogger(__name__)

# ─── VADER Sentiment (always available) ─────────────────────────────────────
try:
    import nltk
    nltk.download("vader_lexicon", quiet=True)
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    _vader = SentimentIntensityAnalyzer()
except Exception as e:
    logger.warning(f"VADER not available: {e}")
    _vader = None

# ─── FinBERT (optional, loaded only if USE_FINBERT=true) ────────────────────
_finbert = None
USE_FINBERT = os.getenv("USE_FINBERT", "false").lower() == "true"

if USE_FINBERT:
    try:
        from transformers import pipeline
        _finbert = pipeline("text-classification", model="ProsusAI/finbert", top_k=None)
        logger.info("FinBERT loaded successfully")
    except Exception as e:
        logger.warning(f"FinBERT not available, falling back to VADER: {e}")
        _finbert = None

# ─── Financial Lexicon (Loughran-McDonald–inspired keywords) ────────────────
POSITIVE_FINANCIAL_WORDS = {
    "growth", "profit", "surge", "rally", "bullish", "upgrade", "outperform",
    "breakout", "gains", "dividend", "earnings", "beat", "record", "strong",
    "momentum", "optimistic", "recovery", "expansion", "upside", "buy",
    "accumulate", "robust", "resilient", "attractive", "rebound",
}

NEGATIVE_FINANCIAL_WORDS = {
    "loss", "decline", "crash", "bearish", "downgrade", "underperform",
    "selloff", "correction", "debt", "default", "recession", "warning",
    "weak", "slump", "risk", "volatile", "cut", "drop", "fall", "miss",
    "concern", "fear", "uncertainty", "inflation", "sell", "pressure",
    "fraud", "scam", "probe", "investigation",
}

# ─── Fallback News (when NewsAPI key not set) ───────────────────────────────
FALLBACK_NEWS = [
    {
        "title": "NIFTY 50 holds steady amid global uncertainty",
        "description": "Indian benchmark indices showed resilience as FII flows remained mixed.",
        "url": "https://example.com/nifty-steady",
        "publishedAt": datetime.now().isoformat(),
        "source": "Financial Express",
    },
    {
        "title": "RBI holds repo rate steady at 6.5%, signals cautious outlook",
        "description": "The Reserve Bank of India kept rates unchanged, citing inflation concerns.",
        "url": "https://example.com/rbi-rate",
        "publishedAt": datetime.now().isoformat(),
        "source": "Economic Times",
    },
    {
        "title": "IT sector sees mixed earnings as global demand softens",
        "description": "TCS and Infosys report moderate growth, cautious on near-term guidance.",
        "url": "https://example.com/it-earnings",
        "publishedAt": datetime.now().isoformat(),
        "source": "Mint",
    },
]


def fetch_ticker_news(ticker: str, days_back: int = 7, max_articles: int = 5) -> list[dict]:
    """
    Fetches news from NewsAPI for the given ticker.
    Falls back to FALLBACK_NEWS if API key not set or request fails.
    """
    api_key = os.getenv("NEWS_API_KEY", "")
    if not api_key or api_key == "your_newsapi_key_here":
        logger.info(f"NewsAPI key not set, using fallback news for {ticker}")
        return FALLBACK_NEWS

    try:
        # Strip .NS/.BO suffix for search
        search_term = ticker.replace(".NS", "").replace(".BO", "")
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        url = "https://newsapi.org/v2/everything"
        params = {
            "q": f"{search_term} stock India",
            "from": from_date,
            "sortBy": "relevance",
            "pageSize": max_articles,
            "language": "en",
            "apiKey": api_key,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        articles = []
        for a in data.get("articles", []):
            articles.append({
                "title": a.get("title", ""),
                "description": a.get("description", ""),
                "url": a.get("url", ""),
                "publishedAt": a.get("publishedAt", ""),
                "source": a.get("source", {}).get("name", "Unknown"),
            })
        return articles
    except Exception as e:
        logger.error(f"NewsAPI fetch failed for {ticker}: {e}")
        return FALLBACK_NEWS


def _score_with_vader(text: str) -> float:
    """Scores text using VADER. Returns -1.0 to +1.0."""
    if _vader is None:
        return _score_with_lexicon(text)
    scores = _vader.polarity_scores(text)
    return scores["compound"]  # -1 to +1


def _score_with_lexicon(text: str) -> float:
    """Simple financial-keyword–based scorer. Returns -1.0 to +1.0."""
    words = text.lower().split()
    pos = sum(1 for w in words if w in POSITIVE_FINANCIAL_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_FINANCIAL_WORDS)
    total = pos + neg
    if total == 0:
        return 0.0
    return round((pos - neg) / total, 2)


def _score_with_finbert(text: str) -> float:
    """Scores text using FinBERT. Returns -1.0 to +1.0."""
    if _finbert is None:
        return _score_with_vader(text)
    try:
        results = _finbert(text[:512])  # FinBERT max 512 tokens
        scores_dict = {r["label"]: r["score"] for r in results[0]}
        pos = scores_dict.get("positive", 0)
        neg = scores_dict.get("negative", 0)
        return round(pos - neg, 4)
    except Exception as e:
        logger.error(f"FinBERT scoring failed, falling back to VADER: {e}")
        return _score_with_vader(text)


def score_sentiment(text: str) -> float:
    """
    Scores sentiment of text. Uses the best available method:
    1. FinBERT (if USE_FINBERT=true and loaded)
    2. VADER (default)
    3. Financial lexicon (final fallback)
    Returns: -1.0 (very negative) to +1.0 (very positive)
    """
    if not text:
        return 0.0
    if _finbert is not None:
        return _score_with_finbert(text)
    return _score_with_vader(text)


def score_articles(articles: list[dict]) -> list[dict]:
    """
    Adds sentiment_score to each article dict.
    Returns sorted list, most negative first.
    """
    scored = []
    for article in articles:
        text = f"{article.get('title', '')} {article.get('description', '')}"
        article["sentiment_score"] = score_sentiment(text)
        scored.append(article)
    scored.sort(key=lambda x: x["sentiment_score"])
    return scored
