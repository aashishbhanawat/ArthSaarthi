from typing import Callable, Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.user import create_random_user

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")

def test_capital_gains_unauthenticated(client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/capital-gains/?fy=2025-26")
    assert response.status_code == 401

def test_dividends_unauthenticated(client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/dividends/?fy=2025-26")
    assert response.status_code == 401

def test_capital_gains_idor_portfolio(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
) -> None:
    # User 1
    user1, password1 = create_random_user(db)
    user1_headers = get_auth_headers(user1.email, password1)

    # User 2 and their portfolio
    user2, _ = create_random_user(db)
    portfolio2 = create_test_portfolio(db, user_id=user2.id, name="User 2 Portfolio")

    # User 1 tries to access User 2's portfolio
    response = client.get(
        f"{settings.API_V1_STR}/capital-gains/?fy=2025-26&portfolio_id={portfolio2.id}",
        headers=user1_headers
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions"

def test_dividends_idor_portfolio(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
) -> None:
    # User 1
    user1, password1 = create_random_user(db)
    user1_headers = get_auth_headers(user1.email, password1)

    # User 2 and their portfolio
    user2, _ = create_random_user(db)
    portfolio2 = create_test_portfolio(db, user_id=user2.id, name="User 2 Portfolio")

    # User 1 tries to access User 2's portfolio
    response = client.get(
        f"{settings.API_V1_STR}/dividends/?fy=2025-26&portfolio_id={portfolio2.id}",
        headers=user1_headers
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions"
