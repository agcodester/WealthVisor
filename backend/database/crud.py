"""
WealthVisor — CRUD Operations
All read/write functions for the database. NO raw SQL — all SQLAlchemy ORM.
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from backend.database.schema import Client, Holding, TaxLot, Meeting, Interaction, MarketCache


# ═══════════════════════════════════════════════════════════════════════════
# CLIENT operations
# ═══════════════════════════════════════════════════════════════════════════

def get_all_clients(db: Session) -> list[dict]:
    """Returns all clients with upcoming meeting count."""
    clients = db.query(Client).all()
    now = datetime.utcnow()
    result = []
    for c in clients:
        upcoming = db.query(Meeting).filter(
            Meeting.client_id == c.id,
            Meeting.scheduled_at > now
        ).count()
        result.append({
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "age": c.age,
            "occupation": c.occupation,
            "risk_tolerance": c.risk_tolerance,
            "investment_goal": c.investment_goal,
            "aum": c.aum,
            "annual_income": c.annual_income,
            "tax_bracket": c.tax_bracket,
            "upcoming_meeting_count": upcoming,
        })
    return result


def get_client_with_holdings(db: Session, client_id: int) -> dict | None:
    """Returns full client profile with holdings, tax_lots, interactions, meetings."""
    client = db.query(Client).options(
        joinedload(Client.holdings),
        joinedload(Client.tax_lots),
        joinedload(Client.interactions),
        joinedload(Client.meetings),
    ).filter(Client.id == client_id).first()

    if not client:
        return None

    return {
        "id": client.id,
        "name": client.name,
        "email": client.email,
        "phone": client.phone,
        "age": client.age,
        "occupation": client.occupation,
        "risk_tolerance": client.risk_tolerance,
        "investment_goal": client.investment_goal,
        "tax_bracket": client.tax_bracket,
        "annual_income": client.annual_income,
        "aum": client.aum,
        "advisor_notes": client.advisor_notes,
        "behavioral_score": client.behavioral_score,
        "holdings": [
            {
                "id": h.id,
                "ticker": h.ticker,
                "asset_class": h.asset_class,
                "quantity": h.quantity,
                "purchase_price": h.purchase_price,
                "purchase_date": h.purchase_date.isoformat() if h.purchase_date else None,
                "target_weight": h.target_weight,
            }
            for h in client.holdings
        ],
        "tax_lots": [
            {
                "id": tl.id,
                "ticker": tl.ticker,
                "quantity": tl.quantity,
                "cost_basis": tl.cost_basis,
                "purchase_date": tl.purchase_date.isoformat() if tl.purchase_date else None,
                "lot_type": tl.lot_type,
            }
            for tl in client.tax_lots
        ],
        "interactions": [
            {
                "id": it.id,
                "interaction_date": it.interaction_date.isoformat() if it.interaction_date else None,
                "type": it.type,
                "summary": it.summary,
                "sentiment": it.sentiment,
            }
            for it in client.interactions
        ],
        "meetings": [
            {
                "id": m.id,
                "scheduled_at": m.scheduled_at.isoformat() if m.scheduled_at else None,
                "duration_min": m.duration_min,
                "meeting_type": m.meeting_type,
                "agenda_notes": m.agenda_notes,
                "brief_generated": m.brief_generated,
            }
            for m in client.meetings
        ],
    }


# ═══════════════════════════════════════════════════════════════════════════
# MEETING operations
# ═══════════════════════════════════════════════════════════════════════════

def get_all_meetings(db: Session, upcoming_only: bool = True) -> list[dict]:
    """Returns meetings, optionally filtered to upcoming only."""
    query = db.query(Meeting).options(joinedload(Meeting.client))
    if upcoming_only:
        query = query.filter(Meeting.scheduled_at > datetime.now())
    meetings = query.order_by(Meeting.scheduled_at).all()
    return [
        {
            "id": m.id,
            "client_id": m.client_id,
            "client_name": m.client.name if m.client else "Unknown",
            "client_aum": m.client.aum if m.client else 0,
            "client_risk": m.client.risk_tolerance if m.client else "",
            "scheduled_at": m.scheduled_at.isoformat() if m.scheduled_at else None,
            "duration_min": m.duration_min,
            "meeting_type": m.meeting_type,
            "agenda_notes": m.agenda_notes,
            "brief_generated": m.brief_generated,
            "brief_generated_at": m.brief_generated_at.isoformat() if m.brief_generated_at else None,
        }
        for m in meetings
    ]


def get_meeting(db: Session, meeting_id: int) -> dict | None:
    """Returns full meeting detail including brief_content if generated."""
    m = db.query(Meeting).options(joinedload(Meeting.client)).filter(Meeting.id == meeting_id).first()
    if not m:
        return None
    return {
        "id": m.id,
        "client_id": m.client_id,
        "client_name": m.client.name if m.client else "Unknown",
        "client_aum": m.client.aum if m.client else 0,
        "scheduled_at": m.scheduled_at.isoformat() if m.scheduled_at else None,
        "duration_min": m.duration_min,
        "meeting_type": m.meeting_type,
        "agenda_notes": m.agenda_notes,
        "brief_generated": m.brief_generated,
        "brief_content": m.brief_content,
        "brief_generated_at": m.brief_generated_at.isoformat() if m.brief_generated_at else None,
    }


def get_meetings_needing_briefs(db: Session) -> list[Meeting]:
    """Finds meetings 20–40 min from now that don't have briefs yet."""
    now = datetime.now()
    window_start = now + timedelta(minutes=20)
    window_end = now + timedelta(minutes=40)
    return db.query(Meeting).filter(
        Meeting.scheduled_at >= window_start,
        Meeting.scheduled_at <= window_end,
        Meeting.brief_generated == False,
    ).all()


