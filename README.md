# 🏛️ WealthVisor — Agentic Pre-Meeting Intelligence System

> **An AI-powered multi-agent system that generates comprehensive pre-meeting intelligence briefs for Indian wealth advisors managing HNI/UHNI portfolios.**

WealthVisor uses a **LangGraph orchestration pipeline** with 6 autonomous AI agents running in a parallel fan-out/fan-in architecture. It fetches live NSE market data, scans for Indian tax optimization opportunities (LTCG/STCG/Section 80C), applies Kahneman-Tversky behavioral finance frameworks, and synthesizes everything into a single actionable advisor brief — all in under 60 seconds.

---

## 🎯 Problem Statement

Wealth advisors in India spend **2-3 hours** manually preparing for each HNI client meeting:

- Reviewing portfolio positions across multiple systems
- Checking current NSE prices and market movements
- Analyzing LTCG/STCG tax implications under Indian tax law
- Recalling client behavioral patterns and past meeting notes
- Reading sector research and macro indicators

**WealthVisor automates this entire workflow into a single click**, delivering a professionally formatted intelligence brief with actionable insights, coaching points, and even a draft follow-up email.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        WealthVisor Pipeline                        │
│                    (LangGraph StateGraph)                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌──────────────────┐                                             │
│   │  Portfolio Agent  │  ← Superstep 1 (Sequential)                │
│   │  (SQLite + NSE)  │                                             │
│   └────────┬─────────┘                                             │
│            │                                                        │
│   ┌────────┼───────────────────────────────────────┐               │
│   │        │         PARALLEL FAN-OUT              │               │
│   │   ┌────▼────┐ ┌────────┐ ┌────────────┐ ┌─────▼────┐         │
│   │   │ Market  │ │  Tax   │ │ Behavioral │ │ Research │         │
│   │   │ Agent   │ │ Agent  │ │   Agent    │ │  Agent   │         │
│   │   │(yfinance│ │(LTCG/  │ │(Kahneman- │ │(News +   │         │
│   │   │+ News)  │ │STCG/   │ │ Tversky)  │ │ Qdrant)  │         │
│   │   │         │ │80C)    │ │           │ │          │         │
│   │   └────┬────┘ └───┬────┘ └─────┬─────┘ └────┬─────┘         │
│   │        │           │            │             │               │
│   └────────┼───────────┼────────────┼─────────────┘               │
│            │           │            │                              │
│   ┌────────▼───────────▼────────────▼──────────────┐              │
│   │              Brief Agent (Synthesizer)          │  ← Superstep 3 │
│   │         Groq Llama 3.3 70B Versatile           │              │
│   └────────────────────┬───────────────────────────┘              │
│                        │                                           │
│                   ┌────▼────┐                                      │
│                   │  JSON   │  → Frontend / API                    │
│                   │  Brief  │                                      │
│                   └─────────┘                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Why This Architecture?

| Design Decision | Rationale |
|:---|:---|
| **Parallel fan-out** | Market, Tax, Behavioral, and Research agents are independent — running them concurrently cuts generation time by ~60% |
| **Annotated State Reducers** | LangGraph `TypedDict` with `Annotated` types + custom reducers prevents concurrent state corruption |
| **Portfolio-first** | All downstream agents need the client profile and holdings — the Portfolio Agent runs first to hydrate state |
| **Brief-last** | The Brief Agent synthesizes all upstream outputs into a single coherent document |

---

## ✨ Features

### 🤖 Multi-Agent Intelligence Pipeline

| Agent | Role | Key Capabilities |
|:------|:-----|:-----------------|
| **Portfolio Agent** | Foundation | Client profile from SQLite, live NSE prices via `yf.download()`, 30-day/YTD returns, NIFTY 50 benchmark comparison, asset allocation drift analysis |
| **Market Agent** | Market Intelligence | Real-time NSE alerts (52-week highs/lows, large drawdowns), sector sentiment via VADER, macro summary with market outlook |
| **Tax Agent** | Tax Optimization | Indian LTCG/STCG scanning, tax-loss harvesting identification (losses > ₹5,000), Section 80C / ELSS recommendations, carry-forward opportunity detection |
| **Behavioral Agent** | Behavioral Finance | 6-dimension Kahneman-Tversky scoring (loss aversion, overconfidence, herding, recency bias, anchoring, status quo bias), risk flags, personalized coaching points |
| **Research Agent** | Macro & Sector | Sector-wise outlook, key economic indicators (GDP, RBI policy, FII flows), Qdrant vector search over past briefs for historical context |
| **Brief Agent** | Synthesis | Executive summary, structured JSON brief, suggested meeting agenda, talking points, draft follow-up email — all generated by Groq Llama 3.3 70B |

