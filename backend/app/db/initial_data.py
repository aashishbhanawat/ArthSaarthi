import logging

from sqlalchemy.orm import Session

from app import schemas
from app.db.seed_data.ppf_interest_rates import HISTORICAL_PPF_RATES

logger = logging.getLogger(__name__)


def seed_interest_rates(db: Session) -> None:
    """
    Seeds the historical_interest_rates table with PPF rates.
    """
    from app import crud
    logger.info("Seeding historical PPF interest rates...")
    count = 0
    for rate_data in HISTORICAL_PPF_RATES:
        rate = crud.historical_interest_rate.get_by_scheme_and_start_date(
            db, scheme_name="PPF", start_date=rate_data["start_date"]
        )
        if not rate:
            rate_in = schemas.HistoricalInterestRateCreate(
                **rate_data, scheme_name="PPF"
            )
            crud.historical_interest_rate.create(db, obj_in=rate_in)
            count += 1
    logger.info(f"Seeded {count} new historical PPF rates.")
