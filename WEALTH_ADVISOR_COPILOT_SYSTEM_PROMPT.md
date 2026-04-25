# Agentic Wealth Advisor Copilot — Complete System Prompt & Build Specification

> **For the AI building this project:** Read this document in full before writing a single line of code.
> Every section is a contract — not a suggestion. Do not deviate, skip, or simplify any step.
> When in doubt, follow the spec exactly. This document is the ground truth.

---

## 0. Project Identity

| Field | Value |
|---|---|
| **Project name** | WealthVisor — Agentic Pre-Meeting Intelligence System |
| **Target user** | Financial advisor at a wealth management firm (Morgan Stanley / JP Morgan persona) |
| **Core problem solved** | Advisors spend 2–4 hours manually preparing for each client meeting. This system eliminates that entirely. |
| **What it produces** | A one-page AI-generated meeting brief, delivered 30 minutes before each scheduled meeting, containing: portfolio snapshot, market relevance alerts, tax opportunities, behavioral risk flags, and draft talking points |
| **Architecture type** | Multi-agent LangGraph pipeline with a local SQLite portfolio database, FastAPI backend, and React frontend |
| **Primary framework** | LangGraph (multi-agent orchestration) |
| **LLM** | OpenAI GPT-4o (via API key in `.env`) |
| **Database** | SQLite (local, file-based, zero setup) — replaces all CRM/Salesforce dependencies |
| **Target metrics** | Brief generated in < 90 seconds · 100% meeting coverage · 0 manual data pulls |

---

## 1. Problem Statement (Memorize This)

This is not a chatbot. This is not a report generator. This is a proactive, autonomous multi-agent system that:

1. **Senses** an upcoming client meeting (by reading the meetings table in SQLite)
2. **Thinks** across 6 specialist agents simultaneously, each with a specific task
3. **Acts** by pulling real market data, running tax calculations, and scoring behavioral risk
4. **Remembers** every output in a persistent vector store (Qdrant) for future context

The advisor never opens a terminal. The system runs as a scheduled job (APScheduler), checks for meetings in the next 30 minutes, and pushes a brief to the React dashboard automatically.

**What this project is NOT:**
- It is NOT a simple RAG chatbot that answers questions
- It is NOT a dashboard that shows portfolio charts
- It is NOT a rule-based report generator
- It IS a fully autonomous agent network that makes decisions, fetches live data, and generates a structured output without human intervention

---

## 2. Complete File & Folder Structure

Build this structure exactly. Do not add or remove folders.

```
wealth-copilot/
├── backend/
│   ├── main.py                    # FastAPI entry point
│   ├── scheduler.py               # APScheduler — checks for meetings every 5 min
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator.py        # LangGraph StateGraph definition + supervisor node
│   │   ├── portfolio_agent.py     # Agent 1: reads SQLite, computes portfolio metrics
│   │   ├── market_agent.py        # Agent 2: fetches live prices + news via yfinance + NewsAPI
│   │   ├── tax_agent.py           # Agent 3: scans for TLH + Roth conversion opportunities
│   │   ├── behavioral_agent.py    # Agent 4: scores client behavioral risk profile
│   │   ├── research_agent.py      # Agent 5: fetches macro research relevant to portfolio
│   │   └── brief_agent.py         # Agent 6: synthesizes all outputs into final brief
│   ├── database/
│   │   ├── __init__.py
│   │   ├── schema.py              # SQLAlchemy models — defines all tables
│   │   ├── seed.py                # Seeds 10 synthetic clients + 3 upcoming meetings
│   │   └── crud.py                # All read/write functions — NO raw SQL in agents
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── market_tools.py        # yfinance wrappers — price, return, volatility
│   │   ├── news_tools.py          # NewsAPI + FinBERT sentiment scoring
│   │   ├── tax_tools.py           # TLH scanner, wash-sale checker, Roth estimator
│   │   └── vector_store.py        # Qdrant client wrapper — store + retrieve past briefs
│   ├── models/
│   │   ├── __init__.py
│   │   └── state.py               # TypedDict: CopilotState — shared state across all agents
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── Dashboard.tsx      # Main advisor view — meeting list + brief viewer
│   │   │   ├── ClientCard.tsx     # Client summary card
│   │   │   ├── BriefViewer.tsx    # Renders the generated brief in formatted sections
│   │   │   ├── PortfolioChart.tsx # Recharts pie chart of asset allocation
│   │   │   ├── TaxAlerts.tsx      # TLH + Roth opportunity cards
│   │   │   ├── BehavioralRadar.tsx # Recharts radar chart of 6 behavioral dimensions
│   │   │   └── MarketFeed.tsx     # Scrollable market news relevant to client
│   │   └── api/
│   │       └── client.ts          # All API calls to FastAPI — no fetch() calls in components
│   ├── package.json
│   └── tsconfig.json
├── data/
│   └── wealth_visor.db          # SQLite database file — auto-created by seed.py
├── .env.example                   # Template for environment variables
├── docker-compose.yml             # Runs backend + Qdrant together
└── README.md
```

---

## 3. Database Schema (Build Exactly As Specified)

**File: `backend/database/schema.py`**

Use SQLAlchemy ORM. Define 6 tables. Do not use raw SQL. Do not add extra columns without explicit instruction.

### Table 1: `clients`
```python
class Client(Base):
    __tablename__ = "clients"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    name            = Column(String, nullable=False)           # "Sarah Johnson"
    email           = Column(String, unique=True, nullable=False)
    phone           = Column(String)
    age             = Column(Integer)
    occupation      = Column(String)                           # "Senior VP, Google"
    risk_tolerance  = Column(String)                           # "moderate", "aggressive", "conservative"
    investment_goal = Column(String)                           # "retirement", "wealth_growth", "income"
    tax_bracket     = Column(Float)                            # 0.37 (37%)
    annual_income   = Column(Float)                            # 450000.0
    aum             = Column(Float)                            # 2500000.0 (assets under management)
    advisor_notes   = Column(Text)                             # Free-text historical notes
    behavioral_score= Column(JSON)                             # {"loss_aversion": 7, "overconfidence": 4, ...}
    created_at      = Column(DateTime, default=datetime.utcnow)
    # relationships
    holdings        = relationship("Holding", back_populates="client")
    meetings        = relationship("Meeting", back_populates="client")
    tax_lots        = relationship("TaxLot", back_populates="client")
    interactions    = relationship("Interaction", back_populates="client")
```

