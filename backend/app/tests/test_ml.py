from app.ml.deduplicator import HeadlineDeduplicator
from app.ml.entity_matcher import FastEntityMatcher
from app.ml.model_manager import ModelManager
from app.ml.sentiment_engine import FinancialLexicon, SentimentEngine


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
    assert result.engine in ["financial_lexicon", "finbert_onnx"]


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

    # Long ticker symbols pass cleanly
    assert relevance_filter.validate_ticker("RELIANCE", "Reliance expands retail presence across tier 2 cities")

