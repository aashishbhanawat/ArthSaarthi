import uuid
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.config import settings
from app.models.bond import Bond
from app.models.corporate_action_event import CorporateActionEvent
from app.schemas.asset import AssetType
from app.schemas.enums import PaymentFrequency
from app.tests.utils.user import create_random_user, get_access_token

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")


def test_corporate_action_events_api_flow(
    client: TestClient,
    db: Session,
) -> None:
    regular_user, password = create_random_user(db, is_admin=False)
    token = get_access_token(client, regular_user.email, password)
    headers = {"Authorization": f"Bearer {token}"}

    portfolio = crud.portfolio.create_with_owner(
        db,
        obj_in=schemas.PortfolioCreate(name=f"Bond Test Port {uuid.uuid4().hex[:4]}"),
        user_id=regular_user.id,
    )
    asset = crud.asset.create(
        db,
        obj_in=schemas.AssetCreate(
            name="Test Gov Bond 2026",
            ticker_symbol=f"GOV-{uuid.uuid4().hex[:6]}",
            asset_type=AssetType.BOND,
            currency="INR",
        ),
    )
    bond = Bond(
        id=uuid.uuid4(),
        asset_id=asset.id,
        bond_type="GOVERNMENT",
        face_value=Decimal("1000.00"),
        coupon_rate=Decimal("7.0"),
        maturity_date=date(2030, 1, 1),
        payment_frequency=PaymentFrequency.ANNUALLY,
        isin="IN0030000001",
    )
    db.add(bond)
    db.commit()

    # Create dummy corporate action events
    event1 = CorporateActionEvent(
        user_id=regular_user.id,
        portfolio_id=portfolio.id,
        asset_id=asset.id,
        event_type="BOND_COUPON",
        event_date=date(2026, 11, 8),
        units=Decimal("10"),
        amount=Decimal("700.00"),
        status="NEW",
        details={"bond_name": asset.name},
    )
    event2 = CorporateActionEvent(
        user_id=regular_user.id,
        portfolio_id=portfolio.id,
        asset_id=asset.id,
        event_type="BOND_MATURITY",
        event_date=date(2026, 11, 8),
        units=Decimal("10"),
        amount=Decimal("10000.00"),
        status="NEW",
        details={"bond_name": asset.name},
    )
    db.add(event1)
    db.add(event2)
    db.commit()

    # 1. GET /corporate-actions/events
    res = client.get(
        f"{settings.API_V1_STR}/corporate-actions/events",
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 2
    assert data["unread_count"] >= 2

    # 2. POST /corporate-actions/events/{event_id}/dismiss
    res_dismiss = client.post(
        f"{settings.API_V1_STR}/corporate-actions/events/{event1.id}/dismiss",
        headers=headers,
    )
    assert res_dismiss.status_code == 200
    assert res_dismiss.json()["status"] == "DISMISSED"

    # 3. POST /corporate-actions/events/dismiss-all
    res_dismiss_all = client.post(
        f"{settings.API_V1_STR}/corporate-actions/events/dismiss-all",
        headers=headers,
    )
    assert res_dismiss_all.status_code == 200
    assert res_dismiss_all.json()["dismissed_count"] >= 1

    # Verify unread count is now 0
    res_after = client.get(
        f"{settings.API_V1_STR}/corporate-actions/events",
        headers=headers,
    )
    assert res_after.json()["unread_count"] == 0
