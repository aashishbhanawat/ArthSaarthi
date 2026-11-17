import asyncio
import logging
from datetime import date
from typing import Optional

from app.db.session import SessionLocal
from app.services.corporate_actions.bond_engine import process_bond_corporate_actions

logger = logging.getLogger(__name__)


async def run_bond_corporate_actions_job(check_date: Optional[date] = None) -> int:
    """
    Executes automated bond corporate actions (coupons and maturity redemptions)
    for all active bond holdings across user portfolios.
    Runs blocking DB operations in a thread executor to ensure the asyncio
    event loop remains completely non-blocking.
    """
    logger.info("Executing automated bond corporate actions background job...")
    db = SessionLocal()
    try:
        loop = asyncio.get_running_loop()
        events = await loop.run_in_executor(
            None, process_bond_corporate_actions, db, check_date
        )
        count = len(events)
        logger.info(
            "Bond corporate actions job finished successfully. %d events created.",
            count,
        )
        return count
    except Exception as e:
        logger.error(
            "Error during automated bond corporate action execution: %s",
            e,
            exc_info=True,
        )
        raise
    finally:
        db.close()