### 📊 Frontend Dashboard (React + Vite)

- **Client Sidebar** — Searchable HNI client list with AUM, risk badges, and meeting counts
- **Meeting Cards** — One-click brief generation with real-time polling and loading states
- **Brief Viewer** — Collapsible sections for each intelligence domain:
  - Portfolio Snapshot (holdings table, allocation chart, performance grid)
  - Interactive Pie Chart (asset allocation via Recharts)
  - Behavioral Radar Chart (6-axis Kahneman-Tversky radar)
  - Tax Opportunities (harvest cards with estimated savings)
  - Market Feed (news cards + alerts)
  - Coaching Points + Meeting Agenda
  - Draft Follow-Up Email
- **Glassmorphism UI** — Dark mode with backdrop blur, gradient borders, micro-animations
- **Connection Status** — Real-time backend health indicator (DB + Qdrant)

### 🇮🇳 Indian Market Specific

- All values in **INR (₹)** with Indian number formatting (Lakhs/Crores)
- NIFTY 50 benchmark comparison
- NSE ticker format (`.NS` suffix)
- Indian tax rules: LTCG 10% (>₹1L exemption), STCG 15%, Section 80C ₹1.5L limit
- ELSS fund recommendations (Axis, Mirae, Quant, SBI, DSP)
- Indian HNI client personas with realistic portfolios

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|:------|:-----------|:--------|
| **LLM** | Groq (Llama 3.3 70B Versatile) | Agent reasoning, brief synthesis, coaching points |
| **Orchestration** | LangGraph (StateGraph) | Multi-agent pipeline with parallel execution |
| **Backend** | FastAPI + Uvicorn | REST API with async background tasks |
| **Database** | SQLite + SQLAlchemy 2.0 | Client profiles, holdings, tax lots, meetings, briefs |
| **Vector DB** | Qdrant (Docker) | Semantic search over past briefs via FastEmbed |
| **Market Data** | yfinance 1.3.0 (`yf.download()`) | Live NSE prices, historical data, benchmark returns |
| **News** | NewsAPI.org | Indian financial news with sentiment scoring |
| **Sentiment** | VADER + Financial Lexicon | News article sentiment (extendable to FinBERT) |
| **Frontend** | React 18 + TypeScript + Vite | SPA with component-based architecture |
| **Charts** | Recharts | Portfolio pie, radar, and bar charts |
| **Animations** | Framer Motion | Smooth transitions, spring-based micro-animations |
| **Styling** | Tailwind CSS 4 | Utility-first with custom design tokens |
| **Fonts** | Outfit + JetBrains Mono | Premium typography for financial data |
| **Scheduler** | APScheduler | Automatic brief pre-generation before meetings |

---

## 📁 Project Structure

```
WealthVisor/
├── backend/
│   ├── main.py                    # FastAPI app, endpoints, CORS, lifespan
│   ├── scheduler.py               # APScheduler for auto brief generation
│   ├── requirements.txt           # Python dependencies
│   ├── agents/
│   │   ├── orchestrator.py        # LangGraph StateGraph definition
│   │   ├── portfolio_agent.py     # Agent 1: Portfolio + NSE prices
│   │   ├── market_agent.py        # Agent 2: Market alerts + sentiment
│   │   ├── tax_agent.py           # Agent 3: LTCG/STCG/80C optimizer
│   │   ├── behavioral_agent.py    # Agent 4: Kahneman-Tversky scorer
│   │   ├── research_agent.py      # Agent 5: Macro + sector research
│   │   └── brief_agent.py         # Agent 6: Final brief synthesizer
│   ├── database/
│   │   ├── __init__.py            # SQLAlchemy engine + SessionLocal
│   │   ├── schema.py              # ORM models (Client, Holding, Meeting...)
│   │   ├── crud.py                # Database query functions
│   │   └── seed.py                # Seed 10 Indian HNI clients
│   ├── models/
│   │   └── state.py               # VisorState TypedDict with Annotated reducers
│   └── tools/
│       ├── market_tools.py        # yfinance wrapper + fallback pricing
│       ├── tax_tools.py           # Indian tax computation engine
│       ├── news_tools.py          # NewsAPI + VADER sentiment
│       └── vector_store.py        # Qdrant client + FastEmbed
├── frontend/
│   ├── index.html                 # Entry point with Google Fonts
│   ├── src/
│   │   ├── App.tsx                # Root layout: sidebar + topbar + content
│   │   ├── main.tsx               # React render entry
│   │   ├── index.css              # Design system tokens + glassmorphism
│   │   ├── api/
│   │   │   └── client.ts          # API client + formatINR() + timeUntil()
│   │   └── components/
│   │       ├── Dashboard.tsx       # Stat cards + meeting list
│   │       ├── BriefViewer.tsx     # Full brief renderer (collapsible)
│   │       ├── ClientCard.tsx      # Sidebar client item
│   │       ├── PortfolioChart.tsx  # Recharts pie chart
│   │       ├── BehavioralRadar.tsx # Recharts radar chart
│   │       ├── TaxAlerts.tsx       # Tax harvest + ELSS cards
│   │       └── MarketFeed.tsx      # News + market alerts
├── data/
│   └── wealth_visor.db            # SQLite database (auto-created)
├── docker-compose.yml             # Qdrant vector database
├── .env                           # Environment variables
└── .env.example                   # Template for environment setup
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+** (Anaconda recommended)
- **Node.js 18+** and npm
- **Docker** (for Qdrant vector database)
- **Groq API Key** (free at [console.groq.com](https://console.groq.com))

### 1. Clone & Setup Environment

```bash
git clone https://github.com/yourusername/WealthVisor.git
cd WealthVisor