### Table 2: `holdings`
One row per ticker per client. This is the current portfolio.
```python
class Holding(Base):
    __tablename__ = "holdings"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    client_id       = Column(Integer, ForeignKey("clients.id"), nullable=False)
    ticker          = Column(String, nullable=False)            # "AAPL"
    asset_class     = Column(String, nullable=False)            # "equity", "bond", "etf", "cash", "alt"
    quantity        = Column(Float, nullable=False)             # 150.0 (shares)
    purchase_price  = Column(Float, nullable=False)             # 142.50 (cost basis per share)
    purchase_date   = Column(Date, nullable=False)              # date("2022-03-15")
    target_weight   = Column(Float)                             # 0.15 (15% of portfolio)
    client          = relationship("Client", back_populates="holdings")
```

### Table 3: `tax_lots`
One row per tax lot (one purchase event). A client may hold the same ticker across multiple lots.
```python
class TaxLot(Base):
    __tablename__ = "tax_lots"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    client_id       = Column(Integer, ForeignKey("clients.id"), nullable=False)
    ticker          = Column(String, nullable=False)
    quantity        = Column(Float, nullable=False)
    cost_basis      = Column(Float, nullable=False)             # per share
    purchase_date   = Column(Date, nullable=False)
    lot_type        = Column(String, nullable=False)            # "long_term" or "short_term"
    # long_term = held > 365 days; short_term = held <= 365 days
    client          = relationship("Client", back_populates="tax_lots")
```

### Table 4: `meetings`
```python
class Meeting(Base):
    __tablename__ = "meetings"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    client_id       = Column(Integer, ForeignKey("clients.id"), nullable=False)
    scheduled_at    = Column(DateTime, nullable=False)          # future datetime
    duration_min    = Column(Integer, default=60)
    meeting_type    = Column(String)                            # "quarterly_review", "onboarding", "adhoc"
    agenda_notes    = Column(Text)                              # advisor's pre-meeting notes
    brief_generated = Column(Boolean, default=False)
    brief_content   = Column(JSON)                             # stores the final generated brief dict
    brief_generated_at = Column(DateTime)
    client          = relationship("Client", back_populates="meetings")
```

### Table 5: `interactions`
Historical log of all advisor-client interactions.
```python
class Interaction(Base):
    __tablename__ = "interactions"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    client_id       = Column(Integer, ForeignKey("clients.id"), nullable=False)
    interaction_date = Column(Date, nullable=False)
    type            = Column(String)                            # "meeting", "email", "call", "note"
    summary         = Column(Text)                              # "Client expressed concern about tech exposure"
    sentiment       = Column(String)                            # "positive", "neutral", "negative", "anxious"
    client          = relationship("Client", back_populates="interactions")
```

### Table 6: `market_cache`
Prevents re-fetching market data for the same ticker within 15 minutes.
```python
class MarketCache(Base):
    __tablename__ = "market_cache"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    ticker          = Column(String, nullable=False)
    fetched_at      = Column(DateTime, nullable=False)
    current_price   = Column(Float)
    price_30d_ago   = Column(Float)
    price_1y_ago    = Column(Float)
    ytd_return      = Column(Float)
    volatility_30d  = Column(Float)                             # annualized
    beta            = Column(Float)
```

---

## 4. Seed Data (Build All 10 Clients)

**File: `backend/database/seed.py`**

This file must create exactly 10 synthetic clients with realistic data. Run it once at startup if the DB is empty.

The 10 clients must span:
- 3 different risk tolerances (conservative, moderate, aggressive)
- 3 different investment goals (retirement, wealth_growth, income)
- 3 different tax brackets (0.24, 0.32, 0.37)
- AUM ranging from $500,000 to $5,000,000
- Ages ranging from 35 to 68

Each client must have:
- 5–8 holdings in their portfolio (mix of equities, ETFs, bonds)
- 3–5 tax lots per holding
- 3–5 past interactions
- At least 1 upcoming meeting (scheduled within the next 48 hours for demo purposes)

**Use these specific tickers so all market data fetches succeed:**
```python
EQUITY_TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "JPM", "BRK-B", "JNJ", "V"]
ETF_TICKERS    = ["SPY", "QQQ", "VTI", "AGG", "BND", "GLD", "VNQ", "IWM", "IEFA", "VEA"]
BOND_TICKERS   = ["TLT", "IEF", "SHY", "LQD", "HYG"]
```

**Seed 3 upcoming meetings** (scheduled 25 minutes from now, 2 hours from now, and tomorrow morning) so the scheduler immediately triggers one brief on first run.

---

## 5. Shared State Definition

**File: `backend/models/state.py`**

This TypedDict is passed through every node in the LangGraph. Every agent reads from and writes to this object. Never pass data between agents any other way.

```python
from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime

class CopilotState(TypedDict):
    # Input (set by orchestrator before graph starts)
    meeting_id:             int
    client_id:              int
    meeting_scheduled_at:   datetime
    meeting_type:           str

    # Populated by portfolio_agent
    client_profile:         Dict[str, Any]       # full client row as dict
    portfolio_summary:      Dict[str, Any]        # total_value, asset_allocation, top_holdings, drift
    portfolio_performance:  Dict[str, Any]        # 30d_return, ytd_return, vs_benchmark

    # Populated by market_agent
    market_alerts:          List[Dict[str, Any]]  # [{ticker, alert_type, description, severity}]
    relevant_news:          List[Dict[str, Any]]  # [{headline, source, sentiment_score, relevance}]
    market_summary:         str                   # 2-sentence macro context

    # Populated by tax_agent
    tlh_opportunities:      List[Dict[str, Any]]  # [{ticker, unrealized_loss, tax_saving, replacement}]
    roth_opportunity:       Optional[Dict]         # {recommended_amount, tax_saving_estimate, reasoning}
    tax_summary:            str                   # Plain-English summary of tax actions

    # Populated by behavioral_agent
    behavioral_scores:      Dict[str, float]      # {loss_aversion, overconfidence, herding, recency, anchoring, status_quo}
    behavioral_flags:       List[str]             # ["Client may panic-sell if portfolio drops >8%"]
    coaching_points:        List[str]             # Advisor talking points for behavioral coaching

    # Populated by research_agent
    macro_research:         List[Dict[str, Any]]  # [{title, summary, relevance_score, source}]
    sector_outlook:         Dict[str, str]        # {tech: "cautious", financials: "positive", ...}

    # Populated by brief_agent (final output)
    meeting_brief:          Optional[Dict]        # Complete structured brief
    brief_markdown:         Optional[str]         # Human-readable markdown version

    # Control flags
    errors:                 List[str]             # Any agent errors — never raise exceptions
    generation_time_sec:    Optional[float]
```

