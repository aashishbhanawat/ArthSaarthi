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


def test_purge_noise_and_disambiguate_db(db: Session) -> None:
    # 1. Insert a noise article (e.g. the exact user-reported SCI exam spam)
    noise_article = MarketNewsArticleCreate(
        id=f"noise-{uuid.uuid4().hex[:8]}",
        title="SCI JCA answer key 2026 released at sci.gov.in: Supreme Court Junior Court Assistant provisional answer k",
        summary="Supreme Court has released the junior court assistant answer key.",
        url=f"https://example.com/sci-exam-{uuid.uuid4().hex[:6]}",
        source="The Times of India",
        category="NEWS",
        published_at=datetime.now(timezone.utc),
        symbols=["SCI"],
        sentiment="NEUTRAL",
    )
    crud.market_news.create_or_update(db, obj_in=noise_article)

    # 2. Insert a valid article that had a falsely tagged SCI ticker among valid ones
    mixed_article = MarketNewsArticleCreate(
        id=f"mixed-{uuid.uuid4().hex[:8]}",
        title="Supreme Court bench directs auto firms on EV guidelines; Tata Motors shares rise",
        summary="Supreme Court issued guidelines. Tata Motors shares gained 2% on NSE.",
        url=f"https://example.com/sc-tata-{uuid.uuid4().hex[:6]}",
        source="Economic Times",
        category="NEWS",
        published_at=datetime.now(timezone.utc),
        symbols=["SCI", "TATAMOTORS"],
        sentiment="POSITIVE",
    )
    crud.market_news.create_or_update(db, obj_in=mixed_article)

    # Execute purge
    deleted, updated = crud.market_news.purge_noise_and_disambiguate(db)
    assert deleted >= 1

    # Check noise article is gone
    purged = crud.market_news.get(db, noise_article.id)
    assert purged is None

    # Check mixed article had SCI stripped, retaining TATAMOTORS
    retained = crud.market_news.get(db, mixed_article.id)
    assert retained is not None
    assert "SCI" not in retained.symbols
    assert "TATAMOTORS" in retained.symbols


def test_analyze_concall_api(client, db):
    user, password = create_random_user(db)
    token = get_access_token(client, user.email, password)
    headers = {"Authorization": f"Bearer {token}"}

    concall_id = f"test-concall-{uuid.uuid4().hex[:8]}"
    article = MarketNewsArticleCreate(
        id=concall_id,
        title="Exide Industries Results Earnings Call for Q2FY27",
        summary="Conference call discussing Q2 results, margin outlook, and capex.",
        url=f"https://example.com/exide-call-{concall_id}",
        source="Trendlyne Concalls",
        category="CONCALL",
        published_at=datetime.now(timezone.utc),
        symbols=["EXIDEIND"],
        sentiment="NEUTRAL",
        metadata_json={
            "quarter": "Q2FY27",
            "audio_url": "https://example.com/exide.mp3",
        },
    )
    crud.market_news.create_or_update(db, obj_in=article)

    # 1. Analyze with custom transcript text
    custom_text = (
        "Opening Remarks: We are pleased to report strong performance for Q2. "
        "Revenue grew 16% YoY with EBITDA margins at 12.5%. "
        "Planned capex for the lithium gigafactory is ₹1,200 crore. "
        "Question-and-Answer Session: "
        "Analyst: What is your outlook on margins? "
        "Management: We maintain positive outlook on margins."
    )
    res = client.post(
        f"/api/v1/news/{concall_id}/analyze-concall",
        headers=headers,
        json={"transcript_text": custom_text},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["article_id"] == concall_id
    assert "management_tone" in data
    assert "qa_tone" in data
    assert "guidance_metrics" in data
    assert len(data["guidance_metrics"]) > 0
    assert any(g["category"] == "Capex" for g in data["guidance_metrics"])
    assert data["transcription_source"] == "USER_INPUT"

    # 2. Subsequent call without payload should return cached analysis
    res_cached = client.post(
        f"/api/v1/news/{concall_id}/analyze-concall",
        headers=headers,
        json={},
    )
    assert res_cached.status_code == 200
    assert res_cached.json()["article_id"] == concall_id


def test_analyze_concall_audio_only_without_transcript_returns_400(client, db):
    user, password = create_random_user(db)
    token = get_access_token(client, user.email, password)
    headers = {"Authorization": f"Bearer {token}"}

    audio_only_id = f"audio-only-{uuid.uuid4().hex[:8]}"
    article = MarketNewsArticleCreate(
        id=audio_only_id,
        title="Rail Vikas Nigam Results Earnings Call for Q2FY27",
        summary="Audio podcast of Q2 concall.",
        url=f"https://example.com/rvnl-call-{audio_only_id}",
        source="Trendlyne Concalls",
        category="CONCALL",
        published_at=datetime.now(timezone.utc),
        symbols=["RVNL"],
        sentiment="NEUTRAL",
        metadata_json={
            "quarter": "Q2FY27",
            "audio_url": "https://example.com/rvnl.mp3",
        },
    )
    crud.market_news.create_or_update(db, obj_in=article)

    # Calling analyze-concall with no transcript and whisper unavailable should return 400
    with patch("app.api.v1.endpoints.news.whisper_engine.is_available", False):
        res = client.post(
            f"/api/v1/news/{audio_only_id}/analyze-concall",
            headers=headers,
            json={},
        )
        assert res.status_code == 400
        assert "Only audio podcast is available" in res.json()["detail"]

    # Calling analyze-concall when whisper is available transcribes audio and returns 200
    with patch("app.api.v1.endpoints.news.whisper_engine.is_available", True):
        with patch(
            "app.api.v1.endpoints.news.whisper_engine.transcribe_audio_file",
            return_value="Management delivered strong results with robust revenue and guidance.",
        ):
            res_transcribe = client.post(
                f"/api/v1/news/{audio_only_id}/analyze-concall",
                headers=headers,
                json={},
            )
            assert res_transcribe.status_code == 200
            data = res_transcribe.json()
            assert data["transcription_source"] == "WHISPER_AUDIO"
            assert data["management_tone"]["overall"] in ["BULLISH", "BALANCED", "NEUTRAL", "BEARISH"]


def test_purge_removes_fake_whisper_analysis(db: Session) -> None:
    fake_whisper_id = f"fake-whisper-{uuid.uuid4().hex[:8]}"
    article = MarketNewsArticleCreate(
        id=fake_whisper_id,
        title="GHCL Ltd. Results Earnings Call for Q2FY27",
        summary="Conference call.",
        url=f"https://example.com/ghcl-{fake_whisper_id}",
        source="Trendlyne Concalls",
        category="CONCALL",
        published_at=datetime.now(timezone.utc),
        symbols=["GHCL"],
        sentiment="NEUTRAL",
        metadata_json={
            "quarter": "Q2FY27",
            "audio_url": "https://example.com/ghcl.mp3",
            "transcript_text": "Management opening remarks: We are pleased to report...",
            "concall_analysis": {
                "transcription_source": "WHISPER_AUDIO",
                "management_tone": {"overall": "NEUTRAL"},
            },
        },
    )
    crud.market_news.create_or_update(db, obj_in=article)

    # Execute purge
    deleted, updated = crud.market_news.purge_noise_and_disambiguate(db)
    assert updated >= 1

    cleaned = crud.market_news.get(db, fake_whisper_id)
    assert cleaned is not None
    meta = cleaned.metadata_json or {}
    assert "concall_analysis" not in meta
    assert "transcript_text" not in meta


