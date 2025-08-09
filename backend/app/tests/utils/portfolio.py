from sqlalchemy.orm import Session

from app import crud, schemas
from app.models.portfolio import Portfolio


def create_test_portfolio(db: Session, *, user_id: int, name: str) -> Portfolio:
    """
    Test utility to create a portfolio for a given user.
    """
    portfolio_in = schemas.PortfolioCreate(
        name=name, description=f"Test portfolio for user {user_id}"
    )
    return crud.portfolio.create_with_owner(db=db, obj_in=portfolio_in, user_id=user_id)
