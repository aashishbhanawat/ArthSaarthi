# Functional Requirement: FR8.2.1 - Concall & Quarterly Result Ingestion Reliability & Optimization

**Status:** In Progress  
**Parent Requirement:** [FR8.2: Market News Feed](requirements.md#fr8-market-insights--research)  
**Issue Reference:** [#616](https://github.com/aashishbhanawat/ArthSaarthi/issues/616)

---

## 1. Overview & Problem Statement

Mainstream news headlines frequently get syndicated across multiple news agencies (e.g., Press Trust of India syndications to NDTV, Mint, and Economic Times). To prevent duplicate clutter, `HeadlineDeduplicator` uses word-shingle Jaccard similarity ($\ge 0.60$) to filter near-duplicate headlines.

However, earnings conference calls and quarterly financial disclosures adhere to standard corporate templates:
* `"{Company Name} Results Earnings Call for Q2FY27"`
* `"{Company Name} Q2 Results / Financial Disclosures"`

Because these structured items share high word-shingle overlap across completely different companies, `HeadlineDeduplicator` erroneously filtered over **180 out of 500 earnings concalls** (e.g. Exide Industries, Cummins India, Oil India, Voltas, Page Industries) as "duplicates" of each other. Furthermore, exchange announcements (BSE) returning ~9,400 entries caused synchronous `/refresh` timeouts, preventing high-value corporate disclosures from completing ingestion.

---

## 2. Functional Requirements

### FR8.2.1.1: Category-Specific Headline Deduplication
* `HeadlineDeduplicator.is_duplicate()` must **only** be applied to items where `category == "NEWS"`.
* Structured corporate disclosures (`CONCALL`, `RESULT`, `BROKER_REPORT`) must **never** be discarded by headline similarity.

### FR8.2.1.2: Feed Ingestion Capping & Performance Optimization
* Ingest high-value feeds (Concalls, Broker Reports, Quarterly Results, Targeted Google News) without truncation.
* Cap voluminous raw announcement feeds (such as BSE Announcements) to the most recent 100 items per sync run to keep sync duration $< 5$ seconds and eliminate HTTP timeout aborts.

### FR8.2.1.3: 30-Day Guaranteed Retention in Respective Tabs
* The **Earnings Concalls** (`CONCALL`) and **Quarterly Results** (`RESULT`) tabs must always display all items stored within the 30-day retention window for the user's holdings and watchlists.
* Retroactively match and tag existing untagged articles within the 30-day retention window against active watchlist and holding symbols during sync execution.
