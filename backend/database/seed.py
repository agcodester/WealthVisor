"""
WealthVisor — Seed Data
Creates 10 synthetic Indian HNI clients with realistic NSE portfolios.
Run once at startup if DB is empty.
"""

import os
import sys
import random
from datetime import datetime, date, timedelta

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.database import engine, SessionLocal, Base
from backend.database.schema import Client, Holding, TaxLot, Meeting, Interaction

# ─── Ticker Pools ───────────────────────────────────────────────────────────
EQUITY_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS", "LT.NS", "AXISBANK.NS",
    "SBIN.NS", "WIPRO.NS", "HCLTECH.NS", "MARUTI.NS", "TATAMOTORS.NS",
]
ETF_TICKERS = [
    "NIFTYBEES.NS", "BANKBEES.NS", "GOLDBEES.NS", "JUNIORBEES.NS",
]
BOND_FUND_TICKERS = ["LIQUIDBEES.NS"]

ALL_TICKERS = EQUITY_TICKERS + ETF_TICKERS + BOND_FUND_TICKERS

# ─── Client Templates ──────────────────────────────────────────────────────
CLIENT_DATA = [
    {
        "name": "Rajesh Sharma",
        "email": "rajesh.sharma@example.com",
        "phone": "+91-98100-12345",
        "age": 52,
        "occupation": "Managing Director, Tata Steel",
        "risk_tolerance": "moderate",
        "investment_goal": "retirement",
        "tax_bracket": 0.30,
        "annual_income": 8500000,
        "aum": 45000000,
        "advisor_notes": "Rajesh is a seasoned investor, prefers blue-chip stocks and index ETFs. Concerned about succession planning. Wants to create a retirement corpus by age 60.",
        "behavioral_score": {"loss_aversion": 6, "overconfidence": 3, "herding": 4, "recency_bias": 5, "anchoring": 4, "status_quo": 7},
    },
    {
        "name": "Priya Menon",
        "email": "priya.menon@example.com",
        "phone": "+91-98200-23456",
        "age": 38,
        "occupation": "VP Engineering, Flipkart",
        "risk_tolerance": "aggressive",
        "investment_goal": "wealth_growth",
        "tax_bracket": 0.30,
        "annual_income": 12000000,
        "aum": 25000000,
        "advisor_notes": "Priya has high risk appetite, loves tech stocks. Recently received large ESOP payout. Interested in sectoral bets and mid-cap exposure.",
        "behavioral_score": {"loss_aversion": 3, "overconfidence": 8, "herding": 5, "recency_bias": 6, "anchoring": 3, "status_quo": 2},
    },
    {
        "name": "Arun Krishnamurthy",
        "email": "arun.k@example.com",
        "phone": "+91-98300-34567",
        "age": 65,
        "occupation": "Retired IAS Officer",
        "risk_tolerance": "conservative",
        "investment_goal": "income",
        "tax_bracket": 0.20,
        "annual_income": 3500000,
        "aum": 35000000,
        "advisor_notes": "Arun prioritizes capital preservation and regular income. Large allocation to fixed income and gold. Anxious about market volatility since retirement.",
        "behavioral_score": {"loss_aversion": 9, "overconfidence": 2, "herding": 6, "recency_bias": 7, "anchoring": 8, "status_quo": 9},
    },
    {
        "name": "Sneha Patel",
        "email": "sneha.patel@example.com",
        "phone": "+91-98400-45678",
        "age": 42,
        "occupation": "Co-founder, HealthTech Startup",
        "risk_tolerance": "aggressive",
        "investment_goal": "wealth_growth",
        "tax_bracket": 0.30,
        "annual_income": 15000000,
        "aum": 50000000,
        "advisor_notes": "Sneha sold her previous startup for ₹20 Cr. Aggressive investor with sectoral concentration in pharma and IT. Wants to diversify but resists moving out of familiar sectors.",
        "behavioral_score": {"loss_aversion": 4, "overconfidence": 7, "herding": 3, "recency_bias": 4, "anchoring": 5, "status_quo": 6},
    },
    {
        "name": "Vikram Singh",
        "email": "vikram.singh@example.com",
        "phone": "+91-98500-56789",
        "age": 55,
        "occupation": "Senior Partner, Deloitte India",
        "risk_tolerance": "moderate",
        "investment_goal": "retirement",
        "tax_bracket": 0.30,
        "annual_income": 9500000,
        "aum": 40000000,
        "advisor_notes": "Vikram wants a balanced portfolio. Currently worried about interest rate changes by RBI. Prefers a mix of equity and debt. Plans to retire at 58.",
        "behavioral_score": {"loss_aversion": 5, "overconfidence": 4, "herding": 5, "recency_bias": 3, "anchoring": 6, "status_quo": 5},
    },
    {
        "name": "Ananya Reddy",
        "email": "ananya.reddy@example.com",
        "phone": "+91-98600-67890",
        "age": 35,
        "occupation": "Product Lead, Google India",
        "risk_tolerance": "aggressive",
        "investment_goal": "wealth_growth",
        "tax_bracket": 0.30,
        "annual_income": 18000000,
        "aum": 20000000,
        "advisor_notes": "Ananya is a young high earner. Wants maximum growth, comfortable with volatility. Interested in momentum strategies and small-cap exposure.",
        "behavioral_score": {"loss_aversion": 2, "overconfidence": 9, "herding": 7, "recency_bias": 8, "anchoring": 2, "status_quo": 1},
    },
    {
        "name": "Deepak Gupta",
        "email": "deepak.gupta@example.com",
        "phone": "+91-98700-78901",
        "age": 48,
        "occupation": "Owner, Gupta Textiles Pvt Ltd",
        "risk_tolerance": "moderate",
        "investment_goal": "income",
        "tax_bracket": 0.30,
        "annual_income": 7000000,
        "aum": 30000000,
        "advisor_notes": "Deepak is a business owner who wants his portfolio to generate regular dividend income. Heavy allocation to PSU stocks and high-dividend yielders. Resistant to change.",
        "behavioral_score": {"loss_aversion": 7, "overconfidence": 5, "herding": 6, "recency_bias": 4, "anchoring": 7, "status_quo": 8},
    },
    {
        "name": "Kavitha Nair",
        "email": "kavitha.nair@example.com",
        "phone": "+91-98800-89012",
        "age": 60,
        "occupation": "Retired Professor, IIM Bangalore",
        "risk_tolerance": "conservative",
        "investment_goal": "retirement",
        "tax_bracket": 0.20,
        "annual_income": 2800000,
        "aum": 18000000,
        "advisor_notes": "Kavitha is highly analytical and research-oriented. Prefers evidence-based approach. Defensive posture since COVID crash. Needs reassurance about fixed income allocation.",
        "behavioral_score": {"loss_aversion": 8, "overconfidence": 3, "herding": 2, "recency_bias": 6, "anchoring": 7, "status_quo": 8},
    },
    {
        "name": "Rohit Malhotra",
        "email": "rohit.malhotra@example.com",
        "phone": "+91-98900-90123",
        "age": 40,
        "occupation": "CTO, Razorpay",
        "risk_tolerance": "aggressive",
        "investment_goal": "wealth_growth",
        "tax_bracket": 0.30,
        "annual_income": 22000000,
        "aum": 55000000,
        "advisor_notes": "Rohit is tech-savvy, tracks markets daily, trades frequently. Has large concentrated position in tech stocks. Needs to be guided on diversification and overtrading risks.",
        "behavioral_score": {"loss_aversion": 3, "overconfidence": 9, "herding": 4, "recency_bias": 9, "anchoring": 3, "status_quo": 2},
    },
    {
        "name": "Meera Iyer",
        "email": "meera.iyer@example.com",
        "phone": "+91-99000-01234",
        "age": 58,
        "occupation": "CFO, Mahindra Group",
        "risk_tolerance": "moderate",
        "investment_goal": "retirement",
        "tax_bracket": 0.30,
        "annual_income": 13000000,
        "aum": 48000000,
        "advisor_notes": "Meera is financially sophisticated. Approaching retirement in 2 years. Wants to gradually shift from equity to fixed income. Has significant unrealized gains to manage tax-efficiently.",
        "behavioral_score": {"loss_aversion": 5, "overconfidence": 4, "herding": 3, "recency_bias": 4, "anchoring": 5, "status_quo": 6},
    },
]

