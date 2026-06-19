import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.user import create_random_user

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")


def test_ppf_account_multi_user_creation(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    # Create User 1
    user1, password1 = create_random_user(db)
    portfolio1 = create_test_portfolio(db, user_id=user1.id, name="User 1 Portfolio")
    headers1 = get_auth_headers(user1.email, password1)

    # Create User 2
    user2, password2 = create_random_user(db)
    portfolio2 = create_test_portfolio(db, user_id=user2.id, name="User 2 Portfolio")
    headers2 = get_auth_headers(user2.email, password2)

    # Both users will create a PPF account with the SAME account number "PPF-DUP-12345"
    shared_account_num = "PPF-DUP-12345"

    # 1. User 1 creates PPF Account
    ppf_data_1 = {
        "institution_name": "User 1 PPF Bank",
        "portfolio_id": str(portfolio1.id),
        "account_number": shared_account_num,
        "opening_date": "2023-04-01",
        "amount": 15000,
        "contribution_date": "2023-04-10",
    }
    response1 = client.post(
        f"{settings.API_V1_STR}/ppf-accounts/",
        headers=headers1,
        json=ppf_data_1,
    )
    assert response1.status_code == 201
    asset_id_1 = response1.json()["asset"]["id"]
    asset1 = crud.asset.get(db, id=asset_id_1)
    assert asset1 is not None
    assert asset1.account_number == shared_account_num
    assert str(user1.id)[:8].upper() in asset1.ticker_symbol

    # 2. User 2 creates PPF Account with the SAME account number
    ppf_data_2 = {
        "institution_name": "User 2 PPF Bank",
        "portfolio_id": str(portfolio2.id),
        "account_number": shared_account_num,
        "opening_date": "2023-04-01",
        "amount": 25000,
        "contribution_date": "2023-04-15",
    }
    response2 = client.post(
        f"{settings.API_V1_STR}/ppf-accounts/",
        headers=headers2,
        json=ppf_data_2,
    )
    assert response2.status_code == 201
    asset_id_2 = response2.json()["asset"]["id"]
    asset2 = crud.asset.get(db, id=asset_id_2)
    assert asset2 is not None
    assert asset2.account_number == shared_account_num
    assert str(user2.id)[:8].upper() in asset2.ticker_symbol

    # Assert ticker symbols are distinct
    assert asset1.ticker_symbol != asset2.ticker_symbol


def test_ppf_multi_user_backup_restore(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    # Setup two users with the same PPF account number
    user1, password1 = create_random_user(db)
    portfolio1 = create_test_portfolio(
        db, user_id=user1.id, name="User 1 Portfolio Backup"
    )
    headers1 = get_auth_headers(user1.email, password1)

    shared_account_num = "PPF-BACKUP-9999"

    # User 1 creates PPF Account
    ppf_data_1 = {
        "institution_name": "User 1 Bank",
        "portfolio_id": str(portfolio1.id),
        "account_number": shared_account_num,
        "opening_date": "2023-04-01",
        "amount": 5000,
        "contribution_date": "2023-04-10",
    }
    response1 = client.post(
        f"{settings.API_V1_STR}/ppf-accounts/",
        headers=headers1,
        json=ppf_data_1,
    )
    assert response1.status_code == 201

    # 1. Test Backup for User 1
    backup_resp = client.get("/api/v1/users/me/backup", headers=headers1)
    assert backup_resp.status_code == 200
    backup_data = backup_resp.json()

    # Verify backup structures
    assert len(backup_data["data"]["ppf_accounts"]) == 1
    ppf_accs = backup_data["data"]["ppf_accounts"]
    assert ppf_accs[0]["account_number"] == shared_account_num

    # 2. Test Restore for User 1
    file_content = json.dumps(backup_data).encode("utf-8")
    files = {"file": ("backup.json", file_content, "application/json")}
    restore_resp = client.post(
        "/api/v1/users/me/restore", headers=headers1, files=files
    )
    assert restore_resp.status_code == 200

    # Verify restored data
    db.expire_all()
    restored_portfolios = crud.portfolio.get_multi_by_owner(db, user_id=user1.id)
    assert len(restored_portfolios) == 1
    transactions = crud.transaction.get_multi_by_portfolio(
        db, portfolio_id=restored_portfolios[0].id
    )
    assert len(transactions) == 1
    assert str(user1.id)[:8].upper() in transactions[0].asset.ticker_symbol


def test_ppf_legacy_backup_restore(
    client: TestClient, db: Session, get_auth_headers
) -> None:
    # Test that a legacy backup JSON is restored correctly
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)

    legacy_account_num = "112233"

    # Construct legacy backup JSON manually
    legacy_backup = {
        "metadata": {
            "version": "1.2"
        },
        "data": {
            "portfolios": [
                {"name": "Legacy Portfolio", "description": "Legacy test"}
            ],
            "ppf_accounts": [
                {
                    "account_number": legacy_account_num,
                    "institution": "Legacy Bank",
                    "opening_date": "2020-04-01"
                }
            ],
            "transactions": [
                {
                    "portfolio_name": "Legacy Portfolio",
                    "transaction_type": "PPF_CONTRIBUTION",
                    "quantity": 1000.0,
                    "price_per_unit": 1.0,
                    "transaction_date": "2020-04-05",
                    "fees": 0.0,
                    "ppf_account_number": legacy_account_num
                }
            ]
        }
    }

    file_content = json.dumps(legacy_backup).encode("utf-8")
    files = {"file": ("backup.json", file_content, "application/json")}
    restore_resp = client.post(
        "/api/v1/users/me/restore", headers=headers, files=files
    )
    assert restore_resp.status_code == 200

    # Verify data is restored under the new user-specific ticker
    db.expire_all()
    portfolios = crud.portfolio.get_multi_by_owner(db, user_id=user.id)
    assert len(portfolios) == 1
    transactions = crud.transaction.get_multi_by_portfolio(
        db, portfolio_id=portfolios[0].id
    )
    assert len(transactions) == 1

    # It should restore as the new ticker since the old one
    # didn't exist in the database yet
    expected_new_ticker = f"PPF-{str(user.id)[:8]}-{legacy_account_num}".upper()
    assert transactions[0].asset.ticker_symbol == expected_new_ticker