---

## 6. Agent Definitions

### 6.1 Orchestrator (Supervisor Node)

**File: `backend/agents/orchestrator.py`**

Build the LangGraph StateGraph here. Use the **parallel fan-out** pattern: after reading the client profile, run agents 1–5 simultaneously using `asyncio.gather`, then pipe their outputs into brief_agent.

```
START
  │
  ▼
[portfolio_agent]  ← reads SQLite + yfinance for current prices
  │
  ├──────────────────────────────────────────┐
  ▼                  ▼                       ▼
[market_agent]  [tax_agent]  [behavioral_agent]  [research_agent]
  │                  │                  │                 │
  └──────────────────┴──────────────────┴─────────────────┘
                          │
                          ▼
                   [brief_agent]
                          │
                          ▼
                  [save to SQLite + Qdrant]
                          │
                          ▼
                        END
```

**Critical implementation details for the orchestrator:**
- Define the graph using `StateGraph(CopilotState)`
- portfolio_agent runs FIRST and alone, because all other agents depend on `portfolio_summary`
- The 4 middle agents (market, tax, behavioral, research) run in PARALLEL using `asyncio.gather`
- brief_agent runs LAST and alone, because it depends on all other agents' outputs
- If ANY agent fails, write the error to `state["errors"]` and continue — never let one agent crash the pipeline
- Add a `human_review` interrupt point after brief_agent generates the brief but before saving — use LangGraph's `interrupt_after=["brief_agent"]` so the advisor can optionally edit before it's finalized

---

### 6.2 Portfolio Agent

**File: `backend/agents/portfolio_agent.py`**

**Inputs:** `meeting_id`, `client_id` from state
**Outputs:** Writes `client_profile`, `portfolio_summary`, `portfolio_performance` to state

**Step-by-step logic (implement every step):**

**Step 1: Load client profile**
- Call `crud.get_client_with_holdings(client_id)` — returns client row + all holdings
- Store full client dict in `state["client_profile"]`

**Step 2: Fetch current prices for all tickers**
- Get unique tickers from holdings list
- For each ticker, check `market_cache` table: if `fetched_at` is within 15 minutes, use cached price
- Otherwise, call `market_tools.get_current_price(ticker)` (yfinance)
- Save new prices to `market_cache` table

**Step 3: Compute portfolio metrics**
```
For each holding:
  current_value = quantity × current_price
  cost_basis = quantity × purchase_price
  unrealized_gain_loss = current_value - cost_basis
  unrealized_return_pct = (current_value - cost_basis) / cost_basis

portfolio_total_value = sum(all holding current_values)

For each holding:
  actual_weight = current_value / portfolio_total_value
  drift = actual_weight - target_weight

asset_allocation = {
  "equity": sum of current_values where asset_class == "equity",
  "etf":    ...,
  "bond":   ...,
  "cash":   ...,
  "alt":    ...
}
```

**Step 4: Compute performance**
- Fetch 30-day-ago price and 1-year-ago price for each ticker from yfinance (use `history(period="1y")`)
- Compute portfolio 30d return and YTD return using weighted average
- Compare against SPY return over same period (benchmark)

**Step 5: Identify top 3 drifted holdings**
- Sort holdings by `abs(drift)` descending
- Mark top 3 as "rebalancing candidates" in portfolio_summary

**Step 6: Write to state**
```python
state["portfolio_summary"] = {
    "total_value": portfolio_total_value,
    "asset_allocation": asset_allocation,
    "holdings": [enhanced holding dicts with current_value, drift, unrealized_return_pct],
    "top_holdings": top 3 by current_value,
    "rebalancing_candidates": top 3 by abs(drift),
    "total_unrealized_gain": sum of all unrealized gains where positive,
    "total_unrealized_loss": sum of all unrealized losses where negative
}
state["portfolio_performance"] = {
    "return_30d": ...,
    "ytd_return": ...,
    "vs_spy_30d": return_30d - spy_return_30d,
    "vs_spy_ytd": ytd_return - spy_ytd_return
}
```

---

### 6.3 Market Agent

**File: `backend/agents/market_agent.py`**

**Inputs:** `client_profile`, `portfolio_summary` from state
**Outputs:** Writes `market_alerts`, `relevant_news`, `market_summary` to state

**Dependencies:**
- `yfinance` for price data
- `NewsAPI` (free tier, 100 requests/day) for news headlines — store key in `.env` as `NEWS_API_KEY`
- `FinBERT` (ProsusAI/finbert on HuggingFace) for sentiment scoring of headlines

**Step-by-step logic:**

**Step 1: Identify client's held tickers**
- Extract all tickers from `portfolio_summary["holdings"]`

**Step 2: Fetch news for each ticker**
- For each ticker, call NewsAPI: `GET https://newsapi.org/v2/everything?q={ticker}&from={7_days_ago}&sortBy=relevance&pageSize=5`
- Total articles: up to 5 per ticker, max 40 articles total (to avoid rate limits)
- Deduplicate by URL

**Step 3: Score each headline with FinBERT**
- Load `ProsusAI/finbert` model ONCE at module level (not inside the function)
- Score each headline: outputs `{positive, negative, neutral}` probabilities
- `sentiment_score = positive_prob - negative_prob` (range -1 to +1)
- Mark articles with `sentiment_score < -0.4` as negative alerts
- Mark articles with `sentiment_score > 0.5` as positive signals

**Step 4: Generate market alerts**
For each ticker with at least one negative article:
```python
{
  "ticker": "NVDA",
  "alert_type": "negative_news",    # or "price_drop", "high_volatility", "drift"
  "description": "3 negative articles in past 7 days",
  "severity": "high",               # "low", "medium", "high"
  "articles": [list of top 2 negative headlines]
}
```

Also generate price-based alerts:
- If 30d return < -10%: severity = "high", alert_type = "price_drop"
- If 30d return < -5%: severity = "medium", alert_type = "price_drop"
- If annualized 30d volatility > 40%: alert_type = "high_volatility"

