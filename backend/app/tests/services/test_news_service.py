
from unittest.mock import patch

from app.services.news_service import (
    MarketNewsService,
    calculate_sentiment,
    clean_html_text,
    extract_broker_metadata,
    extract_concall_metadata,
    extract_corporate_metadata,
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


def test_exchange_filings_exempt_from_noise_and_detect_concall(db):
    from app.models.market_news import MarketNewsArticle
    service = MarketNewsService()
    transcript_url = "https://www.bseindia.com/xml-data/corpfiling/AttachHis/b0188f3e-9bad-41cf-a0fc-5ffce711e708.pdf"

    mock_items = [
        {
            "title": "Exide Industries Limited - Transcript of Earnings Conference Call for Q2FY27",
            "url": transcript_url,
            "summary": "Transcript of the earnings call held on May 24, 2024",
            "published_at": None,
            "source": "BSE Announcements",
            "category": "NEWS",
            "enclosure_url": None,
        }
    ]

    with patch.object(service, "fetch_feed_items", return_value=mock_items):
        with patch.object(service, "get_active_portfolio_symbols", return_value={"EXIDEIND"}):
            with patch.object(service, "get_symbol_keyword_mappings", return_value={"Exide": "EXIDEIND"}):
                fetched, inserted = service.sync_all_feeds(db, max_targeted_symbols=0)
                assert inserted >= 1

                filing = db.query(MarketNewsArticle).filter(MarketNewsArticle.url == transcript_url).first()
                assert filing is not None
                # Should be auto-detected as CONCALL
                assert filing.category == "CONCALL"
                assert filing.metadata_json is not None
                assert filing.metadata_json.get("transcript_url") == transcript_url
                assert filing.metadata_json.get("quarter") == "Q2FY27"

                # Cleanup
                db.delete(filing)
                db.commit()


def test_bse_generic_description_peek_subject(db):
    from app.models.market_news import MarketNewsArticle
    from app.services.news_service import _is_generic_exchange_description

    # Test generic description detector
    assert _is_generic_exchange_description("Please find enclosed.")
    assert _is_generic_exchange_description("Enclosed herewith.")
    assert _is_generic_exchange_description("Regulation 30 disclosure")
    assert not _is_generic_exchange_description("Transcript of the Q2FY27 Earnings Conference Call held on November 24, 2026")

    service = MarketNewsService()
    igl_url = "https://www.bseindia.com/xml-data/corpfiling/AttachLive/d0b3e5b8-6f33-4db6-a680-2e44e81bde91.pdf"
    generic_items = [
        {
            "title": "IGL Spirits Ltd (545013)",
            "url": igl_url,
            "summary": "Please find enclosed.",
            "published_at": None,
            "source": "BSE Announcements",
            "category": "NEWS",
            "enclosure_url": None,
        }
    ]

    with patch.object(service, "fetch_feed_items", return_value=generic_items):
        with patch.object(service, "get_active_portfolio_symbols", return_value={"IGLSPIRITS"}):
            with patch.object(service, "get_symbol_keyword_mappings", return_value={"IGL Spirits": "IGLSPIRITS"}):
                with patch("app.services.news_service.peek_pdf_subject", return_value="Transcript of Q2 & H1 FY27 Earnings Conference Call"):
                    fetched, inserted = service.sync_all_feeds(db, max_targeted_symbols=0)
                    assert inserted >= 1

                    article = db.query(MarketNewsArticle).filter(MarketNewsArticle.url == igl_url).first()
                    assert article is not None
                    # Auto-detected as CONCALL from peeked subject
                    assert article.category == "CONCALL"
                    assert "Transcript of Q2 & H1 FY27" in article.title
                    assert "Transcript of Q2 & H1 FY27" in article.summary

                    db.delete(article)
                    db.commit()


def test_corporate_action_and_result_metadata_extraction(db):
    from app.models.market_news import MarketNewsArticle
    from app.services.news_service import extract_corporate_metadata

    # 1. Dividend
    div_meta = extract_corporate_metadata(
        "Fusion CX Limited - Ex-Date: 27-Nov-2026",
        "SERIES:EQ |PURPOSE:DIVIDEND - RE 0.75 PER SHARE |FACE VALUE:1 |RECORD DATE:27-Nov-2026",
    )
    assert div_meta["action_type"] == "DIVIDEND"
    assert div_meta["dividend_amount"] == 0.75
    assert div_meta["ex_date"] == "27-Nov-2026"
    assert div_meta["record_date"] == "27-Nov-2026"

    # 2. Split
    split_meta = extract_corporate_metadata(
        "VARVEE GLOBAL LIMITED - Ex-Date: 27-Nov-2026",
        "PURPOSE:FACE VALUE SPLIT (SUB-DIVISION) - FROM RS 5/- PER SHARE TO RS 2/- PER SHARE",
    )
    assert split_meta["action_type"] == "SPLIT"

    # 3. Leadership Change
    mgmt_meta = extract_corporate_metadata(
        "Infosys Limited (500209)",
        "Resignation of Chief Financial Officer and KMP of the Company",
    )
    assert mgmt_meta["change_type"] == "MANAGEMENT_CHANGE"

    # 4. Result Auto-Detection in sync_all_feeds
    service = MarketNewsService()
    result_url = "https://example.com/results-announcement-q2"
    result_item = [
        {
            "title": "Tata Motors Ltd (500570)",
            "url": result_url,
            "summary": "Outcome of Board Meeting - Unaudited Financial Results for Q2FY27 and Investor Presentation",
            "published_at": None,
            "source": "BSE Announcements",
            "category": "NEWS",
            "enclosure_url": None,
        }
    ]

    with patch.object(service, "fetch_feed_items", return_value=result_item):
        with patch.object(service, "get_active_portfolio_symbols", return_value={"TATAMOTORS"}):
            with patch.object(service, "get_symbol_keyword_mappings", return_value={"Tata Motors": "TATAMOTORS"}):
                fetched, inserted = service.sync_all_feeds(db, max_targeted_symbols=0)
                assert inserted >= 1

                article = db.query(MarketNewsArticle).filter(MarketNewsArticle.url == result_url).first()
                assert article is not None
                # Auto-detected as RESULT category
                assert article.category == "RESULT"
                assert article.metadata_json is not None
                assert article.metadata_json.get("quarter") == "Q2FY27"

                db.delete(article)
                db.commit()


def test_extract_corporate_metadata_dividend_guard():
    # User's reported Livemint article: Editorial yield screening should NOT be tagged as DIVIDEND
    editorial_meta = extract_corporate_metadata(
        "5 energy stocks with attractive dividend yield - Hindustan Petroleum, Indian Oil, Bharat Petroleum, ONGC, to Gulf Oil",
        "HPCL, Indian Oil, BPCL, ONGC and Gulf Oil Lubricants are highlighted for dividend income. HPCL delivered a 7.1% FY26 dividend yield...",
        is_exchange_filing=False,
    )
    assert editorial_meta.get("action_type") is None

    # Legitimate corporate dividend announcement
    declared_meta = extract_corporate_metadata(
        "TCS Board approves interim dividend of Rs 10.00 per share; fixes record date",
        "Tata Consultancy Services declared an interim dividend of Rs 10 per equity share for FY25. Record date: 18-Oct-2024",
        is_exchange_filing=False,
    )
    assert declared_meta.get("action_type") == "DIVIDEND"
    assert declared_meta.get("dividend_amount") == 10.0
    assert declared_meta.get("record_date") == "18-Oct-2024"


def test_exchange_announcement_deduplication():
    from app.services.news_service import (
        are_exchange_subjects_similar,
        extract_core_exchange_subject,
        is_xbrl_stub,
    )

    xbrl_title = "IGL SPIRITS LIMITED has informed the Exchange about Transcripts - earnings or quarterly calls |SUBJECT: Analyst/Investor Meet Para A-XBRL"
    real_title = "IGL Spirits Limited has informed the Exchange about Transcript |SUBJECT: Analysts/Institutional Investor Meet/Con. Call Updates"

    assert is_xbrl_stub(xbrl_title, "", "https://nsearchives.nseindia.com/corporate/xbrl/IGL_123.xml")
    assert not is_xbrl_stub(real_title, "", "https://nsearchives.nseindia.com/corporate/IGL_concall.pdf")

    sub_xbrl = extract_core_exchange_subject(xbrl_title, "")
    sub_real = extract_core_exchange_subject(real_title, "")
    assert are_exchange_subjects_similar(sub_xbrl, sub_real)

    # User reported: Bank of Baroda EGM newspaper publication across NSE and BSE
    nse_bob = "Bank Of Baroda has informed the Exchange about Newspaper Publication - EGM |SUBJECT: General Updates"
    bse_bob = "Bank of Baroda (532134) - Newspaper Publication - EGM"
    sub_nse = extract_core_exchange_subject(nse_bob, "")
    sub_bse = extract_core_exchange_subject(bse_bob, "")
    assert are_exchange_subjects_similar(sub_nse, sub_bse)


def test_generic_name_blacklist():
    from app.services.news_service import GENERIC_NAME_BLACKLIST

    assert "general insurance" in GENERIC_NAME_BLACKLIST
    assert "life insurance" in GENERIC_NAME_BLACKLIST
    assert "oil and gas" in GENERIC_NAME_BLACKLIST
    assert "bank of india" in GENERIC_NAME_BLACKLIST


def test_citurgia_result_classification(db):
    from app.models.market_news import MarketNewsArticle
    from app.services.news_service import (
        extract_corporate_metadata,
        extract_quarter_from_text,
    )

    desc = "UNAUDITED FINANCE RESULT FOR THE QUARTER AND HALF YEAR ENDED 30.09.2026"
    title = "Citurgia Biochemicals Ltd (506373)"
    pdf_url = "https://www.bseindia.com/xml-data/corpfiling/AttachLive/54847877-fcd2-4c2a-aca8-95238196a22b.pdf"

    # 1. Date-based quarter inference: 30.09.2026 is Q2 FY27
    assert extract_quarter_from_text(desc) == "Q2 FY27"

    # User reported: Subject line with month spelled out in words
    sub_line = "Sub: Submission of Unaudited Financial Results for Quarter and half year ended 30th September, 2026."
    assert extract_quarter_from_text(sub_line) == "Q2 FY27"

    # Additional month variations
    assert extract_quarter_from_text("Results for quarter ended 30th June, 2026") == "Q1 FY27"
    assert extract_quarter_from_text("Audited Results for year ended 31st March, 2026") == "Q4 FY26"

    meta = extract_corporate_metadata(title, desc, is_exchange_filing=True)
    assert meta.get("quarter") == "Q2 FY27"

    # 2. Feed sync auto-classification as RESULT
    service = MarketNewsService()
    raw_item = [
        {
            "title": title,
            "url": pdf_url,
            "summary": desc,
            "published_at": None,
            "source": "BSE Announcements",
            "category": "NEWS",
            "enclosure_url": None,
        }
    ]

    with patch.object(service, "fetch_feed_items", return_value=raw_item):
        with patch.object(service, "get_active_portfolio_symbols", return_value={"CITURGIBIO"}):
            with patch.object(service, "get_symbol_keyword_mappings", return_value={"Citurgia Biochemicals": "CITURGIBIO"}):
                fetched, inserted = service.sync_all_feeds(db, max_targeted_symbols=0)
                assert inserted >= 1

                article = db.query(MarketNewsArticle).filter(MarketNewsArticle.url == pdf_url).first()
                assert article is not None
                assert article.category == "RESULT"
                assert article.metadata_json is not None
                assert article.metadata_json.get("quarter") == "Q2 FY27"
                assert article.metadata_json.get("transcript_url") == pdf_url

                db.delete(article)
                db.commit()




