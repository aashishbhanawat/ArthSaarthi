from unittest.mock import patch

from app.ml.concall_analyzer import concall_analyzer
from app.ml.whisper_engine import whisper_engine

SAMPLE_CONCALL_TRANSCRIPT = """
Operator: Ladies and gentlemen, welcome to the Q2 FY27 Earnings Conference Call of Exide Industries Limited.
I now hand over the conference to the management for their opening remarks.

Management: Good afternoon, everyone, and thank you for joining us today.
We are pleased to report strong performance for the second quarter of financial year 2027.
Revenue for the quarter grew 16.5% year-on-year driven by robust demand across automotive OEM and industrial markets.
EBITDA margins improved by 140 bps to 12.8% despite lingering raw material price pressures.
Our capital expenditure for the Phase 1 lithium-ion cell gigafactory is on track at ₹1,200 crore and commercial production is expected in Q4.
We are maintaining our guidance of 15% to 18% revenue growth for the full financial year.
Our net debt reduced by ₹250 crore during the quarter as operating cash flows improved significantly.

Question-and-Answer Session:
Operator: The floor is now open for questions. Our first question comes from the line of Rohan from Motilal Oswal.
Analyst: Congratulations on the margin expansion. What is your outlook on raw material costs and lead price volatility in the coming quarters?
Management: Thank you, Rohan. Lead prices have stabilized in the last two months and we have backward integration that cushions margin fluctuations.
Analyst: Can you give more color on the capacity utilization of the new lithium plant?
Management: We expect initial capacity utilization of 60% ramping up to 85% by end of FY28.
"""


def test_concall_analyzer_segmentation():
    mgmt, qa = concall_analyzer.segment_transcript(SAMPLE_CONCALL_TRANSCRIPT)
    assert len(mgmt) > 0
    assert len(qa) > 0
    assert any("EBITDA margins" in s for s in mgmt)
    assert any("capacity utilization" in s for s in qa)


def test_concall_guidance_mining():
    guidance = concall_analyzer.mine_guidance_metrics(SAMPLE_CONCALL_TRANSCRIPT)
    categories = [g["category"] for g in guidance]

    assert "Capex" in categories
    assert "Margin Outlook" in categories
    assert "Guidance & Growth" in categories

    capex_item = next(g for g in guidance if g["category"] == "Capex")
    assert "1,200" in capex_item["text"] or "1200" in capex_item["text"]


def test_concall_extractive_summarization():
    takeaways = concall_analyzer.extract_top_sentences(SAMPLE_CONCALL_TRANSCRIPT, n=3)
    assert len(takeaways) <= 3
    # Boilerplate lines should be excluded
    assert not any("Operator:" in t for t in takeaways)
    assert not any("Ladies and gentlemen" in t for t in takeaways)


def test_concall_topic_extraction():
    topics = concall_analyzer.extract_topics(SAMPLE_CONCALL_TRANSCRIPT, n=5)
    assert len(topics) > 0
    assert isinstance(topics, list)


def test_concall_tone_analysis():
    mgmt, qa = concall_analyzer.segment_transcript(SAMPLE_CONCALL_TRANSCRIPT)
    mgmt_tone = concall_analyzer.analyze_tone(mgmt)
    assert "positive_pct" in mgmt_tone
    assert "neutral_pct" in mgmt_tone
    assert "negative_pct" in mgmt_tone
    assert mgmt_tone["overall"] in ["BULLISH", "BEARISH", "NEUTRAL", "BALANCED"]


def test_concall_analyzer_end_to_end():
    result = concall_analyzer.analyze(SAMPLE_CONCALL_TRANSCRIPT)
    assert "management_tone" in result
    assert "qa_tone" in result
    assert "guidance_metrics" in result
    assert "top_takeaways" in result
    assert "key_themes" in result
    assert len(result["guidance_metrics"]) > 0
    assert len(result["top_takeaways"]) > 0


def test_whisper_engine_status():
    status = whisper_engine.get_status()
    assert status["model_id"] == "whisper_tiny_en"
    assert "status" in status
    assert "is_available" in status


def test_whisper_transcription_when_available():
    with patch("app.ml.model_manager.model_manager.is_model_available", return_value=True):
        with patch.object(whisper_engine, "_transcribe_with_model", return_value="Transcribed text"):
            with patch("app.ml.model_manager.model_manager.get_model_path") as mock_path:
                mock_path.return_value.exists.return_value = True
                res = whisper_engine.transcribe_audio_file("dummy.m4a")
                assert res == "Transcribed text"