**Step 5: Generate macro market summary**
- Fetch SPY, AGG, GLD, TLT current data (macro proxies)
- Use LLM to write a 2-sentence macro context: "Equity markets have declined X% in the past 30 days, driven by [macro factor]. Bond yields are [direction], suggesting [implication for client's fixed income holdings]."
- Call GPT-4o with a structured prompt — do not hardcode the summary

**Step 6: Write to state**
- `state["market_alerts"]` = list of alert dicts, sorted by severity (high first)
- `state["relevant_news"]` = top 10 articles by absolute sentiment score
- `state["market_summary"]` = 2-sentence macro string

---

### 6.4 Tax Agent

**File: `backend/agents/tax_agent.py`**

**Inputs:** `client_profile`, `portfolio_summary` from state (which contains current prices)
**Outputs:** Writes `tlh_opportunities`, `roth_opportunity`, `tax_summary` to state

**Dependencies:** `tax_tools.py` — all logic lives there, not in the agent

**Step-by-step logic:**

**Step 1: Run TLH scanner**
Call `tax_tools.scan_tlh_opportunities(client_id, portfolio_summary, current_prices)` which:
- Reads all `tax_lots` for the client from SQLite
- For each lot: `unrealized_loss = (current_price - cost_basis) × quantity`
- Only consider lots where `unrealized_loss < -500` (threshold: $500 minimum loss to harvest)
- Check wash-sale compliance: flag the lot ONLY if no purchase of the SAME ticker was made in the past 30 days (check interactions table and purchase_date of other lots)
- For each harvestable lot, suggest a replacement security using the ETF pairs map:

```python
WASH_SALE_REPLACEMENT_MAP = {
    # Equities → sector ETF (different underlying)
    "AAPL": ("QQQ", "Tracks different index from stock"),
    "MSFT": ("VGT", "Vanguard IT ETF — broad sector exposure"),
    "GOOGL": ("OGIG", "Internet & e-commerce ETF"),
    "AMZN": ("OGIG", "Internet & e-commerce ETF"),
    "NVDA": ("SOXX", "Semiconductor ETF"),
    "META": ("SOCL", "Global social media ETF"),
    # ETFs → different-index equivalent
    "SPY": ("VTI", "Total market vs S&P 500"),
    "QQQ": ("ONEQ", "Fidelity Nasdaq vs Invesco Nasdaq"),
    "VTI": ("ITOT", "iShares total market"),
    "AGG": ("BND", "Vanguard vs iShares agg bond"),
    "TLT": ("VGLT", "Vanguard long-term treasury"),
    # Default fallback
    "DEFAULT": ("VTI", "Broad market ETF")
}
```

- Compute `tax_saving = unrealized_loss × client.tax_bracket`
- Return list of TLH opportunities sorted by `tax_saving` descending

**Step 2: Run Roth conversion estimator**
Call `tax_tools.estimate_roth_opportunity(client_profile)` which:
- Check if client has a traditional IRA (infer from `investment_goal == "retirement"` and `age > 50`)
- Estimate current marginal rate from `tax_bracket`
- Apply simple Roth conversion logic:
  - If `client.age < 59.5` AND `client.annual_income < 400000`: suggest converting up to the top of current bracket
  - Compute `conversion_amount = next_bracket_threshold - estimated_taxable_income`
  - Compute `estimated_tax_saving = conversion_amount × (future_rate_estimate - current_rate_estimate)`
- If no Roth opportunity applies, return None

**Step 3: Write plain-English summary**
Use GPT-4o to generate a 3-sentence tax summary:
- Sentence 1: Total potential tax savings across all TLH opportunities
- Sentence 2: Most impactful opportunity specifically
- Sentence 3: Roth conversion recommendation or "No Roth opportunity identified"

**Step 4: Write to state**
```python
state["tlh_opportunities"] = [sorted list of TLH opportunity dicts]
state["roth_opportunity"] = {Roth dict or None}
state["tax_summary"] = "3-sentence plain-English summary"
```

---

### 6.5 Behavioral Agent

**File: `backend/agents/behavioral_agent.py`**

**Inputs:** `client_profile`, `portfolio_summary`, `portfolio_performance` from state
**Outputs:** Writes `behavioral_scores`, `behavioral_flags`, `coaching_points` to state

**Background:** This agent implements a simplified Kahneman-Tversky behavioral finance framework. It scores the client on 6 dimensions and generates advisor coaching points.

**Step 1: Load base behavioral scores**
- Read `client.behavioral_score` from SQLite (a JSON column populated during seed)
- Base scores are set during client onboarding (1–10 scale)
- These are the starting point, not the final score

**Step 2: Adjust scores dynamically based on current data**

Apply these adjustment rules — each rule modifies a base score:

```
RULE: Portfolio down >10% in 30 days?
  → loss_aversion score += 2 (client more likely to panic sell)
  → flag: "Portfolio has declined {X}% in 30 days — client may request defensive repositioning"

RULE: Client age > 60 AND risk_tolerance == "aggressive"?
  → status_quo score += 3 (inconsistency between stated risk and life stage)
  → flag: "Risk tolerance misalignment: aggressive stance at age {age} conflicts with retirement timeline"

RULE: Portfolio has >40% concentration in single sector?
  → overconfidence score += 2
  → flag: "High sector concentration ({sector}: {pct}%) may indicate overconfidence in that sector"

RULE: Client has 3+ negative sentiment interactions in past 60 days?
  → recency_bias score += 2
  → flag: "Negative interaction pattern suggests heightened anxiety — avoid leading with losses"

RULE: Portfolio performance vs benchmark negative by >5% over 30d?
  → anchoring score += 1
  → flag: "Underperformance vs SPY may trigger anchoring to previous high-water mark"

RULE: Client's actual allocation drifted significantly from target?
  → status_quo score += 2 (client may resist rebalancing)
  → flag: "Portfolio has drifted from target — expect resistance to recommended rebalancing"
```

Cap all scores at 10. Minimum is 1.