def save_brief(db: Session, meeting_id: int, brief_content: dict):
    """Saves generated brief to the meetings table."""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if meeting:
        meeting.brief_content = brief_content
        meeting.brief_generated = True
        meeting.brief_generated_at = datetime.utcnow()
        db.commit()


# ═══════════════════════════════════════════════════════════════════════════
# MARKET CACHE operations
# ═══════════════════════════════════════════════════════════════════════════

def get_cached_price(db: Session, ticker: str) -> MarketCache | None:
    """Returns cached market data if fetched within the last 15 minutes."""
    cutoff = datetime.utcnow() - timedelta(minutes=15)
    return db.query(MarketCache).filter(
        MarketCache.ticker == ticker,
        MarketCache.fetched_at >= cutoff,
    ).first()


def upsert_market_cache(db: Session, ticker: str, data: dict):
    """Inserts or updates market cache for a ticker."""
    existing = db.query(MarketCache).filter(MarketCache.ticker == ticker).first()
    if existing:
        existing.fetched_at = datetime.utcnow()
        for k, v in data.items():
            if hasattr(existing, k):
                setattr(existing, k, v)
    else:
        cache = MarketCache(
            ticker=ticker,
            fetched_at=datetime.utcnow(),
            **data
        )
        db.add(cache)
    db.commit()


# ═══════════════════════════════════════════════════════════════════════════
# PORTFOLIO operations
# ═══════════════════════════════════════════════════════════════════════════

def get_client_tax_lots(db: Session, client_id: int) -> list[dict]:
    """Returns all tax lots for a client."""
    lots = db.query(TaxLot).filter(TaxLot.client_id == client_id).all()
    return [
        {
            "id": tl.id,
            "ticker": tl.ticker,
            "quantity": tl.quantity,
            "cost_basis": tl.cost_basis,
            "purchase_date": tl.purchase_date.isoformat() if tl.purchase_date else None,
            "lot_type": tl.lot_type,
        }
        for tl in lots
    ]


def get_client_interactions(db: Session, client_id: int, days: int = 60) -> list[dict]:
    """Returns recent interactions within the given number of days."""
    cutoff = datetime.now().date() - timedelta(days=days)
    interactions = db.query(Interaction).filter(
        Interaction.client_id == client_id,
        Interaction.interaction_date >= cutoff,
    ).order_by(Interaction.interaction_date.desc()).all()
    return [
        {
            "id": it.id,
            "interaction_date": it.interaction_date.isoformat(),
            "type": it.type,
            "summary": it.summary,
            "sentiment": it.sentiment,
        }
        for it in interactions
    ]


# ═══════════════════════════════════════════════════════════════════════════
# STATS / METRICS
# ═══════════════════════════════════════════════════════════════════════════

def get_dashboard_stats(db: Session) -> dict:
    """Computes dashboard-level metrics."""
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    briefs_today = db.query(Meeting).filter(
        Meeting.brief_generated == True,
        Meeting.brief_generated_at >= today_start,
    ).count()

    # Avg generation time from brief_content
    all_briefs = db.query(Meeting).filter(Meeting.brief_generated == True).all()
    gen_times = []
    total_tax_savings = 0.0
    for m in all_briefs:
        if m.brief_content:
            gt = m.brief_content.get("generation_time_sec")
            if gt:
                gen_times.append(gt)
            tax_opps = m.brief_content.get("tax_opportunities", {})
            total_tax_savings += tax_opps.get("total_potential_tax_saving", 0)

    avg_gen_time = sum(gen_times) / len(gen_times) if gen_times else 0

    # Clients with high behavioral risk (any score > 7)
    high_risk_count = 0
    clients = db.query(Client).all()
    for c in clients:
        if c.behavioral_score:
            if any(v > 7 for v in c.behavioral_score.values()):
                high_risk_count += 1

    active_meetings_today = db.query(Meeting).filter(
        Meeting.scheduled_at >= today_start,
        Meeting.scheduled_at < today_start + timedelta(days=1),
    ).count()

    return {
        "briefs_generated_today": briefs_today,
        "avg_generation_time": round(avg_gen_time, 1),
        "total_tax_savings_identified": total_tax_savings,
        "clients_high_behavioral_risk": high_risk_count,
        "active_meetings_today": active_meetings_today,
    }
