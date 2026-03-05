import logging
import sys

from app.db.session import SessionLocal
from app.services.snapshot_service import take_daily_snapshots_for_all

# Configure basic logging for the script
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Starting daily portfolio snapshot job...")
    db = SessionLocal()
    try:
        count = take_daily_snapshots_for_all(db)
        logger.info(f"Successfully created/updated {count} daily portfolio snapshots.")
    except Exception as e:
        logger.error(f"Error running daily snapshot job: {e}")
        sys.exit(1)
    finally:
        db.close()

    logger.info("Daily portfolio snapshot job completed.")


if __name__ == "__main__":
    main()