**Step 3: Generate coaching points using GPT-4o**
Pass all behavioral scores + flags to GPT-4o with this system prompt:
```
You are a behavioral finance expert advising a financial advisor before a client meeting.
Given these behavioral risk scores for [client name], generate exactly 3 coaching points.
Each coaching point is 1-2 sentences.
Format: "If the client mentions [scenario], respond by [advisor action] because [behavioral reasoning]."
Do not give generic advice. Make each point specific to this client's scores and portfolio.
Scores: {behavioral_scores}
Flags: {behavioral_flags}
Portfolio 30d return: {portfolio_performance.return_30d}
Client age: {client_profile.age}
Risk tolerance: {client_profile.risk_tolerance}
```

**Step 4: Write to state**
```python
state["behavioral_scores"] = final_adjusted_scores_dict
state["behavioral_flags"] = list_of_flag_strings
state["coaching_points"] = list_of_3_coaching_point_strings
```

---

### 6.6 Research Agent

**File: `backend/agents/research_agent.py`**

**Inputs:** `client_profile`, `portfolio_summary`, `market_alerts` from state
**Outputs:** Writes `macro_research`, `sector_outlook` to state

**Dependencies:**
- `yfinance` for sector ETF performance (use sector SPDR ETFs: XLK, XLF, XLE, XLV, XLY, etc.)
- FRED API (Federal Reserve Economic Data) — free, no key required for basic endpoints
- Qdrant vector store — retrieve past relevant research briefs

**Step 1: Determine client's sector exposure**
- From `portfolio_summary["holdings"]`, map each ticker to its sector
- Use a hardcoded sector map for the seed tickers:
```python
SECTOR_MAP = {
    "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Technology",
    "AMZN": "Consumer Discretionary", "NVDA": "Technology", "META": "Technology",
    "JPM": "Financials", "V": "Financials", "JNJ": "Healthcare",
    "BRK-B": "Financials", "SPY": "Broad Market", "QQQ": "Technology",
    "VTI": "Broad Market", "AGG": "Fixed Income", "BND": "Fixed Income",
    "TLT": "Fixed Income", "GLD": "Commodities", "VNQ": "Real Estate",
    # ... add all seed tickers
}
```
- Compute sector weights as percentage of portfolio

**Step 2: Fetch sector performance data**
- For each sector the client is exposed to (weight > 5%), fetch the corresponding sector ETF's 30d return
- Use SPDR sector ETFs: XLK (tech), XLF (financials), XLV (health), XLE (energy), XLY (consumer disc)
- Classify each sector as: "outperforming" (>2% vs SPY), "in-line" (-2% to +2%), "underperforming" (<-2%)

**Step 3: Fetch 2 macro FRED indicators**
Call these 2 FRED endpoints (no API key needed):
- 10-year Treasury yield: `https://fred.stlouisfed.org/graph/fredgraph.csv?id=GS10`
- Federal Funds Rate: `https://fred.stlouisfed.org/graph/fredgraph.csv?id=FEDFUNDS`
- Parse the CSV, get latest value and direction (rising/falling vs 3 months ago)

**Step 4: Retrieve past briefs from Qdrant**
- Query Qdrant with the query: `f"portfolio review for {client_profile['name']} sector exposure research"`
- Return top 2 past brief summaries (if any exist) — used by brief_agent for continuity context

**Step 5: Generate sector outlook**
Use GPT-4o to write a 1-sentence outlook for each of the client's top 3 sectors:
- Input: sector name, 30d ETF return, 10Y treasury direction, client's weight in that sector
- Output: `{"Technology": "Tech remains under pressure from rising rates; client's 42% tech exposure warrants discussion.", ...}`

**Step 6: Write to state**
```python
state["macro_research"] = [
    {
        "title": "10Y Treasury at X%",
        "summary": "...",
        "relevance_score": 0.85,
        "source": "FRED"
    },
    ...
]
state["sector_outlook"] = {sector_name: one_sentence_outlook, ...}
```

---

### 6.7 Brief Agent (Final Synthesizer)

**File: `backend/agents/brief_agent.py`**

**Inputs:** ALL fields from state (portfolio_summary, market_alerts, tlh_opportunities, behavioral_scores, macro_research, sector_outlook, etc.)
**Outputs:** Writes `meeting_brief` (dict) and `brief_markdown` (string) to state

**This is the most important agent.** It takes everything from all 5 previous agents and produces a structured, advisor-ready meeting brief.

**Step 1: Build the brief dict**
```python
meeting_brief = {
    "metadata": {
        "client_name": state["client_profile"]["name"],
        "client_id": state["client_id"],
        "meeting_at": state["meeting_scheduled_at"].isoformat(),
        "meeting_type": state["meeting_type"],
        "generated_at": datetime.utcnow().isoformat(),
        "advisor_aum_this_client": state["portfolio_summary"]["total_value"]
    },
    "executive_summary": "",       # 3-sentence GPT-generated summary of everything critical
    "portfolio": {
        "total_value": ...,
        "performance": state["portfolio_performance"],
        "asset_allocation": state["portfolio_summary"]["asset_allocation"],
        "top_holdings": state["portfolio_summary"]["top_holdings"],
        "rebalancing_candidates": state["portfolio_summary"]["rebalancing_candidates"]
    },
    "market_intelligence": {
        "macro_summary": state["market_summary"],
        "alerts": state["market_alerts"],          # max 5, sorted by severity
        "relevant_news": state["relevant_news"][:5]
    },
    "tax_opportunities": {
        "tlh_opportunities": state["tlh_opportunities"],  # max 3 highest-value
        "roth_opportunity": state["roth_opportunity"],
        "tax_summary": state["tax_summary"],
        "total_potential_tax_saving": sum(opp["tax_saving"] for opp in state["tlh_opportunities"])
    },
    "behavioral_intelligence": {
        "risk_profile": state["behavioral_scores"],
        "flags": state["behavioral_flags"],
        "coaching_points": state["coaching_points"]
    },
    "macro_research": {
        "sector_outlook": state["sector_outlook"],
        "key_indicators": state["macro_research"]
    },
    "suggested_agenda": [],         # GPT-generated 5-point meeting agenda
    "talking_points": [],           # GPT-generated 4 advisor talking points
    "draft_follow_up_email": ""     # GPT-generated draft email for after the meeting
}
```

**Step 2: Generate executive summary with GPT-4o**
System prompt:
```
You are an elite financial advisor's assistant. Generate a 3-sentence executive summary
for a client meeting brief. Sentence 1: portfolio status and performance. 
Sentence 2: the single most urgent action item (tax, rebalance, or risk alert).
Sentence 3: one behavioral note the advisor must keep in mind.
Be specific. Use numbers. Never be vague.
```
User message: pass JSON of portfolio_performance, market_alerts[:2], tlh_opportunities[:1], behavioral_flags[:1]

