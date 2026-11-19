import asyncio
import logging
from typing import Dict

from app.db.session import SessionLocal
from app.services.news_service import news_service

logger = logging.getLogger(__name__)


async def run_market_news_job() -> Dict[str, int]:
    """
    Executes background synchronization of market news, broker research reports,
    earnings concalls, and company results for active portfolio holdings.
    Runs blocking HTTP & DB operations in a thread pool executor.
    """
    logger.info("Starting market research & news feed background sync job...")
    db = SessionLocal()
    try:
        loop = asyncio.get_running_loop()
        fetched, saved = await loop.run_in_executor(
            None, news_service.sync_all_feeds, db
        )
        logger.info(
            "Market research news job finished successfully. %d articles fetched, %d saved/updated.",
            fetched,
            saved,
        )
        return {"fetched": fetched, "saved": saved}
    except Exception as e:
        logger.error(
            "Error executing market research news feed job: %s",
            e,
            exc_info=True,
        )
        raise
    finally:
        db.close()
