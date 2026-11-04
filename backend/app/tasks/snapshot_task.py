import asyncio
import logging

from app.db.session import SessionLocal
from app.services.snapshot_service import take_daily_snapshots_for_all

logger = logging.getLogger(__name__)


async def run_daily_snapshot_job() -> int:
    """
    Executes daily portfolio valuation snapshots for all users and portfolios.
    Runs blocking DB operations in a thread executor to ensure the asyncio
    event loop remains completely non-blocking.
    """
    logger.info("Executing daily portfolio snapshot background job...")
    db = SessionLocal()
    try:
        loop = asyncio.get_running_loop()
        count = await loop.run_in_executor(None, take_daily_snapshots_for_all, db)
        logger.info(
            f"Daily snapshot job finished successfully. {count} portfolios updated."
        )
        return count
    except Exception as e:
        logger.error(f"Error during daily snapshot execution: {e}", exc_info=True)
        raise
    finally:
        db.close()