# ─── Approximate prices for seeding (will be overridden by live data) ──────
APPROX_PRICES = {
    "RELIANCE.NS": 2500, "TCS.NS": 3800, "INFY.NS": 1500, "HDFCBANK.NS": 1600,
    "ICICIBANK.NS": 1100, "BHARTIARTL.NS": 1600, "ITC.NS": 450,
    "KOTAKBANK.NS": 1800, "LT.NS": 3500, "AXISBANK.NS": 1100,
    "SBIN.NS": 800, "WIPRO.NS": 450, "HCLTECH.NS": 1600,
    "MARUTI.NS": 12000, "TATAMOTORS.NS": 950,
    "NIFTYBEES.NS": 250, "BANKBEES.NS": 480, "GOLDBEES.NS": 55,
    "JUNIORBEES.NS": 700, "LIQUIDBEES.NS": 1000,
}

MEETING_TYPES = ["quarterly_review", "onboarding", "adhoc", "annual_review", "tax_planning"]
INTERACTION_TYPES = ["meeting", "email", "call", "note"]
SENTIMENTS = ["positive", "neutral", "negative", "anxious"]

INTERACTION_SUMMARIES = [
    ("Client expressed concern about NIFTY volatility", "anxious"),
    ("Discussed tax-loss harvesting strategy for equities", "neutral"),
    ("Client happy with recent returns, wants to increase equity exposure", "positive"),
    ("Reviewed fixed income allocation, client comfortable with current mix", "positive"),
    ("Client worried about RBI rate hike impact on bond portfolio", "negative"),
    ("Discussed ELSS investment for Section 80C benefits", "positive"),
    ("Client requested shift from mid-cap to large-cap after recent dip", "anxious"),
    ("Quarterly performance review — portfolio outperformed NIFTY by 2%", "positive"),
    ("Client mentioned wanting to invest in gold as hedge", "neutral"),
    ("Discussed rebalancing — client resistant to selling winners", "negative"),
    ("Client asked about international diversification via LRS", "neutral"),
    ("Worried about tech sector concentration in portfolio", "anxious"),
    ("Happy with dividend income from ITC and Infosys", "positive"),
    ("Explored NPS Tier 1 contribution for additional tax savings", "neutral"),
    ("Client panicked after 5% single-day NIFTY drop, urged calm", "negative"),
]


