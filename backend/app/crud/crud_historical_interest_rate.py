from datetime import date

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.historical_interest_rate import HistoricalInterestRate
from app.schemas.historical_interest_rate import (
    HistoricalInterestRateCreate,
    HistoricalInterestRateUpdate,
)


class CRUDHistoricalInterestRate(
    CRUDBase[
        HistoricalInterestRate,
        HistoricalInterestRateCreate,
        HistoricalInterestRateUpdate,
    ]
):
    def get_by_scheme_and_start_date(
        self, db: Session, *, scheme_name: str, start_date: date
    ) -> HistoricalInterestRate | None:
        return (
            db.query(self.model)
            .filter(
                self.model.scheme_name == scheme_name,
                self.model.start_date == start_date,
            )
            .first()
        )


historical_interest_rate = CRUDHistoricalInterestRate(HistoricalInterestRate)
