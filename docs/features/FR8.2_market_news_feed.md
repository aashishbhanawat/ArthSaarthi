# Functional Requirement Specification: Portfolio Research & Intelligence Feed (FR8.2)

**Feature ID:** FR8.2  
**GitHub Issue:** [#86](https://github.com/aashishbhanawat/ArthSaarthi/issues/86)  
**Title:** Portfolio Research & Intelligence Feed (Curated News, Broker Targets & Concall Insights)  
**Target Release:** v1.5.0  

---

## 1. Executive Summary & Objective

Modern equity investors require more than fragmented raw news headlines to make informed portfolio decisions. Inspired by institutional and retail research hubs like **Trendlyne** (`/recommended/`, `/conference-calls/`, `/rapid-results/`, `/news-by-trendlyne/`), **FR8.2** expands ArthSaarthi's Market News Feed into a comprehensive **Portfolio Research & Intelligence Feed**.

The system periodically aggregates, normalizes, and filters external feeds specifically linked to the active stock holdings and watchlists of the user, categorizing them into three core research pillars:
1. **Curated News & Market Pulse:** Material events, order wins, regulatory news, and macro updates.
2. **Brokerage Research & Target Prices:** Domestic analyst ratings (Buy/Accumulate/Hold/Sell), target prices, and upside potential %.
3. **Quarterly Results & Concalls:** Upcoming result dates, declared financial performance scorecards (YoY/QoQ), and conference call audio recordings and investor presentations.

---

## 2. The 3 Research Pillars & Source Integrations

```
                               ┌────────────────────────────────────────────────────────┐
                               │        Portfolio Research & News Feed (FR8.2)          │
                               └──────────────────────────┬─────────────────────────────┘
                                                          │
          ┌───────────────────────────────────────────────┼───────────────────────────────────────────────┐
          │                                               │                                               │
          ▼                                               ▼                                               ▼
┌───────────────────┐                           ┌───────────────────┐                           ┌───────────────────┐
│ 1. Curated News   │                           │ 2. Broker Reports │                           │ 3. Earnings Calls │
│    & Market Pulse │                           │    & Target Price │                           │    & Concalls     │
├───────────────────┤                           ├───────────────────┤                           ├───────────────────┤
│ • Material events │                           │ • Broker Buy/Hold │                           │ • Concall audio & │
│ • Regulatory news │                           │   /Sell ratings   │                             transcripts links │
│ • Order wins      │                           │ • Target prices & │                           │ • Management      │
│ • Macro updates   │                           │   upside %        │                             guidance summary  │
├───────────────────┤                           ├───────────────────┤                           ├───────────────────┤
│ Google News RSS,  │                           │ Moneycontrol      │                           │ Trendlyne Concall │
│ ET Markets, Mint  │                           │ Broker Reports,   │                           │ Feed, Moneycontrol│
│ & Moneycontrol    │                           │ Trendlyne Public  │                           │ Results, BSE/NSE  │
└───────────────────┘                           └───────────────────┘                           └───────────────────┘
```

### 2.1 Pillar 1: Curated News & Market Pulse
* **Google News Finance RSS:** Queries targeted patterns such as `"{company_name}" OR "{symbol}" stock india` to extract high-signal reporting from top business publications (Economic Times, Mint, Moneycontrol, Business Standard, CNBC-TV18, NDTV Profit).
* **Yahoo Finance RSS:** Targeted queries for foreign equities, ESPPs, and RSUs (`{symbol}`).
* **Macro Market Feeds:** Economic Times Markets (`1977021501.cms`) and Moneycontrol Top News for market-wide context.

### 2.2 Pillar 2: Brokerage Research & Recommendations (Trendlyne Recommended Style)
* **Moneycontrol Broker Research Feed:** `https://www.moneycontrol.com/rss/brokeragereports.xml`.
* **Analyst Consensus & Target Extraction:** Extracts:
  - Brokerage House (e.g., Motilal Oswal, ICICI Direct, HDFC Securities, Kotak, Jefferies).
  - Recommendation Action (`BUY`, `ACCUMULATE`, `HOLD`, `REDUCE`, `SELL`).
  - Target Price (`target_price`) & Upside Potential percentage based on current market price.

### 2.3 Pillar 3: Quarterly Results & Earnings Concalls (Trendlyne AI Concall Style)
* **Trendlyne Concall Podcast / Audio Feed:** `https://trendlyne.com/feeds/earning-calls-podcast-rss/` providing concall audio links and discussions for listed Indian companies.
* **Moneycontrol Quarterly Results Feed:** `https://www.moneycontrol.com/rss/results.xml` for newly declared earnings.
* **Metadata Extraction:** Quarter period (e.g., `Q2 FY25`), audio URL, presentation link, and key takeaway bullets.

---

## 3. Database Schema

A new table `market_news_articles` tracks ingested research items with categorization and metadata:

```sql
CREATE TABLE market_news_articles (
    id VARCHAR(64) PRIMARY KEY, -- SHA256 hash of URL or GUID for strict deduplication
    title VARCHAR(500) NOT NULL,
    summary TEXT NULL,
    url VARCHAR(1000) UNIQUE NOT NULL,
    source VARCHAR(100) NOT NULL, -- e.g., 'Google News', 'Moneycontrol', 'Trendlyne', 'ET'
    category VARCHAR(30) NOT NULL DEFAULT 'NEWS', -- 'NEWS', 'BROKER_REPORT', 'CONCALL', 'RESULT'
    published_at TIMESTAMP WITH TIME ZONE NOT NULL,
    symbols JSONB NOT NULL DEFAULT '[]', -- Array of mapped tickers e.g. ["RECLTD", "TCS"]
    sentiment VARCHAR(20) NOT NULL DEFAULT 'NEUTRAL', -- 'POSITIVE', 'NEGATIVE', 'NEUTRAL'
    metadata_json JSONB NULL, -- Extracted fields: {"broker": "Motilal Oswal", "target_price": 600, "recommendation": "BUY", "audio_url": "...", "quarter": "Q2FY25"}
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_news_published_at ON market_news_articles(published_at DESC);
CREATE INDEX idx_news_category ON market_news_articles(category);
```

---

## 4. Backend Architecture & Scheduling

### 4.1 Ingestion Service (`backend/app/services/news_service.py`)
* **Pure Python RSS & XML Parser:** Standard library `xml.etree.ElementTree` with `httpx` async client (with graceful error handling and timeouts) ensuring 100% Android (Chaquopy) and desktop SQLite compatibility with zero C-extension issues.
* **Symbol Matching Engine:**
  - Extracts active equity/ETF holding symbols and watchlist tickers for active users.
  - Matches tickers against article titles, descriptions, and tags.
  - Sentiment dictionary scoring (positive/bullish keywords vs negative/bearish keywords).

### 4.2 Background Task Registration (`backend/app/tasks/news_task.py`)
* Registered in `app/tasks/registry.py` under job ID `fetch_market_news`:
  - **Server Mode:** CronTrigger every 4 hours (`0 */4 * * *`).
  - **Desktop / Android Mode:** IntervalTrigger every 4 hours.
* Auto-cleans articles older than 30 days to keep database size lightweight.

### 4.3 REST API Endpoints (`backend/app/api/v1/endpoints/news.py`)
* `GET /api/v1/news/feed`:
  - Query params: `category` (optional: `NEWS`, `BROKER_REPORT`, `CONCALL`, `RESULT`), `symbol` (optional), `limit` (default 30), `offset` (default 0).
  - Filters by the authenticated user's portfolio holdings and watchlists, or returns macro news if portfolio is empty.
* `GET /api/v1/news/summary`:
  - Returns counts and latest highlights across all 3 pillars for quick dashboard badges.
* `POST /api/v1/news/admin/refresh`:
  - Admin/user trigger to manually execute an on-demand feed fetch.

---

## 5. Frontend UI/UX Architecture

### 5.1 Dashboard Research Widget (`frontend/src/components/dashboard/ResearchIntelligenceFeed.tsx`)
* Embedded on the main Dashboard page.
* **Filter Bar:**
  - Asset Ticker pills: "All Holdings", followed by chips for user's held stocks (e.g. `[All]`, `[RECLTD]`, `[TCS]`, `[INFY]`).
* **Three Functional Tabs:**
  1. **News & Media:** Displays news card with publisher badge, relative timestamp ("2h ago"), sentiment pill, and external link.
  2. **Broker Calls & Targets:** Displays target price, broker name, rating badge (Green `BUY`, Amber `HOLD`, Red `SELL`), and upside % badge.
  3. **Results & Concalls:** Displays quarterly result summary cards and concall audio player / external recording links.
* **Responsive Design:** Fully fluid for mobile screens (`< 768px`) with horizontal scrollable tabs and swipeable cards.

---

## 6. Implementation & Micro-Phases

* **Phase 1: Database Models & Alembic Migration**
  - Create `MarketNewsArticle` model in `backend/app/models/market_news.py`.
  - Create Alembic migration script.
* **Phase 2: Ingestion & Symbol Matching Engine**
  - Implement `backend/app/services/news_service.py` with multi-source RSS parsers, symbol matching, and deduplication.
  - Implement `backend/app/crud/crud_news.py`.
* **Phase 3: Background Scheduler Task & Admin Trigger**
  - Create `backend/app/tasks/news_task.py` and register in `app/tasks/registry.py`.
  - Wire up `/api/v1/news` endpoints.
* **Phase 4: Frontend Intelligence Feed Widget**
  - Build `ResearchIntelligenceFeed.tsx` with tabs, filter pills, and cards.
  - Integrate into `DashboardPage.tsx`.
* **Phase 5: Comprehensive Automated Testing & Verification**
  - Backend tests in `test_news_service.py` and `test_news_api.py` (Postgres & SQLite).
  - Frontend Jest/Vitest tests in `ResearchIntelligenceFeed.test.tsx`.
  - Documentation updates (`workflow_history.md`, `project_handoff_summary.md`, `requirements.md`).