def _random_purchase_date(months_back_min=3, months_back_max=36):
    days = random.randint(months_back_min * 30, months_back_max * 30)
    return date.today() - timedelta(days=days)


def _build_holdings_for_client(client_idx: int):
    """Generate 5–8 diversified holdings for a client."""
    random.seed(42 + client_idx)
    num_equities = random.randint(3, 5)
    num_etfs = random.randint(1, 3)

    selected_equities = random.sample(EQUITY_TICKERS, num_equities)
    selected_etfs = random.sample(ETF_TICKERS, num_etfs)
    tickers = selected_equities + selected_etfs

    holdings = []
    weights = []
    for i, ticker in enumerate(tickers):
        w = random.uniform(0.08, 0.25)
        weights.append(w)
    # Normalize weights
    total_w = sum(weights)
    weights = [w / total_w for w in weights]

    for ticker, weight in zip(tickers, weights):
        price = APPROX_PRICES.get(ticker, 1000)
        # Random purchase price within ±30% of current
        purch_price = price * random.uniform(0.70, 1.10)
        asset_class = "equity"
        if ticker in ETF_TICKERS:
            asset_class = "etf"
        if ticker in BOND_FUND_TICKERS:
            asset_class = "bond_fund"
        if "GOLD" in ticker:
            asset_class = "gold"

        holdings.append({
            "ticker": ticker,
            "asset_class": asset_class,
            "quantity": round(random.uniform(20, 500), 0),
            "purchase_price": round(purch_price, 2),
            "purchase_date": _random_purchase_date(),
            "target_weight": round(weight, 4),
        })
    return holdings


def _build_tax_lots(client_idx: int, holdings: list):
    """Generate 3–5 tax lots per holding (multiple purchase events)."""
    random.seed(100 + client_idx)
    lots = []
    for h in holdings:
        num_lots = random.randint(2, 4)
        remaining_qty = h["quantity"]
        for i in range(num_lots):
            if i == num_lots - 1:
                lot_qty = remaining_qty
            else:
                lot_qty = round(remaining_qty * random.uniform(0.2, 0.5), 0)
                remaining_qty -= lot_qty

            purch = _random_purchase_date(1, 30)
            days_held = (date.today() - purch).days
            lot_type = "long_term" if days_held > 365 else "short_term"

            price_var = h["purchase_price"] * random.uniform(0.85, 1.15)
            lots.append({
                "ticker": h["ticker"],
                "quantity": max(lot_qty, 1),
                "cost_basis": round(price_var, 2),
                "purchase_date": purch,
                "lot_type": lot_type,
            })
    return lots


