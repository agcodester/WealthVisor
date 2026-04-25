"""
WealthVisor — FastAPI Backend
All API endpoints for the wealth advisor copilot.
"""

import os
import sys
import logging
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

load_dotenv()

from backend.database import SessionLocal, init_db
from backend.database import crud
from backend.agents.orchestrator import run_pipeline
from backend.scheduler import scheduler

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─── Lifespan ────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("🚀 WealthVisor starting up...")
    init_db()
    logger.info("  ✓ Database initialized")

    # Check Qdrant
    try:
        from backend.tools.vector_store import check_qdrant_health
        if check_qdrant_health():
            logger.info("  ✓ Qdrant connected")
        else:
            logger.warning("  ⚠ Qdrant not available — briefs won't be vectorized")
    except Exception:
        logger.warning("  ⚠ Qdrant not available")

    # Start scheduler
    scheduler.start()
    logger.info("  ✓ Scheduler started (checking every 5 min)")
    logger.info("🟢 WealthVisor ready at http://localhost:8000")

    yield

    # Shutdown
    scheduler.shutdown()
    logger.info("🔴 WealthVisor shut down")


# ─── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="WealthVisor API",
    description="Agentic Pre-Meeting Intelligence System for Indian Wealth Advisors",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    db_ok = False
    qdrant_ok = False
    try:
        db = SessionLocal()
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db.close()
        db_ok = True
    except Exception:
        pass
    try:
        from backend.tools.vector_store import check_qdrant_health
        qdrant_ok = check_qdrant_health()
    except Exception:
        pass
    return {"status": "ok", "db": "connected" if db_ok else "disconnected", "qdrant": "connected" if qdrant_ok else "disconnected"}


@app.get("/clients")
async def list_clients():
    """Returns all clients with upcoming meeting count."""
    db = SessionLocal()
    try:
        clients = crud.get_all_clients(db)
        return clients
    finally:
        db.close()


@app.get("/clients/{client_id}")
async def get_client(client_id: int):
    """Returns full client profile with holdings, tax_lots, interactions, meetings."""
    db = SessionLocal()
    try:
        client = crud.get_client_with_holdings(db, client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        return client
    finally:
        db.close()


@app.get("/meetings")
async def list_meetings(upcoming_only: bool = True):
    """Returns meetings. upcoming_only=True filters to future meetings."""
    db = SessionLocal()
    try:
        meetings = crud.get_all_meetings(db, upcoming_only=upcoming_only)
        return meetings
    finally:
        db.close()


@app.get("/meetings/{meeting_id}")
async def get_meeting(meeting_id: int):
    """Returns full meeting including brief_content if generated."""
    db = SessionLocal()
    try:
        meeting = crud.get_meeting(db, meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return meeting
    finally:
        db.close()


async def _generate_brief_background(meeting_id: int):
    """Background task to generate a meeting brief."""
    db = SessionLocal()
    try:
        meeting = crud.get_meeting(db, meeting_id)
        if not meeting:
            logger.error(f"Meeting {meeting_id} not found for brief generation")
            return

        scheduled_at = meeting.get("scheduled_at")
        if isinstance(scheduled_at, str):
            scheduled_at = datetime.fromisoformat(scheduled_at)
        elif scheduled_at is None:
            scheduled_at = datetime.now()

        await run_pipeline(
            meeting_id=meeting_id,
            client_id=meeting["client_id"],
            scheduled_at=scheduled_at,
            meeting_type=meeting.get("meeting_type", "review"),
        )
    except Exception as e:
        logger.error(f"Background brief generation failed for meeting {meeting_id}: {e}")
    finally:
        db.close()


@app.post("/meetings/{meeting_id}/generate-brief")
async def generate_brief(meeting_id: int, background_tasks: BackgroundTasks):
    """
    Triggers LangGraph pipeline for this meeting.
    Runs in background. Returns immediately.
    """
    db = SessionLocal()
    try:
        meeting = crud.get_meeting(db, meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        if meeting.get("brief_generated"):
            return {"status": "already_generated", "meeting_id": meeting_id}
    finally:
        db.close()

    background_tasks.add_task(_generate_brief_background, meeting_id)
    return {"status": "generating", "meeting_id": meeting_id}


@app.get("/meetings/{meeting_id}/brief")
async def get_brief(meeting_id: int):
    """Returns the generated brief for a meeting. 404 if not yet generated."""
    db = SessionLocal()
    try:
        meeting = crud.get_meeting(db, meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        if not meeting.get("brief_generated"):
            raise HTTPException(status_code=404, detail="Brief not yet generated")
        return {
            "meeting_id": meeting_id,
            "brief_content": meeting.get("brief_content"),
            "brief_generated_at": meeting.get("brief_generated_at"),
        }
    finally:
        db.close()


@app.get("/portfolio/{client_id}/snapshot")
async def portfolio_snapshot(client_id: int):
    """Returns current portfolio snapshot without running the full pipeline."""
    db = SessionLocal()
    try:
        client = crud.get_client_with_holdings(db, client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        return {
            "client_id": client_id,
            "name": client["name"],
            "aum": client["aum"],
            "holdings_count": len(client["holdings"]),
            "holdings": client["holdings"],
        }
    finally:
        db.close()


@app.get("/portfolio/{client_id}/tax-opportunities")
async def tax_opportunities(client_id: int):
    """Returns tax analysis for a client."""
    db = SessionLocal()
    try:
        client = crud.get_client_with_holdings(db, client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        from backend.tools.market_tools import get_multiple_prices
        from backend.tools.tax_tools import scan_ltcg_stcg_opportunities, estimate_elss_opportunity

        tickers = list(set(h["ticker"] for h in client["holdings"]))
        prices = get_multiple_prices(tickers)

        tax_lots = crud.get_client_tax_lots(db, client_id)
        result = scan_ltcg_stcg_opportunities(tax_lots, prices, client["tax_bracket"])

        elss = estimate_elss_opportunity(
            client["age"], client["tax_bracket"],
            client["annual_income"], client["investment_goal"],
        )

        return {
            "client_id": client_id,
            "ltcg_stcg": result,
            "elss_recommendation": elss,
        }
    finally:
        db.close()


@app.get("/stats")
async def dashboard_stats():
    """Returns dashboard-level metrics."""
    db = SessionLocal()
    try:
        return crud.get_dashboard_stats(db)
    finally:
        db.close()


# ─── Run directly ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
