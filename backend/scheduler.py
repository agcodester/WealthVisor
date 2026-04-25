"""
WealthVisor — Scheduler
APScheduler checks for upcoming meetings every 5 minutes and triggers the pipeline.
"""

import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.database import SessionLocal
from backend.database.crud import get_meetings_needing_briefs
from backend.agents.orchestrator import run_pipeline

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


@scheduler.scheduled_job('interval', minutes=5, id='check_meetings')
async def check_upcoming_meetings():
    """
    Every 5 minutes:
    1. Query meetings where scheduled_at is between now+20min and now+40min
    2. Filter to brief_generated == False
    3. Trigger LangGraph pipeline for each
    4. Log results
    """
    try:
        db = SessionLocal()
        meetings = get_meetings_needing_briefs(db)
        db.close()

        if not meetings:
            logger.debug("[Scheduler] No upcoming meetings needing briefs")
            return

        logger.info(f"[Scheduler] Found {len(meetings)} meeting(s) needing briefs")

        for meeting in meetings:
            try:
                logger.info(
                    f"[Scheduler] Triggering pipeline for meeting #{meeting.id} "
                    f"(client #{meeting.client_id}, at {meeting.scheduled_at})"
                )
                await run_pipeline(
                    meeting_id=meeting.id,
                    client_id=meeting.client_id,
                    scheduled_at=meeting.scheduled_at,
                    meeting_type=meeting.meeting_type,
                )
                logger.info(f"[Scheduler] ✅ Brief generated for meeting #{meeting.id}")
            except Exception as e:
                logger.error(f"[Scheduler] ❌ Failed to generate brief for meeting #{meeting.id}: {e}")

    except Exception as e:
        logger.error(f"[Scheduler] Error checking meetings: {e}")
