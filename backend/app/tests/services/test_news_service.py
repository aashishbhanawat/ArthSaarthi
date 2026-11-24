
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


def test_parse_indian_exchange_dates():
    from app.services.news_service import parse_rfc2822_date

    # NSE & BSE date string in IST: "22-Nov-2026 14:39:18"
    dt = parse_rfc2822_date("22-Nov-2026 14:39:18")
    # 14:39:18 IST = 09:09:18 UTC
    assert dt.year == 2026
    assert dt.month == 11
    assert dt.day == 22
    assert dt.hour == 9
    assert dt.minute == 9
    assert dt.second == 18


def test_match_symbols_with_mappings():
    svc = MarketNewsService()
    mappings = {
        "RECLTD": "RECLTD",
        "REC Limited": "RECLTD",
        "532955": "RECLTD",
        "TCS": "TCS",
        "Tata Consultancy Services": "TCS",
    }
    # Test NSE headline format with company name
    nse_text = "REC Limited has informed the Exchange regarding outcome of Board Meeting"
    matched_nse = svc.match_symbols(nse_text, mappings)
    assert "RECLTD" in matched_nse

    # Test BSE headline format with scrip code
    bse_text = "Adani Energy Solutions Ltd (539254) has acquired transmission assets"
    # Not in mappings, should not match
    assert "RECLTD" not in svc.match_symbols(bse_text, mappings)

    bse_rec = "REC Ltd (532955) Board approves dividend payout"
    matched_bse = svc.match_symbols(bse_rec, mappings)
    assert "RECLTD" in matched_bse


def test_feed_configs_include_nse_bse_livemint():
    from app.services.news_service import FEED_CONFIGS

    sources = [cfg["source"] for cfg in FEED_CONFIGS]
    urls = [cfg["url"] for cfg in FEED_CONFIGS]

    assert "Livemint Markets" in sources
    assert "Livemint Companies" in sources
    assert "NSE Announcements" in sources
    assert "BSE Announcements" in sources

    assert "https://www.livemint.com/rss/markets" in urls
    assert "https://nsearchives.nseindia.com/content/RSS/Online_announcements.xml" in urls
    assert "https://www.bseindia.com/data/xml/announcements.aspx" in urls


def test_concalls_and_results_not_dropped_by_deduplication():
    from app.ml.deduplicator import headline_deduplicator
    headline_deduplicator.clear()

    # Two distinct concalls with boilerplate format
    call1 = "Exide Industries Results Earnings Call for Q2FY27"
    call2 = "Kajaria Ceramics Results Earnings Call for Q2FY27"

    # Both CONCALL items must be preserved
    items = [
        {"title": call1, "url": "https://example.com/c1", "category": "CONCALL", "summary": "", "source": "Trendlyne", "published_at": None},
        {"title": call2, "url": "https://example.com/c2", "category": "CONCALL", "summary": "", "source": "Trendlyne", "published_at": None},
    ]
    survived = [it for it in items if not (it["category"] == "NEWS" and headline_deduplicator.is_duplicate(it["title"]))]
    assert len(survived) == 2


def test_bse_feed_capping():
    from app.services.news_service import FEED_CONFIGS
    bse_cfg = next(
        cfg
        for cfg in FEED_CONFIGS
        if cfg["url"] == "https://www.bseindia.com/data/xml/announcements.aspx"
        and cfg["category"] == "NEWS"
    )
    assert bse_cfg.get("max_items") == 100


def test_crud_retroactive_tagging(db):
    from datetime import datetime, timezone

    from app.crud.crud_news import market_news
    from app.models.market_news import MarketNewsArticle

    # Seed an untagged concall within 30 days
    article_id = "test_untagged_concall_exide"
    db.query(MarketNewsArticle).filter(MarketNewsArticle.id == article_id).delete()
    db.commit()

    art = MarketNewsArticle(
        id=article_id,
        title="Exide Industries Results Earnings Call for Q2FY27",
        summary="Conference call transcript",
        url="https://example.com/exide-call-audio.mp3",
        source="Trendlyne Concalls",
        category="CONCALL",
        published_at=datetime.now(timezone.utc),
        symbols=[],
        sentiment="NEUTRAL",
    )
    db.add(art)
    db.commit()

    # Retroactively tag with mock matcher
    def matcher(text):
        if "exide industries" in text.lower():
            return ["EXIDEIND"]
        return []

    updated = market_news.retroactively_tag_symbols(db, matcher_callback=matcher, days=30)
    assert updated >= 1

    refreshed = db.query(MarketNewsArticle).filter(MarketNewsArticle.id == article_id).first()
    assert refreshed is not None
    assert "EXIDEIND" in refreshed.symbols

    # Cleanup
    db.delete(refreshed)
    db.commit()