**Step 3: Generate suggested agenda with GPT-4o**
Produce exactly 5 agenda items as a list of strings. Format each as: "10 min — [Topic]: [one sentence why this matters for THIS client]"

**Step 4: Generate talking points with GPT-4o**
Produce exactly 4 talking points. Each is 2 sentences max. Format: numbered list. Ground every point in specific data from the state (specific numbers, tickers, percentages).

**Step 5: Generate draft follow-up email with GPT-4o**
Subject: `f"Following Up on Our Meeting — [client_name]"`
Body: Professional, 150 words, references specific items discussed. Include placeholders like `[INSERT AGREED ACTION]` for advisor to fill in.

**Step 6: Write to state and save**
```python
state["meeting_brief"] = meeting_brief
state["brief_markdown"] = generate_markdown(meeting_brief)  # See Section 7
```

Then call:
```python
crud.save_brief(meeting_id, meeting_brief)   # updates meetings table
vector_store.upsert_brief(client_id, meeting_id, brief_markdown)   # saves to Qdrant
```

---

## 7. Markdown Brief Format

**Function: `generate_markdown(brief: dict) -> str`**

This function lives in `brief_agent.py`. It converts the brief dict to a formatted markdown string for display in the React frontend. Build it exactly as specified:

```markdown
# 📋 Meeting Brief: {client_name}
**{meeting_type}** · {formatted_datetime} · AUM: ${total_value:,.0f}

---

## 🔑 Executive Summary
{executive_summary}

---

## 📊 Portfolio Snapshot
**Total Value:** ${total_value:,.0f}  
**30-Day Return:** {return_30d:+.2f}% (SPY: {spy_30d:+.2f}%)  
**YTD Return:** {ytd_return:+.2f}% (SPY: {spy_ytd:+.2f}%)

**Asset Allocation:**
- Equity: {equity_pct:.1f}%
- ETF: {etf_pct:.1f}%
- Fixed Income: {bond_pct:.1f}%
- Cash: {cash_pct:.1f}%

**Top Holdings:**
| Ticker | Value | Weight | Return 30d | Drift |
|--------|-------|--------|------------|-------|
| {ticker} | ${value:,.0f} | {weight:.1f}% | {ret30d:+.1f}% | {drift:+.1f}% |

---

## ⚠️ Market Alerts ({n} alerts)
{for each alert: "**[{severity.upper()}]** {ticker}: {description}"}

**Macro Context:** {macro_summary}

---

## 💰 Tax Opportunities (Est. Savings: ${total_saving:,.0f})
{for each TLH opportunity:
"- **{ticker}** ({lot_type} term): Harvest ${loss:,.0f} loss → Buy {replacement} 
  Tax saving: ${tax_saving:,.0f} · Wash-sale safe: ✓"
}
{if roth_opportunity: "**Roth Conversion:** {roth_reasoning} — Est. saving: ${saving:,.0f}"}

---

## 🧠 Behavioral Profile
| Dimension | Score | Status |
|-----------|-------|--------|
| Loss Aversion | {score}/10 | {🔴 if >7, 🟡 if >4, 🟢} |
| Overconfidence | ... | ... |

**Flags:**
{for each flag: "- ⚠️ {flag}"}

**Coaching Points:**
{for each point: "{n}. {coaching_point}"}

---

## 🔬 Sector & Macro Research
{for each sector_outlook: "- **{sector}:** {outlook}"}

---

## 📅 Suggested Meeting Agenda
{for each agenda_item: "{item}"}

---

## 💬 Talking Points
{for each talking_point: "{n}. {talking_point}"}

---

## ✉️ Draft Follow-Up Email
**Subject:** {subject}

{email_body}

---
*Generated by WealthVisor · {generated_at} · Generation time: {time_sec:.1f}s*
```

---

## 8. API & Tools Layer

### 8.1 Market Tools (`backend/tools/market_tools.py`)

```python
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_current_price(ticker: str) -> float:
    """Returns latest closing price. Never raises — returns None on failure."""

def get_price_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Returns OHLCV DataFrame. period: '1mo', '3mo', '6mo', '1y', '2y'"""

def compute_return(ticker: str, days: int) -> float:
    """Returns % return over last N calendar days. Negative if declined."""

def compute_annualized_volatility(ticker: str, days: int = 30) -> float:
    """Returns annualized volatility (std of daily returns * sqrt(252))"""

def get_benchmark_return(days: int) -> float:
    """Returns SPY return over last N days."""

def get_sector_etf_return(sector_etf: str, days: int = 30) -> float:
    """Fetches return for a sector SPDR ETF (XLK, XLF, etc.)"""
```

**Error handling rule:** Every function in `market_tools.py` must catch all exceptions and return `None` or `0.0` on failure. The pipeline must never crash because of a market data fetch failure.

### 8.2 News Tools (`backend/tools/news_tools.py`)

```python
import requests
from transformers import pipeline

# Load FinBERT ONCE at module level — not inside functions
_finbert = pipeline("text-classification", model="ProsusAI/finbert", top_k=None)

def fetch_ticker_news(ticker: str, days_back: int = 7, max_articles: int = 5) -> list[dict]:
    """
    Calls NewsAPI. Returns list of dicts:
    {"title": str, "description": str, "url": str, "publishedAt": str, "source": str}
    Falls back to empty list if API fails or key not set.
    """

def score_sentiment(text: str) -> float:
    """
    Runs FinBERT on text. Returns sentiment_score = positive_prob - negative_prob.
    Range: -1.0 (very negative) to +1.0 (very positive).
    """

def score_articles(articles: list[dict]) -> list[dict]:
    """
    Adds sentiment_score to each article dict.
    Returns sorted list, most negative first.
    """
```

**FinBERT loading:** Load the model at module import time. If HuggingFace is unavailable, fall back to a simple keyword-based scorer (count positive/negative financial keywords). Never let FinBERT failure crash the pipeline.

### 8.3 Tax Tools (`backend/tools/tax_tools.py`)

