import uuid
from unittest.mock import patch

from app.core.config import settings
from app.core.dependencies import get_current_active_user
from app.main import app
from app.ml.deduplicator import HeadlineDeduplicator
from app.ml.entity_matcher import FastEntityMatcher
from app.ml.model_manager import EdgeModelInfo, ModelManager
from app.ml.sentiment_engine import FinancialLexicon, SentimentEngine
from app.models.user import User


def test_fast_entity_matcher():
    matcher = FastEntityMatcher(case_sensitive=False)
    matcher.add_keyword("RELIANCE", clean_name="RELIANCE")
    matcher.add_keyword("TATA MOTORS", clean_name="TATAMOTORS")
    matcher.add_keyword("TATAMOTORS", clean_name="TATAMOTORS")
    matcher.add_keyword("IT", clean_name="IT")

    # Match exact and aliases
    text = "Tata Motors reports strong Q3 results, while Reliance Industries partners with IT firm."
    matches = matcher.extract_keywords(text)
    assert "TATAMOTORS" in matches
    assert "RELIANCE" in matches
    assert "IT" in matches

    # Test word boundary protection (e.g. 'IT' in 'with' or 'wait' should not match)
    text_with = "Company had a wait and with strategy."
    matches_none = matcher.extract_keywords(text_with)
    assert "IT" not in matches_none


def test_headline_deduplicator():
    dedup = HeadlineDeduplicator(history_size=100)
    h1 = "Reliance Industries Q3 net profit rises 12% to Rs 18,500 crore"
    h2 = "Reliance Industries Q3 net profit up 12% to Rs 18,500 crore"
    h3 = "Tata Steel signs memorandum of understanding with UK government"

    assert not dedup.is_duplicate(h1)
    # h2 is near identical to h1
    assert dedup.is_duplicate(h2, threshold=0.50)
    # h3 is a completely different headline
    assert not dedup.is_duplicate(h3)


def test_financial_lexicon_sentiment():
    lexicon = FinancialLexicon()

    res_pos = lexicon.analyze("Company net profit surges 45% YoY with record dividend payout")
    assert res_pos.label == "POSITIVE"
    assert res_pos.score > 0.5
    assert res_pos.engine == "financial_lexicon"

    res_neg = lexicon.analyze("Tech firm posts heavy loss as revenue slumps, shares plunge")
    assert res_neg.label == "NEGATIVE"
    assert res_neg.score > 0.5

    # Negation testing: "no loss" or "not declining"
    res_negated = lexicon.analyze("Management reports no loss and expects business turnaround")
    assert res_negated.label == "POSITIVE"


def test_sentiment_engine_fallback():
    engine = SentimentEngine()
    result = engine.analyze("HDFC Bank beats market estimates with robust loan growth")
    assert result.label == "POSITIVE"
    assert result.engine in ["financial_lexicon", "finbert_onnx", "deterministic_rule"]
    assert hasattr(result, "tone_score")


def test_sentiment_engine_hybrid_rules_and_uncertainty():
    engine = SentimentEngine()

    # Layer 1: Broker recommendations and hard corporate catalysts
    res_buy = engine.analyze("Motilal Oswal recommends Buy on REC with target price of Rs 600")
    assert res_buy.label == "POSITIVE"
    assert res_buy.engine == "deterministic_rule"
    assert res_buy.tone_score > 0.5

    res_fraud = engine.analyze("SEBI penalty imposed and promoter arrested in accounting fraud")
    assert res_fraud.label == "NEGATIVE"
    assert res_fraud.engine == "deterministic_rule"
    assert res_fraud.tone_score < -0.5

    # Price action movements
    res_fall = engine.analyze("Exide Industries Share Price Fall: Price Action and Analysis - Univest")
    assert res_fall.label == "NEGATIVE"
    assert res_fall.engine == "deterministic_rule"
    assert res_fall.tone_score < -0.5

    res_surge = engine.analyze("Tata Power shares surge 8% to new 52-week high on massive solar contract")
    assert res_surge.label == "POSITIVE"
    assert res_surge.engine == "deterministic_rule"
    assert res_surge.tone_score > 0.5

    # Uncertainty calculation
    rate = engine.lexicon.compute_uncertainty_rate(
        "Company faces significant headwinds and commodity volatility with cautious outlook"
    )
    assert rate > 0.0


def test_model_manager_status(tmp_path):
    mgr = ModelManager(models_dir=tmp_path)
    models = mgr.list_models()
    assert len(models) >= 1
    finbert = models[0]
    assert finbert.id == "finbert_int8"
    assert finbert.status == "NOT_DOWNLOADED"
    assert not mgr.is_model_available("finbert_int8")

    # Simulate downloaded file
    fake_model = tmp_path / "finbert_int8.onnx"
    fake_model.write_bytes(b"dummy onnx weights" * 100)
    status = mgr.get_model_status("finbert_int8")
    assert status.status == "ACTIVE"
    assert mgr.is_model_available("finbert_int8")

    # Test delete
    deleted = mgr.delete_model("finbert_int8")
    assert deleted
    assert not mgr.is_model_available("finbert_int8")