# Copy environment template
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 2. Start Qdrant (Vector Database)

```bash
docker compose up -d
```

This starts Qdrant on `localhost:6333` for semantic search over past briefs.

### 3. Install Backend Dependencies

```bash
pip install -r backend/requirements.txt

# Download NLTK data for sentiment analysis
python -c "import nltk; nltk.download('vader_lexicon')"
```

### 4. Seed the Database

```bash
python -m backend.database.seed
```

This creates `data/wealth_visor.db` with **10 Indian HNI client profiles**, each with:
- Diversified NSE equity holdings (RELIANCE, HDFCBANK, TCS, INFY, etc.)
- Realistic tax lots with varied purchase dates
- Client interactions history
- 5 upcoming meetings

### 5. Start the Backend

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.   
Swagger docs at `http://localhost:8000/docs`.

### 6. Install & Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

---

## 📡 API Reference

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET` | `/health` | Health check (DB + Qdrant status) |
| `GET` | `/clients` | List all clients with meeting counts |
| `GET` | `/clients/{id}` | Full client profile with holdings |
| `GET` | `/meetings` | List meetings (`?upcoming_only=true`) |
| `GET` | `/meetings/{id}` | Meeting details with brief content |
| `POST` | `/meetings/{id}/generate-brief` | 🚀 **Trigger the multi-agent pipeline** |
| `GET` | `/meetings/{id}/brief` | Retrieve generated brief JSON |
| `GET` | `/portfolio/{id}/snapshot` | Quick portfolio overview |
| `GET` | `/portfolio/{id}/tax-opportunities` | Standalone tax analysis |
| `GET` | `/stats` | Dashboard aggregate metrics |

### Brief Generation Flow

```
POST /meetings/1/generate-brief
  → Returns: { "status": "generating", "meeting_id": 1 }
  → Backend runs LangGraph pipeline in background (~30-60s)

GET /meetings/1/brief
  → Returns: { "meeting_id": 1, "brief_content": { ... }, "brief_generated_at": "..." }
```

---

## 🧠 Intelligence Brief Structure

Each generated brief contains the following sections:

```json
{
  "metadata": {
    "client_name": "Rajesh Sharma",
    "meeting_type": "portfolio_review",
    "meeting_at": "2026-04-26T10:00:00",
    "advisor_aum_this_client": 45000000,
    "generated_at": "2026-04-25T18:00:00"
  },
  "executive_summary": "Concise paragraph covering portfolio health, risks, and key actions...",
  "portfolio": {
    "total_value": 45000000,
    "performance": { "return_30d": 2.3, "vs_nifty_30d": 0.8, "ytd_return": 12.5 },
    "top_holdings": [ ... ],
    "asset_allocation": { "Large Cap": 45, "IT": 25, "Banking": 20, "Pharma": 10 }
  },
  "market_intelligence": {
    "alerts": [ { "ticker": "TCS.NS", "type": "52_week_high", "message": "..." } ],
    "relevant_news": [ { "title": "...", "sentiment": "positive", "score": 0.85 } ],
    "macro_summary": "RBI holds rates steady..."
  },
  "tax_opportunities": {
    "harvest_opportunities": [ { "ticker": "HDFCBANK.NS", "loss_amount": 225423, "estimated_tax_saving": 22542 } ],
    "elss_recommendation": { "recommended_amount": 150000, "suggested_fund": "SBI Long Term Equity Fund", "estimated_tax_saving": 45000 },
    "total_potential_tax_saving": 67639,
    "tax_summary": "..."
  },
  "behavioral_intelligence": {
    "risk_profile": { "loss_aversion": 7, "overconfidence": 5, "herding": 6, ... },
    "flags": [ "High loss aversion detected — client may resist booking losses" ],
    "coaching_points": [ "If the client mentions the NIFTY drop, redirect to..." ]
  },
  "macro_research": {
    "sector_outlook": { "IT": "Cautiously optimistic...", "Banking": "Strong momentum..." },
    "key_indicators": [ { "title": "RBI Policy Rate", "summary": "..." } ]
  },
  "suggested_agenda": [ "Review portfolio performance vs NIFTY 50", "Discuss tax harvesting opportunity in HDFCBANK", ... ],
  "talking_points": [ "Portfolio has outperformed NIFTY by 80bps this month", ... ],
  "draft_follow_up_email": "Dear Rajesh,\n\nThank you for our meeting today...",
  "generation_time_sec": 42.3
}
```

---

## 🎨 Design System

WealthVisor follows the [DESIGN.md](https://github.com/google-labs-code/design.md) specification principles:

| Token | Value | Purpose |
|:------|:------|:--------|
| **Primary** | `#5E6AD2` | Brand accent, interactive elements |
| **Accent** | `#00E5FF` | Highlights, time indicators |
| **Surface** | `#0A0A0B` | Deep black background |
| **Surface-2** | `#141416` | Card backgrounds |
| **Success** | `#1AE296` | Positive returns, savings |
| **Danger** | `#FC5B65` | Losses, alerts |
| **Font (UI)** | Outfit | Modern, clean readability |
| **Font (Data)** | JetBrains Mono | Tickers, numbers, monospace data |

