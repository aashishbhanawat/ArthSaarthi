import logging

from sqlalchemy.orm import Session

from app import schemas
from app.db.seed_data.ppf_interest_rates import HISTORICAL_PPF_RATES

logger = logging.getLogger(__name__)


def seed_interest_rates(db: Session) -> None:
    """
    Seeds or updates the historical_interest_rates table with PPF rates.
    - Creates new records for rates that don't exist
    - Updates existing records if end_date or rate has changed
    """
    from app import crud
    logger.info("Seeding historical PPF interest rates...")
    created_count = 0
    updated_count = 0

    for rate_data in HISTORICAL_PPF_RATES:
        existing = crud.historical_interest_rate.get_by_scheme_and_start_date(
            db, scheme_name="PPF", start_date=rate_data["start_date"]
        )
        if not existing:
            # Create new record
            rate_in = schemas.HistoricalInterestRateCreate(
                **rate_data, scheme_name="PPF"
            )
            crud.historical_interest_rate.create(db, obj_in=rate_in)
            created_count += 1
        else:
            # Check if update is needed (end_date or rate changed)
            needs_update = (
                existing.end_date != rate_data["end_date"] or
                existing.rate != rate_data["rate"]
            )
            if needs_update:
                update_data = schemas.HistoricalInterestRateUpdate(
                    end_date=rate_data["end_date"],
                    rate=rate_data["rate"]
                )
                crud.historical_interest_rate.update(
                    db, db_obj=existing, obj_in=update_data
                )
                updated_count += 1
                logger.info(
                    f"Updated PPF rate for {rate_data['start_date']}: "
                    f"end_date={rate_data['end_date']}, rate={rate_data['rate']}"
                )

    logger.info(f"PPF rates: {created_count} created, {updated_count} updated.")
