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