def test_relevance_filter_noise_detection():
    from app.ml.relevance_filter import relevance_filter

    # The exact noise article reported by the user
    user_noise = (
        "SCI JCA answer key 2026 released at sci.gov.in: "
        "Supreme Court Junior Court Assistant provisional answer k - The Times of India"
    )
    assert relevance_filter.is_noise(user_noise)
    assert not relevance_filter.is_financial_relevant(user_noise)

    # Other exam/recruitment spam
    assert relevance_filter.is_noise("SSC CGL Tier 1 Admit Card 2026 released, download hall ticket now")
    assert relevance_filter.is_noise("Civil judge recruitment preliminary exam result declared on highcourt.gov.in")
    assert not relevance_filter.is_financial_relevant("UPSC Civil Services vacancy 2026 apply online")

    # General noise (crime, sports, entertainment)
    assert relevance_filter.is_noise("Celebrity dating rumors spark controversy at Bollywood box office")
    assert relevance_filter.is_noise("India vs Australia 3rd test match live cricket score and highlights")
    assert not relevance_filter.is_financial_relevant("Horoscope today: Astrological predictions for all zodiac signs")

    # Automated stock price tracker and SEO quote landing pages (User reported)
    assert relevance_filter.is_noise("Share Price Today - HGS (India) Ltd. Stock Price Live NSE/BSE - HDFC Sky")
    assert relevance_filter.is_noise("Lahoti Overseas Limited (LAHOTIOV.NS) stock price, news, quote and history - Yahoo Finance Australia")
    assert relevance_filter.is_noise("Lahoti Overseas Limited (LAHOTIOV.NS) stock major holders - Yahoo Finance Singapore")
    assert relevance_filter.is_noise("ABAN OFFSHORE LTD. Share Price - Live NSE: ABAN Stock Price & Chart - Upstox")
    assert relevance_filter.is_noise("Coal India Share Price Highlights: Coal India Ltd Stock Price History")
    assert relevance_filter.is_noise("RVNL Share Price - Upstox")
    assert relevance_filter.is_noise("RVNL Share Price Today - Rail Vikas Nigam on NSE/BSE - scanx.trade")
    assert relevance_filter.is_noise("HGS India Ltd Share Price Today NSE/BSE Charts - Alice Blue")
    assert relevance_filter.is_noise("HGS (India) (NSEI:HGSINDIALT) - Stock Analysis - Simply Wall St")


def test_relevance_filter_financial_positive():
    from app.ml.relevance_filter import relevance_filter

    valid_1 = "Tata Motors reports 45% surge in Q3 consolidated profit, declares special dividend"
    assert not relevance_filter.is_noise(valid_1)
    assert relevance_filter.is_financial_relevant(valid_1)

    valid_2 = "Shipping Corp of India (SCI) Q3 profit jumps 30% YoY with strong fleet charter rates"
    assert not relevance_filter.is_noise(valid_2)
    assert relevance_filter.is_financial_relevant(valid_2)

    valid_3 = "Motilal Oswal maintains buy on RECLTD with target of Rs 600 as loan book expands"
    assert not relevance_filter.is_noise(valid_3)
    assert relevance_filter.is_financial_relevant(valid_3)


