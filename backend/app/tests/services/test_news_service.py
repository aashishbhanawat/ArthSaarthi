
from app.services.news_service import (
    MarketNewsService,
    calculate_sentiment,
    clean_html_text,
    extract_broker_metadata,
    extract_concall_metadata,
    parse_rss_xml,
)


def test_clean_html_text():
    raw = "<p>REC Limited declared <b>₹4.50</b> dividend &amp; bonus.</p>"
    cleaned = clean_html_text(raw)
    assert cleaned == "REC Limited declared ₹4.50 dividend & bonus."


def test_calculate_sentiment():
    assert calculate_sentiment("Company posted massive profit growth and rally") == "POSITIVE"
    assert calculate_sentiment("Heavy losses, drop in revenue, and debt plunge") == "NEGATIVE"
    assert calculate_sentiment("Board meeting scheduled on Monday") == "NEUTRAL"


def test_extract_broker_metadata():
    title = "Buy REC; target of Rs 600: Motilal Oswal"
    summary = "Motilal Oswal recommends Buy on REC with target price of Rs 600 based on strong loan growth."
    meta = extract_broker_metadata(title, summary)
    assert meta["recommendation"] == "BUY"
    assert meta["target_price"] == 600.0
    assert "Motilal Oswal" in meta["broker"]

    title_accum = "Accumulate Tata Motors; target of Rs 1,150: Sharekhan"
    meta_accum = extract_broker_metadata(title_accum, "")
    assert meta_accum["recommendation"] == "ACCUMULATE"
    assert meta_accum["target_price"] == 1150.0


def test_extract_concall_metadata():
    title = "REC Limited - Q2 FY25 Earnings Call Podcast"
    meta = extract_concall_metadata(title, "Audio podcast of conference call", "https://audio.example.com/rec-q2.mp3")
    assert meta["quarter"] == "Q2 FY25"
    assert meta["audio_url"] == "https://audio.example.com/rec-q2.mp3"


def test_parse_rss_xml():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>Test Market Feed</title>
        <item>
          <title><![CDATA[Reliance Industries secures <b>huge order win</b>]]></title>
          <link>https://example.com/ril-order-win</link>
          <description>Reliance Industries today announced a major energy contract.</description>
          <pubDate>Thu, 19 Nov 2026 12:00:00 +0530</pubDate>
        </item>
        <item>
          <title>Buy TCS; target of Rs 4500: ICICI Direct</title>
          <link>https://example.com/tcs-target</link>
          <description>TCS reported stellar quarter.</description>
          <pubDate>Thu, 19 Nov 2026 10:00:00 GMT</pubDate>
        </item>
      </channel>
    </rss>
    """
    items = parse_rss_xml(xml, default_source="TestFeed", default_category="NEWS")
    assert len(items) == 2
    assert "Reliance Industries secures" in items[0]["title"]
    assert items[0]["url"] == "https://example.com/ril-order-win"
    assert items[0]["source"] == "TestFeed"
    assert items[1]["title"] == "Buy TCS; target of Rs 4500: ICICI Direct"
    assert items[0]["title"] == "Reliance Industries secures huge order win"
    assert items[0]["url"] == "https://example.com/ril-order-win"
    assert items[0]["source"] == "TestFeed"
    assert items[1]["title"] == "Buy TCS; target of Rs 4500: ICICI Direct"


def test_match_symbols():
    svc = MarketNewsService()
    active_symbols = {"RECLTD", "TCS", "INFY", "IT"}
    text = "REC Limited (RECLTD) jumps after reporting robust Q2 net profit. TCS also gains."
    matched = svc.match_symbols(text, active_symbols)
    assert "RECLTD" in matched
    assert "TCS" in matched
    assert "INFY" not in matched
    # "IT" should not match unless whole word "IT" appears
    assert "IT" not in matched
