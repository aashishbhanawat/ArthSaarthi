from decimal import Decimal
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app import crud
from app.tests.utils.goal import create_random_goal
from app.tests.utils.user import create_random_user
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.asset import create_test_asset
from app.schemas.goal import GoalLinkCreate


def test_get_goal_analytics_no_links(db: Session):
    user, _ = create_random_user(db)
    goal = create_random_goal(db, user_id=user.id, target_amount=Decimal("10000"))
    db.commit()

    analytics = crud.goal.get_goal_analytics(db, goal)

    assert analytics["current_value"] == Decimal("0")
    assert analytics["progress"] == 0


def test_get_goal_analytics_with_portfolio_link(db: Session, mocker):
    user, _ = create_random_user(db)
    goal = create_random_goal(db, user_id=user.id, target_amount=Decimal("10000"))
    portfolio = create_test_portfolio(db, user_id=user.id, name="Test Portfolio")
    link_in = GoalLinkCreate(portfolio_id=portfolio.id, goal_id=goal.id)
    crud.goal_link.create_with_owner(db, obj_in=link_in, user_id=user.id)
    db.commit()

    mocker.patch(
        "app.crud.crud_analytics._get_portfolio_current_value",
        return_value=Decimal("2500"),
    )

    analytics = crud.goal.get_goal_analytics(db, goal)

    assert analytics["current_value"] == Decimal("2500")
    assert analytics["progress"] == 25


def test_get_goal_analytics_with_asset_link(db: Session, mocker):
    user, _ = create_random_user(db)
    goal = create_random_goal(db, user_id=user.id, target_amount=Decimal("10000"))
    asset = create_test_asset(db, ticker_symbol="AAPL")
    link_in = GoalLinkCreate(asset_id=asset.id, goal_id=goal.id)
    crud.goal_link.create_with_owner(db, obj_in=link_in, user_id=user.id)
    db.commit()

    mocker.patch(
        "app.crud.crud_goal._get_standalone_asset_current_value",
        return_value=Decimal("1500"),
    )

    analytics = crud.goal.get_goal_analytics(db, goal)

    assert analytics["current_value"] == Decimal("1500")
    assert analytics["progress"] == 15


def test_get_goal_analytics_with_mixed_links(db: Session, mocker):
    user, _ = create_random_user(db)
    goal = create_random_goal(db, user_id=user.id, target_amount=Decimal("10000"))
    portfolio = create_test_portfolio(db, user_id=user.id, name="Test Portfolio")
    asset = create_test_asset(db, ticker_symbol="GOOG")

    link1_in = GoalLinkCreate(portfolio_id=portfolio.id, goal_id=goal.id)
    crud.goal_link.create_with_owner(db, obj_in=link1_in, user_id=user.id)

    link2_in = GoalLinkCreate(asset_id=asset.id, goal_id=goal.id)
    crud.goal_link.create_with_owner(db, obj_in=link2_in, user_id=user.id)
    db.commit()

    mocker.patch(
        "app.crud.crud_analytics._get_portfolio_current_value",
        return_value=Decimal("3000"),
    )
    mocker.patch(
        "app.crud.crud_goal._get_standalone_asset_current_value",
        return_value=Decimal("2000"),
    )

    analytics = crud.goal.get_goal_analytics(db, goal)

    assert analytics["current_value"] == Decimal("5000")
    assert analytics["progress"] == 50
