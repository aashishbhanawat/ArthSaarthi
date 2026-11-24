from unittest.mock import patch

import pytest

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


def test_concall_filtering_and_concrete_takeaways():
    noisy_transcript = """
    Exide Industries Limited
    May 2024 Page 1 of 18
    Operator: Ladies and gentlemen, welcome to Exide Industries Limited conference call.
    Avik Roy: So let me take the first one.
    So I would say, if you look at complete mobility, complete mobility full year, they contribute to about, let's say, one-third of our business, 35% of our business has almost grown by 15%, both put together, 4-wheeler and 2- wheeler.
    What will be the range of utilization at which the business will be breakeven for the lithium-ion cell?
    We will be the first one.
    Now the business is like this, the 2-wheeler and 3-wheeler will be a pack business.
    Our target is to ramp up slowly over the couple of years to a minimum 80% utilization and a running factory.
    Our capital expenditure for the gigawatt hour lithium cell plant is INR 3,602 crores.
    """
    takeaways = concall_analyzer.extract_top_sentences(noisy_transcript, n=3)
    assert len(takeaways) > 0

    # Speaker prefix should be stripped
    assert not any(t.startswith("Avik Roy:") for t in takeaways)
    # Analyst questions should be excluded
    assert not any("?" in t for t in takeaways)
    assert not any(t.startswith("What will be") for t in takeaways)
    # Conversational filler should be excluded
    assert not any("So let me take the first one" in t for t in takeaways)
    assert not any(t == "We will be the first one." for t in takeaways)

    # Concrete statement containing 35% or 3,602 crores or 80% utilization should be captured
    assert any("35%" in t or "3,602" in t or "80%" in t for t in takeaways)

    # Topics should exclude PDF headers/footers, date artifacts, and speaker names
    topics = concall_analyzer.extract_topics(noisy_transcript, n=5)
    for topic in topics:
        assert "Avik" not in topic
        assert "Roy" not in topic
        assert "Page" not in topic
        assert "May" not in topic
        assert "Limited" not in topic


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
    assert "tone_gap_alert" in result
    assert "tone_divergence_summary" in result
    assert "hedge_rate_per_100w" in result
    assert "topic_sentiment" in result
    assert "red_flags" in result
    assert len(result["guidance_metrics"]) > 0
    assert len(result["top_takeaways"]) > 0
    assert isinstance(result["topic_sentiment"], dict)


def test_concall_aspect_scoring_and_tone_gap():
    sample = """
    Management: Revenue for the full year grew 18% with strong order book volume and sales pipeline.
    Our EBITDA margins expanded 140 bps despite raw material cost inflation.
    Capex for the gigafactory is on track at ₹1,200 crore and working capital debt was reduced.
    We are guiding for 15% revenue growth next quarter.
    
    Question-and-Answer Session:
    Analyst: Are you seeing any demand headwinds or margin pressure in aftermarket?
    Management: We see lingering commodity volatility and cautious customer sentiment creating near-term pressure.
    """
    res = concall_analyzer.analyze(sample)
    assert "demand_revenue" in res["topic_sentiment"]
    assert "margins_costs" in res["topic_sentiment"]
    assert res["hedge_rate_per_100w"] > 0
    assert res["tone_gap_alert"] is not None
    assert len(res["red_flags"]) > 0


def test_concall_deduplicate_overlapping_takeaways():
    transcript = """
    Management: We are pleased to report strong performance for Q2.
    Aditya Jhawar: And on the lithium-ion side, could you tell us what sort of pack capacity we have.
    Management: That is the time when we will start getting a view on returns because once we reach 80% of utilization, we need to put up more capacity.
    Kapil Singh: Any color on capacity?
    Management: I think once we reach 80% of the utilization, which is around 4 gigawatt, 5 gigawatt, we should see how our manufacturing cost performs.
    Management: Our new punched grid technology in the 2-wheeler segment has achieved 15% export growth across European markets.
    """
    takeaways = concall_analyzer.extract_top_sentences(transcript, n=5)

    # 1. Interrogative without ? ("could you tell us...") must be excluded
    assert not any("could you tell us" in t.lower() for t in takeaways)

    # 2. Overlapping 80% utilization sentences must be deduplicated to only 1 entry
    utilization_80_count = sum(1 for t in takeaways if "80%" in t and "utilization" in t.lower())
    assert utilization_80_count == 1

    # 3. Punched grid statement should be included as distinct takeaway
    assert any("punched grid" in t.lower() for t in takeaways)


