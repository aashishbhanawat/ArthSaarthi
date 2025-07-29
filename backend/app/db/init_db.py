import logging
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from tenacity import retry, stop_after_attempt, wait_fixed

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1

@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
)
def init() -> None:
    try:
        db_url = str(settings.DATABASE_URL)
        engine = create_engine(db_url, isolation_level="AUTOCOMMIT")
        if not database_exists(engine.url):
            logger.info(f"Database {engine.url.database} does not exist. Creating...")
            create_database(engine.url)
            logger.info("Database created.")
    except Exception as e:
        logger.error(e)
        raise e

def main() -> None:
    logger.info("Initializing service")
    init()
    logger.info("Service finished initializing")

if __name__ == "__main__":
    main()