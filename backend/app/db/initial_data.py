import logging

from sqlalchemy.orm import Session

from app.crud import crud_historical_interest_rate
from app.db.seed_data.ppf_interest_rates import HISTORICAL_PPF_RATES
from app.schemas.historical_interest_rate import HistoricalInterestRateCreate

logger = logging.getLogger(__name__)


def seed_interest_rates(db: Session) -> None:
    """
    Seeds the historical interest rates for PPF.
    """
    logger.info("Seeding historical PPF interest rates...")
    for rate_data in HISTORICAL_PPF_RATES:
        rate = (
            crud_historical_interest_rate.historical_interest_rate.get_by_scheme_and_start_date(
                db, scheme_name="PPF", start_date=rate_data["start_date"]
            )
        )
        if not rate:
            crud_historical_interest_rate.historical_interest_rate.create(
                db,
                obj_in=HistoricalInterestRateCreate(
                    scheme_name="PPF",
                    start_date=rate_data["start_date"],
                    end_date=rate_data["end_date"],
                    rate=rate_data["rate"],
                ),
            )
    logger.info("Finished seeding historical PPF interest rates.")
