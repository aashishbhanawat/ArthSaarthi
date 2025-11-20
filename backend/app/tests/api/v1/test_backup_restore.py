import json
from datetime import date, datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud, schemas
from app.tests.utils.portfolio import create_test_portfolio
from app.tests.utils.transaction import create_test_transaction
from app.tests.utils.user import create_random_user


def test_backup_restore_flow(client: TestClient, db: Session, get_auth_headers):
    # 1. Setup Data
    user, password = create_random_user(db)
    headers = get_auth_headers(user.email, password)

    portfolio = create_test_portfolio(db, user_id=user.id, name="Test Portfolio")

    # Create a Stock Transaction
    create_test_transaction(
        db,
        portfolio_id=portfolio.id,
        ticker="RELIANCE",
        quantity=10,
        price_per_unit=2000,
        transaction_type="BUY",
        transaction_date=date(2023, 1, 15)
    )

    # Create a PPF Asset manually
    ppf_asset_in = schemas.AssetCreate(
        name="My PPF",
        ticker_symbol="PPF-12345",
        asset_type="PPF",
        currency="INR",
        account_number="12345",
        opening_date=date(2020, 4, 1)
    )
    ppf_asset = crud.asset.create(db, obj_in=ppf_asset_in)

    # Create a PPF Transaction
    ppf_tx_in = schemas.TransactionCreate(
        asset_id=ppf_asset.id,
        transaction_type="CONTRIBUTION",
        quantity=10000,
        price_per_unit=1,
        transaction_date=datetime(2023, 4, 1),
    )
    crud.transaction.create_with_portfolio(db, obj_in=ppf_tx_in, portfolio_id=portfolio.id)

    # 2. Backup
    response = client.get("/api/v1/users/me/backup", headers=headers)
    assert response.status_code == 200
    backup_data = response.json()

    # Verify structure
    assert "metadata" in backup_data
    assert "data" in backup_data
    assert len(backup_data["data"]["portfolios"]) == 1
    assert len(backup_data["data"]["transactions"]) == 2
    assert len(backup_data["data"]["ppf_accounts"]) == 1

    # Verify Transaction Type mapping
    txs = backup_data["data"]["transactions"]
    ppf_tx = next((t for t in txs if t.get("ppf_account_number") == "12345"), None)
    assert ppf_tx is not None
    assert ppf_tx["transaction_type"] == "PPF_CONTRIBUTION"

    # 3. Restore (Wipe and Restore)
    file_content = json.dumps(backup_data).encode('utf-8')
    files = {'file': ('backup.json', file_content, 'application/json')}

    response = client.post("/api/v1/users/me/restore", headers=headers, files=files)
    assert response.status_code == 200
    assert response.json()["message"] == "Restore successful"

    # 4. Verify Data Restored
    db.expire_all()
    portfolios = crud.portfolio.get_multi_by_owner(db, user_id=user.id)
    assert len(portfolios) == 1
    assert portfolios[0].name == "Test Portfolio"

    transactions = crud.transaction.get_multi_by_portfolio(db, portfolio_id=portfolios[0].id)
    assert len(transactions) == 2

    # Check PPF transaction
    t_ppf = next((t for t in transactions if t.asset.ticker_symbol == "PPF-12345"), None)
    assert t_ppf is not None
    assert t_ppf.transaction_type == "CONTRIBUTION"
    assert t_ppf.quantity == 10000
