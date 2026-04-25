"""
WealthVisor — Database Schema
6 SQLAlchemy ORM models for Indian wealth management context.
All monetary values in INR (₹). All tickers are NSE (.NS suffix).
"""

from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, Date, DateTime, JSON,
    ForeignKey
)
from sqlalchemy.orm import relationship
from backend.database import Base


class Client(Base):
    """Indian HNI client profile."""
    __tablename__ = "clients"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    name            = Column(String, nullable=False)
    email           = Column(String, unique=True, nullable=False)
    phone           = Column(String)
    age             = Column(Integer)
    occupation      = Column(String)           # "VP Engineering, Infosys"
    risk_tolerance  = Column(String)           # "moderate", "aggressive", "conservative"
    investment_goal = Column(String)           # "retirement", "wealth_growth", "income"
    tax_bracket     = Column(Float)            # 0.30 (30% slab)
    annual_income   = Column(Float)            # 4500000.0 (₹45 lakh)
    aum             = Column(Float)            # 25000000.0 (₹2.5 crore)
    advisor_notes   = Column(Text)
    behavioral_score = Column(JSON)            # {"loss_aversion": 7, "overconfidence": 4, ...}
    created_at      = Column(DateTime, default=datetime.utcnow)

    # Relationships
    holdings        = relationship("Holding", back_populates="client", cascade="all, delete-orphan")
    meetings        = relationship("Meeting", back_populates="client", cascade="all, delete-orphan")
    tax_lots        = relationship("TaxLot", back_populates="client", cascade="all, delete-orphan")
    interactions    = relationship("Interaction", back_populates="client", cascade="all, delete-orphan")


class Holding(Base):
    """One row per ticker per client — current portfolio position."""
    __tablename__ = "holdings"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    client_id       = Column(Integer, ForeignKey("clients.id"), nullable=False)
    ticker          = Column(String, nullable=False)           # "RELIANCE.NS"
    asset_class     = Column(String, nullable=False)           # "equity", "etf", "bond_fund", "gold", "cash"
    quantity        = Column(Float, nullable=False)            # 150.0 shares
    purchase_price  = Column(Float, nullable=False)            # ₹2450.50 cost basis per share
    purchase_date   = Column(Date, nullable=False)
    target_weight   = Column(Float)                            # 0.15 (15% of portfolio)

    client          = relationship("Client", back_populates="holdings")


class TaxLot(Base):
    """One row per purchase event (tax lot). Same ticker may have multiple lots."""
    __tablename__ = "tax_lots"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    client_id       = Column(Integer, ForeignKey("clients.id"), nullable=False)
    ticker          = Column(String, nullable=False)
    quantity        = Column(Float, nullable=False)
    cost_basis      = Column(Float, nullable=False)            # per share in ₹
    purchase_date   = Column(Date, nullable=False)
    lot_type        = Column(String, nullable=False)           # "long_term" (>12mo) or "short_term" (<=12mo)

    client          = relationship("Client", back_populates="tax_lots")


class Meeting(Base):
    """Scheduled advisor-client meetings."""
    __tablename__ = "meetings"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    client_id           = Column(Integer, ForeignKey("clients.id"), nullable=False)
    scheduled_at        = Column(DateTime, nullable=False)
    duration_min        = Column(Integer, default=60)
    meeting_type        = Column(String)                       # "quarterly_review", "onboarding", "adhoc"
    agenda_notes        = Column(Text)
    brief_generated     = Column(Boolean, default=False)
    brief_content       = Column(JSON)
    brief_generated_at  = Column(DateTime)

    client              = relationship("Client", back_populates="meetings")


class Interaction(Base):
    """Historical log of all advisor-client interactions."""
    __tablename__ = "interactions"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    client_id           = Column(Integer, ForeignKey("clients.id"), nullable=False)
    interaction_date    = Column(Date, nullable=False)
    type                = Column(String)                       # "meeting", "email", "call", "note"
    summary             = Column(Text)
    sentiment           = Column(String)                       # "positive", "neutral", "negative", "anxious"

    client              = relationship("Client", back_populates="interactions")


class MarketCache(Base):
    """Prevents re-fetching market data within 15 minutes."""
    __tablename__ = "market_cache"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    ticker          = Column(String, nullable=False)
    fetched_at      = Column(DateTime, nullable=False)
    current_price   = Column(Float)
    price_30d_ago   = Column(Float)
    price_1y_ago    = Column(Float)
    ytd_return      = Column(Float)
    volatility_30d  = Column(Float)           # annualized
    beta            = Column(Float)