def _build_interactions(client_idx: int):
    """Generate 3–5 past interactions."""
    random.seed(200 + client_idx)
    num = random.randint(3, 5)
    interactions = []
    for i in range(num):
        summary, sentiment = random.choice(INTERACTION_SUMMARIES)
        days_ago = random.randint(5, 90)
        interactions.append({
            "interaction_date": date.today() - timedelta(days=days_ago),
            "type": random.choice(INTERACTION_TYPES),
            "summary": summary,
            "sentiment": sentiment,
        })
    return interactions


def seed_database():
    """Create all tables and seed 10 clients + 3 upcoming meetings."""
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Ensure data directory exists
    db_path = os.getenv("DB_PATH", "./data/wealth_visor.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    session = SessionLocal()

    # Check if already seeded
    existing = session.query(Client).count()
    if existing > 0:
        print(f"Database already has {existing} clients. Skipping seed.")
        session.close()
        return

    print("Seeding WealthVisor database with 10 Indian HNI clients...")

    now = datetime.now()
    clients_with_meetings = []

    for idx, cd in enumerate(CLIENT_DATA):
        client = Client(
            name=cd["name"],
            email=cd["email"],
            phone=cd["phone"],
            age=cd["age"],
            occupation=cd["occupation"],
            risk_tolerance=cd["risk_tolerance"],
            investment_goal=cd["investment_goal"],
            tax_bracket=cd["tax_bracket"],
            annual_income=cd["annual_income"],
            aum=cd["aum"],
            advisor_notes=cd["advisor_notes"],
            behavioral_score=cd["behavioral_score"],
        )
        session.add(client)
        session.flush()  # Get the client ID

        # Add holdings
        holdings_data = _build_holdings_for_client(idx)
        for hd in holdings_data:
            holding = Holding(client_id=client.id, **hd)
            session.add(holding)

        # Add tax lots
        lots_data = _build_tax_lots(idx, holdings_data)
        for ld in lots_data:
            lot = TaxLot(client_id=client.id, **ld)
            session.add(lot)

        # Add interactions
        interactions_data = _build_interactions(idx)
        for intd in interactions_data:
            interaction = Interaction(client_id=client.id, **intd)
            session.add(interaction)

        clients_with_meetings.append(client)
        print(f"  ✓ Created client: {cd['name']} (AUM: ₹{cd['aum']:,.0f})")

    # ─── Create 3 upcoming meetings ─────────────────────────────────────
    # Meeting 1: 25 minutes from now (triggers immediately)
    m1 = Meeting(
        client_id=clients_with_meetings[0].id,
        scheduled_at=now + timedelta(minutes=25),
        duration_min=60,
        meeting_type="quarterly_review",
        agenda_notes="Quarterly portfolio review. Discuss NIFTY performance and rebalancing strategy.",
    )
    # Meeting 2: 2 hours from now
    m2 = Meeting(
        client_id=clients_with_meetings[1].id,
        scheduled_at=now + timedelta(hours=2),
        duration_min=45,
        meeting_type="adhoc",
        agenda_notes="Client wants to discuss recent tech sector earnings and the impact on portfolio. Also explore tax-saving strategies before March deadline.",
    )
    # Meeting 3: tomorrow 10 AM IST
    tomorrow_10am = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0)
    m3 = Meeting(
        client_id=clients_with_meetings[4].id,
        scheduled_at=tomorrow_10am,
        duration_min=60,
        meeting_type="tax_planning",
        agenda_notes="Annual tax planning review. Need to evaluate LTCG implications and ELSS fresh investments for 80C.",
    )

    # Additional meetings for demo richness
    m4 = Meeting(
        client_id=clients_with_meetings[2].id,
        scheduled_at=now + timedelta(hours=4),
        duration_min=30,
        meeting_type="adhoc",
        agenda_notes="Client called in worried about market correction. Needs reassurance about conservative portfolio.",
    )
    m5 = Meeting(
        client_id=clients_with_meetings[9].id,
        scheduled_at=tomorrow_10am + timedelta(hours=2),
        duration_min=60,
        meeting_type="annual_review",
        agenda_notes="Pre-retirement portfolio transition discussion. Shift equity to fixed income.",
    )

    session.add_all([m1, m2, m3, m4, m5])

    session.commit()
    session.close()

    print(f"\n✅ Seeded database successfully:")
    print(f"   • 10 clients")
    print(f"   • 5 upcoming meetings")
    print(f"   • Database: {db_path}")


if __name__ == "__main__":
    seed_database()