def test_concall_hedging_lexicon_expansion():
    text = "The business environment was volatile, with sudden headwinds, risky pricing, and weaker auto OEM demand."
    rate = concall_analyzer.compute_hedging_rate(text)
    # volatile, headwinds, risky, weaker = 4 uncertainty words out of 15 words (~26%)
    assert rate > 10.0


def test_concall_high_signal_and_theme_stop_phrases():
    # 1. High signal density guard
    filler = "So whenever we are weak, we are trying to come back."
    assert not concall_analyzer.is_high_signal_sentence(filler)

    short_pack = "The 2-wheeler and 3-wheeler will be a pack business."
    assert not concall_analyzer.is_high_signal_sentence(short_pack)

    substantive = "Operating profitability was impacted due to high input costs in the quarter on account of a considerable increase in the cost of antimony."
    assert concall_analyzer.is_high_signal_sentence(substantive)

    # 2. Tone Gap Calibration (>= 0.10 threshold)
    gap, summary = concall_analyzer.calculate_tone_gap(0.08, -0.03)
    assert gap == 0.11
    assert "Tone Gap Alert (+0.11)" in summary
    assert "Management tone softened during Q&A" in summary

    # 3. Discussion theme stop phrases
    transcript_with_adjectives = """
    Management: We expect double digit volume growth and double digit margin expansion next year and full year.
    Our primary business focus remains on lithium ion battery chemistry and punched grid design.
    """
    topics = concall_analyzer.extract_topics(transcript_with_adjectives, n=5)
    for topic in topics:
        assert "Double Digit" not in topic
        assert "Full Year" not in topic
        assert "Next Year" not in topic


def test_whisper_engine_status():
    status = whisper_engine.get_status()
    assert status["model_id"] == "whisper_tiny_en"
    assert "status" in status
    assert "is_available" in status


def test_whisper_engine_unavailable_without_ffmpeg():
    with patch("shutil.which", return_value=None):
        assert whisper_engine.is_available is False


def test_whisper_transcription_raises_error_without_runtime(tmp_path):
    dummy_audio = tmp_path / "dummy.m4a"
    dummy_audio.write_bytes(b"dummy")
    with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
        with patch("app.ml.model_manager.model_manager.is_model_available", return_value=True):
            with patch("app.ml.model_manager.model_manager.get_model_path") as mock_path:
                mock_path.return_value.exists.return_value = True
                with pytest.raises(RuntimeError, match="Audio transcription requires ffmpeg"):
                    whisper_engine.transcribe_audio_file(dummy_audio)


def test_whisper_transcription_when_available(tmp_path):
    dummy_audio = tmp_path / "dummy.m4a"
    dummy_audio.write_bytes(b"fake audio bytes")
    with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
        with patch("app.ml.model_manager.model_manager.is_model_available", return_value=True):
            with patch.object(whisper_engine, "_transcribe_with_model", return_value="Transcribed text"):
                with patch("app.ml.model_manager.model_manager.get_model_path") as mock_path:
                    mock_path.return_value.exists.return_value = True
                    res = whisper_engine.transcribe_audio_file(dummy_audio)
                    assert res == "Transcribed text"


def test_whisper_transcription_remote_url():
    with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
        with patch("app.ml.model_manager.model_manager.is_model_available", return_value=True):
            with patch.object(whisper_engine, "_transcribe_with_model", return_value="Transcribed text"):
                with patch("app.ml.model_manager.model_manager.get_model_path") as mock_path:
                    mock_path.return_value.exists.return_value = True
                    with patch("requests.get") as mock_get:
                        mock_get.return_value.__enter__.return_value.iter_content.return_value = [b"fake audio stream"]
                        mock_get.return_value.__enter__.return_value.raise_for_status = lambda: None
                        res = whisper_engine.transcribe_audio_file("https://example.com/concall.m4a")
                        assert res == "Transcribed text"
