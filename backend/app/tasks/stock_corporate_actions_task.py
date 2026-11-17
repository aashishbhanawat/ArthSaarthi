import asyncio
import logging
from datetime import date
from typing import Optional

from app.db.session import SessionLocal
from app.services.corporate_actions.stock_engine import process_stock_corporate_actions

logger = logging.getLogger(__name__)


async def run_stock_corporate_actions_job(check_date: Optional[date] = None) -> int:
    """
    Executes automated equity corporate actions (dividends, splits, and bonus shares)
    for all active stock holdings across user portfolios.
    Runs blocking operations in a thread executor to ensure the asyncio
    event loop remains non-blocking.
    """
    logger.info("Executing automated stock corporate actions background job...")
    db = SessionLocal()
    try:
        loop = asyncio.get_running_loop()
        events = await loop.run_in_executor(
            None, process_stock_corporate_actions, db, check_date
        )
        count = len(events)
        logger.info(
            "Stock corporate actions job finished successfully. %d events created.",
            count,
        )
        return count
    except Exception as e:
        logger.error(
            "Error during automated stock corporate action execution: %s",
            e,
            exc_info=True,
        )
        raise
    finally:
        db.close()