```python
from datetime import date, timedelta

def scan_tlh_opportunities(
    tax_lots: list,         # from SQLite tax_lots table
    current_prices: dict,   # {ticker: current_price}
    tax_bracket: float,     # 0.37
    recent_purchases: list  # tax lots from last 30 days — for wash-sale check
) -> list[dict]:
    """
    Returns list of harvestable lots sorted by tax_saving descending.
    Each lot: {ticker, lot_id, quantity, cost_basis, current_price,
                unrealized_loss, tax_saving, replacement_ticker,
                replacement_reason, wash_sale_safe: bool,
                lot_type: "long_term"/"short_term"}
    Only returns lots where wash_sale_safe == True and unrealized_loss < -500.
    """

def check_wash_sale(
    ticker: str,
    sale_date: date,
    recent_purchases: list  # all lots with purchase_date
) -> bool:
    """
    Returns True if the sale is wash-sale SAFE (i.e., no purchase of same ticker
    within 30 days before or after sale_date).
    sale_date is today (the harvest date).
    Check: no lot with same ticker has purchase_date in [sale_date-30, sale_date+30].
    """

def estimate_roth_opportunity(
    age: int,
    tax_bracket: float,
    annual_income: float,
    investment_goal: str
) -> dict | None:
    """
    Returns Roth conversion recommendation or None.
    Logic:
    - Only applicable if investment_goal == "retirement"
    - If tax_bracket <= 0.24: suggest up to $50,000 conversion
    - If tax_bracket == 0.32: suggest up to $25,000 conversion
    - If tax_bracket == 0.37: no Roth opportunity (too high a rate)
    - If age > 73: flag RMD obligation instead
    Return: {recommended_amount, current_bracket, future_bracket_estimate, reasoning}
    """
```

### 8.4 Vector Store (`backend/tools/vector_store.py`)

**Use Qdrant running locally via Docker** (from `docker-compose.yml`). Collection name: `wealth_visor_briefs`.

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from openai import OpenAI

QDRANT_URL = "http://localhost:6333"
COLLECTION = "wealth_visor_briefs"
VECTOR_DIM = 1536  # text-embedding-3-small

def get_client() -> QdrantClient:
    """Returns initialized Qdrant client. Creates collection if not exists."""

def embed_text(text: str) -> list[float]:
    """Embeds using OpenAI text-embedding-3-small. Returns vector."""

def upsert_brief(client_id: int, meeting_id: int, brief_markdown: str) -> None:
    """
    Embeds brief_markdown and upserts to Qdrant.
    Payload: {client_id, meeting_id, timestamp, brief_markdown}
    Point ID: meeting_id
    """

def retrieve_past_briefs(client_id: int, query: str, top_k: int = 2) -> list[dict]:
    """
    Semantic search: finds past briefs for this client_id matching the query.
    Filter: payload.client_id == client_id
    Returns top_k results with payload.brief_markdown
    """
```

---

## 9. FastAPI Backend

**File: `backend/main.py`**

Define these exact endpoints. No other endpoints are needed.

```python
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="WealthVisor API", version="1.0.0")

# CORS: allow React frontend at http://localhost:5173
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], ...)

@app.get("/health")
async def health_check():
    """Returns {"status": "ok", "db": "connected", "qdrant": "connected"}"""

@app.get("/clients")
async def list_clients() -> list[dict]:
    """Returns all clients. Each dict: {id, name, aum, risk_tolerance, upcoming_meeting_count}"""

@app.get("/clients/{client_id}")
async def get_client(client_id: int) -> dict:
    """Returns full client profile with holdings, tax_lots, recent interactions, upcoming meetings."""

@app.get("/meetings")
async def list_meetings(upcoming_only: bool = True) -> list[dict]:
    """Returns meetings. upcoming_only=True filters to scheduled_at > now. Includes brief_generated status."""

@app.get("/meetings/{meeting_id}")
async def get_meeting(meeting_id: int) -> dict:
    """Returns full meeting including brief_content if already generated."""

@app.post("/meetings/{meeting_id}/generate-brief")
async def generate_brief(meeting_id: int, background_tasks: BackgroundTasks):
    """
    Triggers the LangGraph pipeline for this meeting.
    Runs in background. Returns immediately with {"status": "generating", "meeting_id": meeting_id}.
    Pipeline result saved to meetings.brief_content when done.
    """

@app.get("/meetings/{meeting_id}/brief")
async def get_brief(meeting_id: int) -> dict:
    """Returns the generated brief for a meeting. 404 if not yet generated."""

@app.get("/portfolio/{client_id}/snapshot")
async def portfolio_snapshot(client_id: int) -> dict:
    """Returns current portfolio snapshot without running the full pipeline."""

@app.get("/portfolio/{client_id}/tax-opportunities")
async def tax_opportunities(client_id: int) -> dict:
    """Returns TLH and Roth opportunities for a client."""
```

---

## 10. Scheduler

**File: `backend/scheduler.py`**

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('interval', minutes=5)
async def check_upcoming_meetings():
    """
    Every 5 minutes:
    1. Query meetings table for meetings where:
       - scheduled_at is between (now + 20 min) and (now + 40 min)
       - brief_generated == False
    2. For each such meeting, trigger the LangGraph pipeline
    3. Mark brief_generated = True once complete
    4. Log: "Brief generated for meeting {id} at {time}"
    """
```

Start scheduler on FastAPI startup:
```python
@app.on_event("startup")
async def startup():
    scheduler.start()
    # Also initialize DB and Qdrant collection here
```

---

## 11. React Frontend

**Technology:** React 18 + TypeScript + Vite + TailwindCSS + Recharts

### 11.1 Layout
- Left sidebar (240px): Client list with search
- Main content: switches between Dashboard and Meeting Brief view
- Top bar: "WealthVisor" logo + connection status indicator

### 11.2 Dashboard Component (`Dashboard.tsx`)
Shows:
1. **Upcoming Meetings section** — cards sorted by `scheduled_at`. Each card shows: client name, meeting time countdown, meeting type, AUM. "Generate Brief" button if `brief_generated == false`. "View Brief" button if `brief_generated == true`.
2. **Client Overview table** — sortable by AUM, name, risk tolerance

### 11.3 BriefViewer Component (`BriefViewer.tsx`)
Renders the generated brief in sections. Each section is a collapsible card. Include:
- `PortfolioChart.tsx`: Recharts PieChart of asset allocation
- `BehavioralRadar.tsx`: Recharts RadarChart of 6 behavioral dimensions (0–10)
- `TaxAlerts.tsx`: Cards for each TLH opportunity with a green "Est. Tax Saving: $X,XXX" badge
- `MarketFeed.tsx`: Scrollable list of news headlines with sentiment color coding (red for negative, green for positive, gray for neutral)