### Visual Features

- **Glassmorphism cards** with `backdrop-filter: blur(24px)` and translucent borders
- **Radial gradient backgrounds** for depth perception
- **Spring-based animations** via Framer Motion
- **Indian number formatting** (₹45.0L, ₹4.5Cr)
- **WCAG AA compliant** contrast ratios on all text

---

## ⚙️ Environment Variables

| Variable | Required | Default | Description |
|:---------|:---------|:--------|:------------|
| `GROQ_API_KEY` | ✅ Yes | — | Groq API key for Llama 3.3 70B |
| `NEWS_API_KEY` | ❌ No | — | NewsAPI.org key (100 free requests/day) |
| `QDRANT_URL` | ❌ No | `http://localhost:6333` | Qdrant vector DB URL |
| `DB_PATH` | ❌ No | `./data/wealth_visor.db` | SQLite database path |
| `USE_FINBERT` | ❌ No | `false` | Use FinBERT instead of VADER for sentiment |

---

## 🔧 Key Technical Decisions

### LangGraph State Management

The `VisorState` uses `Annotated` types with custom reducer functions to enable safe parallel execution:

```python
class VisorState(TypedDict):
    meeting_id: Annotated[int, _last_value]           # Scalar — last writer wins
    errors: Annotated[list, operator.add]              # List — append across agents
    portfolio_summary: Annotated[dict, _merge_dict]    # Dict — deep merge
    behavioral_flags: Annotated[list, operator.add]    # List — concat from agents
```

Each agent returns **only the state keys it owns**, preventing `INVALID_CONCURRENT_GRAPH_UPDATE` errors.

### yfinance Robustness

NSE tickers are fetched using `yf.download()` (batch API) instead of `Ticker.history()` (unreliable for `.NS` tickers). A comprehensive fallback pricing system uses realistic hardcoded prices for 20+ major NSE stocks to prevent pipeline failure during rate limits.

### Indian Tax Engine

The tax computation engine implements FY 2024-25 rules:
- LTCG: 10% on gains above ₹1,00,000 exemption
- STCG: 15% flat rate
- Loss harvesting: Identifies positions with unrealized losses > ₹5,000
- Section 80C: ELSS recommendations based on age, risk profile, and existing investments
- No wash-sale rule (unlike US markets)

---

## 📈 Performance

| Metric | Value |
|:-------|:------|
| Full pipeline execution | 30-60 seconds |
| Parallel agent speedup | ~60% vs sequential |
| Database seed | 10 clients, 50+ holdings, 5 meetings |
| API response (cached) | < 100ms |
| Frontend bundle size | ~180KB gzipped |

---

## 🗺️ Roadmap

- [ ] **Real-time WebSocket updates** during brief generation
- [ ] **FinBERT integration** for advanced sentiment analysis
- [ ] **Multi-language briefs** (Hindi, Tamil, Marathi)
- [ ] **PDF export** with professional formatting
- [ ] **Voice briefing** via Text-to-Speech
- [ ] **Client portal** for self-service portfolio view
- [ ] **Mutual fund analysis** (SIP tracking, NAV history)
- [ ] **Regulatory compliance** checks (SEBI guidelines)
- [ ] **Meeting recording integration** with transcript analysis
- [ ] **Customizable brief templates** per advisor preference

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