def test_ticker_disambiguation():
    from app.ml.relevance_filter import relevance_filter

    # SCI: Reject Supreme Court and exam noise
    sci_noise = (
        "SCI JCA answer key 2026 released at sci.gov.in: "
        "Supreme Court Junior Court Assistant provisional answer k - The Times of India"
    )
    assert not relevance_filter.validate_ticker("SCI", sci_noise)

    sci_court = "Supreme Court of India (SCI) bench issues notice to government on Delhi air quality"
    assert not relevance_filter.validate_ticker("SCI", sci_court)

    # SCI: Accept genuine Shipping Corporation of India news
    sci_valid_1 = "Shipping Corporation of India (SCI) approves interim dividend of Rs 5 per share"
    assert relevance_filter.validate_ticker("SCI", sci_valid_1)

    sci_valid_2 = "SCI Q3 net profit rises 15%, fleet expansion capex on track"
    assert relevance_filter.validate_ticker("SCI", sci_valid_2)

    # IT: Reject Income Tax / Info Tech phrases without stock markers
    assert not relevance_filter.validate_ticker("IT", "Government extends deadline for Income Tax return filing")
    assert relevance_filter.validate_ticker("IT", "Top IT sector stocks rally on NSE as margins expand")

    # IDEA: Reject general idiom
    assert not relevance_filter.validate_ticker("IDEA", "Here is a good idea to spend your weekend")
    assert relevance_filter.validate_ticker("IDEA", "Vodafone Idea (IDEA) shares jump as telecom ARPU improves")

    # CARE: Reject healthcare idiom
    assert not relevance_filter.validate_ticker("CARE", "Essential tips on child care and infant nutrition")
    assert relevance_filter.validate_ticker("CARE", "CARE Ratings upgrades long-term debt rating of Tata Power")

    # HGS: Reject unrelated SME cable IPO (HGS India / HGSINDIALT on NSE Emerge)
    assert not relevance_filter.validate_ticker("HGS", "HGS India shares debut at 34% premium on NSE Emerge - Moneycontrol")
    assert not relevance_filter.validate_ticker("HGS", "HGS (India) Shares List At ₹160 On NSE SME, Rise To ₹168")
    assert relevance_filter.validate_ticker("HGS", "Hinduja Global Solutions (HGS) Q2 net profit jumps 22% on BPM contract wins")

    # GICRE: Reject ICICI Lombard / other general insurers
    assert not relevance_filter.validate_ticker(
        "GICRE",
        "ICICI Lombard General Insurance Company Limited has informed the Exchange about Analyst Meet",
    )
    assert not relevance_filter.validate_ticker(
        "GICRE",
        "Bajaj Allianz General Insurance reports monthly gross premium collections",
    )
    assert relevance_filter.validate_ticker(
        "GICRE",
        "General Insurance Corporation of India (GIC Re) approves interim dividend of Rs 4 per share",
    )

    # VEDL: Reject distinct unlisted Vedanta Oil and Gas
    assert not relevance_filter.validate_ticker("VEDL", "Why Vedanta Oil and Gas Share Price is Rising - Equitymaster")
    assert relevance_filter.validate_ticker("VEDL", "Vedanta Limited announces interim dividend of Rs 20 per share")

    # Long ticker symbols pass cleanly
    assert relevance_filter.validate_ticker("RELIANCE", "Reliance expands retail presence across tier 2 cities")


def test_ml_api_authorization(client):
    normal_user = User(
        id=uuid.uuid4(),
        email="normal@example.com",
        is_admin=False,
        is_active=True,
    )
    admin_user = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        is_admin=True,
        is_active=True,
    )

    app.dependency_overrides[get_current_active_user] = lambda: normal_user
    try:
        # Test GET /models (accessible to normal users)
        res_list = client.get("/api/v1/ml/models")
        assert res_list.status_code == 200
        assert isinstance(res_list.json(), list)

        # Test POST /sentiment/test (accessible to normal users)
        res_test = client.post(
            "/api/v1/ml/sentiment/test",
            json={"text": "Tata Motors Q3 profit up 45%"},
        )
        assert res_test.status_code == 200
        assert "label" in res_test.json()

        # In server mode: Normal user should get 403 on download and delete
        with patch.object(settings, "DEPLOYMENT_MODE", "server"):
            res_down_fail = client.post(
                "/api/v1/ml/models/finbert_int8/download",
            )
            assert res_down_fail.status_code == 403
            assert "restricted to administrators" in res_down_fail.json()["detail"]

            res_del_fail = client.delete(
                "/api/v1/ml/models/finbert_int8",
            )
            assert res_del_fail.status_code == 403
            assert "restricted to administrators" in res_del_fail.json()["detail"]

        # Admin user should succeed (mock start_download to avoid real network call)
        app.dependency_overrides[get_current_active_user] = lambda: admin_user
        with patch.object(settings, "DEPLOYMENT_MODE", "server"):
            with patch("app.api.v1.endpoints.ml.model_manager.start_download") as mock_start:
                mock_start.return_value = EdgeModelInfo(
                    id="finbert_int8",
                    name="FinBERT INT8 Quantized",
                    description="desc",
                    size_mb=105.2,
                    download_url="https://example.com",
                    filename="finbert_int8.onnx",
                    engine_type="finbert_onnx",
                    status="DOWNLOADING",
                    progress_percentage=0,
                    downloaded_bytes=0,
                    total_bytes=1000,
                )
                res_down_admin = client.post(
                    "/api/v1/ml/models/finbert_int8/download",
                )
                assert res_down_admin.status_code == 200

            with patch("app.api.v1.endpoints.ml.model_manager.delete_model", return_value=True):
                res_del_admin = client.delete(
                    "/api/v1/ml/models/finbert_int8",
                )
                assert res_del_admin.status_code == 200
                assert res_del_admin.json()["deleted"] is True
    finally:
        app.dependency_overrides.pop(get_current_active_user, None)

