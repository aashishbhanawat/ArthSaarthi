import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.schemas.market_news import MarketNewsArticleCreate
from app.tests.utils.user import create_random_user, get_access_token

pytestmark = pytest.mark.usefixtures("pre_unlocked_key_manager")


def test_news_feed_and_summary_api(
    client: TestClient,
    db: Session,
) -> None:
    regular_user, password = create_random_user(db, is_admin=False)
    token = get_access_token(client, regular_user.email, password)
    headers = {"Authorization": f"Bearer {token}"}

    # Seed test articles
    article_1 = MarketNewsArticleCreate(
        id=f"art1-{uuid.uuid4().hex[:8]}",
        title="RECLTD reports 24% rise in Q2 net profit",
        summary="REC Limited posted strong quarterly numbers driven by loan growth.",
        url=f"https://example.com/rec-q2-{uuid.uuid4().hex[:6]}",
        source="Moneycontrol",
        category="NEWS",
        published_at=datetime.now(timezone.utc),
        symbols=["RECLTD"],
        sentiment="POSITIVE",
    )
    article_2 = MarketNewsArticleCreate(
        id=f"art2-{uuid.uuid4().hex[:8]}",
        title="Buy RECLTD; target of Rs 600: Motilal Oswal",
        summary="Motilal Oswal maintains buy rating with revised target.",
        url=f"https://example.com/rec-target-{uuid.uuid4().hex[:6]}",
        source="Moneycontrol Research",
        category="BROKER_REPORT",
        published_at=datetime.now(timezone.utc),
        symbols=["RECLTD"],
        sentiment="POSITIVE",
        metadata_json={"broker": "Motilal Oswal", "target_price": 600.0, "recommendation": "BUY"},
    )
    article_3 = MarketNewsArticleCreate(
        id=f"art3-{uuid.uuid4().hex[:8]}",
        title="TCS Q2 FY25 Earnings Call Podcast",
        summary="Concall audio transcript for Tata Consultancy Services.",
        url=f"https://example.com/tcs-concall-{uuid.uuid4().hex[:6]}",
        source="Trendlyne Concalls",
        category="CONCALL",
        published_at=datetime.now(timezone.utc),
        symbols=["TCS"],
        sentiment="NEUTRAL",
        metadata_json={"quarter": "Q2 FY25", "audio_url": "https://example.com/tcs.mp3"},
    )

    crud.market_news.create_or_update(db, obj_in=article_1)
    crud.market_news.create_or_update(db, obj_in=article_2)
    crud.market_news.create_or_update(db, obj_in=article_3)

    # 1. Test GET /feed without filters
    res = client.get("/api/v1/news/feed?only_holdings=false", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 3
    assert len(data["items"]) >= 3

    # 2. Test GET /feed filtered by category=BROKER_REPORT
    res_broker = client.get("/api/v1/news/feed?category=BROKER_REPORT&only_holdings=false", headers=headers)
    assert res_broker.status_code == 200
    broker_data = res_broker.json()
    assert broker_data["total"] >= 1
    assert all(item["category"] == "BROKER_REPORT" for item in broker_data["items"])

    # 3. Test GET /feed filtered by symbol=RECLTD
    res_sym = client.get("/api/v1/news/feed?symbol=RECLTD&only_holdings=false", headers=headers)
    assert res_sym.status_code == 200
    sym_data = res_sym.json()
    assert sym_data["total"] >= 2
    for item in sym_data["items"]:
        assert "RECLTD" in item["symbols"]

    # 4. Test GET /summary
    res_summary = client.get("/api/v1/news/summary?only_holdings=false", headers=headers)
    assert res_summary.status_code == 200
    summary = res_summary.json()
    assert summary["news_count"] >= 1
    assert summary["broker_reports_count"] >= 1
    assert summary["concalls_count"] >= 1

    # 5. Test POST /refresh (mocked)
    with patch("app.api.v1.endpoints.news.news_service.sync_all_feeds", return_value=(15, 10)):
        res_refresh = client.post("/api/v1/news/refresh", headers=headers)
        assert res_refresh.status_code == 200
        ref_data = res_refresh.json()
        assert ref_data["status"] == "success"
        assert ref_data["articles_fetched"] == 15
        assert ref_data["articles_inserted"] == 10
