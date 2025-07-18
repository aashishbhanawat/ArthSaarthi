from sqlalchemy.orm import Session

from app import crud, schemas
from app.models.portfolio import Portfolio
from app.models.user import User


def create_test_portfolio(db: Session, user: User, name: str = "Test Portfolio") -> Portfolio:
    portfolio_in = schemas.PortfolioCreate(name=name)
    return crud.portfolio.create_with_owner(db=db, obj_in=portfolio_in, user_id=user.id)