### 11.4 API Client (`api/client.ts`)
```typescript
const BASE = "http://localhost:8000";

export const api = {
  getClients: () => fetch(`${BASE}/clients`).then(r => r.json()),
  getClient: (id: number) => fetch(`${BASE}/clients/${id}`).then(r => r.json()),
  getMeetings: () => fetch(`${BASE}/meetings?upcoming_only=true`).then(r => r.json()),
  getMeeting: (id: number) => fetch(`${BASE}/meetings/${id}`).then(r => r.json()),
  generateBrief: (meetingId: number) => fetch(`${BASE}/meetings/${meetingId}/generate-brief`, {method: 'POST'}).then(r => r.json()),
  getBrief: (meetingId: number) => fetch(`${BASE}/meetings/${meetingId}/brief`).then(r => r.json()),
};
```

Poll `getBrief` every 3 seconds after triggering `generateBrief` until `brief_generated == true`.

---

## 12. Environment Variables

**File: `.env.example`** (copy to `.env` before running)

```env
# Required
OPENAI_API_KEY=sk-...

# Optional (NewsAPI free tier: newsapi.org)
NEWS_API_KEY=your_newsapi_key_here

# Do not change these unless you change docker-compose.yml
QDRANT_URL=http://localhost:6333
DB_PATH=./data/wealth_visor.db

# Set to false to skip FinBERT (uses keyword fallback instead)
USE_FINBERT=true
```

If `NEWS_API_KEY` is not set, the news tools must fall back to a hardcoded list of 3 recent financial news headlines (stored in a `FALLBACK_NEWS` constant) rather than crashing.

---

## 13. Docker Compose

**File: `docker-compose.yml`**

```yaml
version: "3.8"
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_storage:/qdrant/storage

volumes:
  qdrant_storage:
```

Only Qdrant runs in Docker. The FastAPI backend and React frontend run directly on the host machine.

---

## 14. Requirements

**File: `backend/requirements.txt`**

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.35
aiosqlite==0.20.0
langchain==0.3.0
langgraph==0.2.0
langchain-openai==0.2.0
openai==1.50.0
yfinance==0.2.43
pandas==2.2.3
numpy==1.26.4
transformers==4.45.0
torch==2.4.1
requests==2.32.3
apscheduler==3.10.4
qdrant-client==1.11.0
python-dotenv==1.0.1
httpx==0.27.2
```

---

## 15. Startup Sequence

When the developer runs the project for the first time, the exact sequence must be:

```bash
# Terminal 1: Start Qdrant
docker-compose up -d

# Terminal 2: Backend
cd backend
pip install -r requirements.txt
python database/seed.py    # creates DB + seeds 10 clients + 3 meetings
uvicorn main:app --reload --port 8000

# Terminal 3: Frontend
cd frontend
npm install
npm run dev
# → opens at http://localhost:5173
```

**On first run:** Scheduler detects the meeting seeded 25 minutes from now and automatically triggers the pipeline. Within 90 seconds, the brief appears in the dashboard.

---

## 16. Error Handling Rules (Non-Negotiable)

1. **Never raise exceptions from within an agent node.** Use try/except everywhere and append errors to `state["errors"]`.
2. **Never let a market data failure cascade.** If `yfinance` returns None, use the most recent cached price from SQLite. If no cache exists, use 0.0 and add a note to `state["errors"]`.
3. **Never let FinBERT failure crash news_agent.** Fall back to keyword sentiment scoring.
4. **Never let LLM failure crash brief_agent.** If GPT-4o call fails (rate limit, timeout), use a template string with available data and mark `brief_content["llm_used"] = false`.
5. **Log every agent's start time, end time, and error count** to stdout using Python's logging module (not print).

---

## 17. Key Metrics to Track and Display in the UI

The React dashboard must display these metrics at the top of the page as stat cards:

| Metric | How to compute |
|---|---|
| Briefs Generated Today | Count meetings where brief_generated == True AND brief_generated_at > today's midnight |
| Avg Generation Time | Average of brief_content.generation_time_sec across all briefs |
| Total Tax Savings Identified | Sum of all tlh_opportunities.tax_saving across all generated briefs |
| Clients with High Behavioral Risk | Count of clients where any behavioral_score > 7 |
| Active Meetings Today | Count of meetings scheduled today |

---

## 18. What Success Looks Like

After building this project, the following must work end-to-end:

1. Developer runs `seed.py` → 10 clients, portfolio data, and 3 upcoming meetings are created in SQLite.
2. Developer starts backend → scheduler runs and detects the meeting seeded 25 minutes from now.
3. Scheduler triggers the LangGraph pipeline for that meeting.
4. All 6 agents run: portfolio loads from SQLite, market data fetches from yfinance, news fetches from NewsAPI (or fallback), tax opportunities computed, behavioral scores adjusted, research fetched from FRED.
5. Brief agent synthesizes everything into a structured dict + markdown.
6. Brief saved to SQLite `meetings.brief_content` column + vectorized in Qdrant.
7. Developer opens React app at `localhost:5173` → sees the meeting with "View Brief" button.
8. Clicking "View Brief" renders a fully formatted brief with portfolio chart, radar chart, TLH cards, news feed, and talking points.
9. Total generation time: under 90 seconds on a standard laptop (most time is LLM calls).

---

## 19. Resume-Ready Metrics (What to Document When Complete)

When presenting this project on a resume or in an interview, use these framings:

- **"Engineered a 6-agent LangGraph pipeline"** — be specific about the agents and their roles
- **"Reduced meeting prep time from 2–4 hours to under 90 seconds"** — this is the headline metric
- **"Integrated yfinance, FinBERT, NewsAPI, and FRED"** — 4 live data sources
- **"Implemented Betterment/Wealthfront-grade TLH scanner"** — reference the industry standard
- **"Behavioral finance scoring across 6 Kahneman-Tversky dimensions"** — academic credibility
- **"Qdrant vector store for persistent meeting intelligence"** — MLOps / production-readiness signal
- **"Human-in-the-loop interrupt point via LangGraph"** — shows understanding of responsible AI

---

*End of System Prompt. Build exactly as specified. Every section is required.*
