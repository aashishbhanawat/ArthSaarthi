from typing import Callable, Dict
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.tests.utils.asset import create_test_asset
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.user import create_random_user


@pytest.mark.usefixtures("pre_unlocked_key_manager")
def test_create_transaction_generic_error_message(
    client: TestClient,
    db: Session,
    get_auth_headers: Callable[[str, str], Dict[str, str]],
) -> None:
    # Setup user and portfolio
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)

    portfolio = create_test_portfolio(db, user_id=user.id, name="Test Portfolio")
    asset = create_test_asset(db, ticker_symbol="TEST-LEAK")

    # Mock crud.transaction.create_with_portfolio to raise an Exception
    # This path might need to be adjusted based on how it's imported in the endpoint
    patch_target = (
        "app.api.v1.endpoints.transactions.crud.transaction.create_with_portfolio"
    )
    with patch(patch_target) as mock_create:
        mock_create.side_effect = Exception("Sensitive DB Information Leaked")

        # Payload
        data = {
            "asset_id": str(asset.id),
            "transaction_type": "BUY",
            "quantity": 10,
            "price_per_unit": 100,
            "transaction_date": "2023-01-01T00:00:00",
            "fees": 0,
        }

        response = client.post(
            f"{settings.API_V1_STR}/transactions/?portfolio_id={portfolio.id}",
            headers=headers,
            json=data,
        )

        assert response.status_code == 400
        # Expect generic error message instead of leaked detail
        expected_msg = "An error occurred while creating the transaction."
        assert response.json()["detail"] == expected_msg
