# Functional Requirement Specification: Market News Feed (FR8.2)

**Feature ID:** FR8.2  
**GitHub Issue:** [#86](https.github.com/aashishbhanawat/ArthSaarthi/issues/86)  
**Title:** Portfolio-Linked Financial Market News Feed  
**Target Release:** v1.5.0  

---

## 1. Sub-component Breakdown & Micro-Phases

### Phase 6.1: RSS & Financial News Fetching Engine
* Create `backend/app/services/news_service.py` to aggregate RSS and news feeds (Google News RSS for financial symbols, Moneycontrol, ET Markets, Yahoo Finance).
* Scheduler task (`fetch_market_news_job`) running every 4 hours to pull latest articles.

### Phase 6.2: Holding Ticker Linking & Sentiment Tagging
* Map news article keywords/tickers to active user portfolio holdings and watchlists.
* Basic NLP sentiment tagging (Positive, Negative, Neutral) based on financial keyword dictionary.

### Phase 6.3: UI News Feed Widgets & Asset Detail Tab
* Dashboard News Feed widget displaying latest relevant news for held assets.
* Asset Detail page tab showing asset-specific news history.

---

## 2. Technical Specification (Backend & Frontend)

### 2.1 Backend Implementation Details
* **News Service (`backend/app/services/news_service.py`):**
  * `fetch_news_for_holdings(user_id, db)`: Queries user's unique ticker list, fetches matching news items, deduplicates based on article URL / GUID.
  * Uses `feedparser` library (pure Python RSS parser) to parse XML/RSS feeds asynchronously.

### 2.2 Frontend Implementation Details
* **Dashboard News Widget (`src/components/dashboard/MarketNewsWidget.tsx`):**
  * Responsive news card list showing article title, publisher, published date, sentiment badge, and clickable external link.
  * Ticker pills linking article directly to specific holding asset detail modal.

---

## 3. Comprehensive Test Plan & Edge Cases

### 3.1 Edge Cases & Failure Scenarios
* **Feed Timeout / Malformed RSS:** `feedparser` handles invalid RSS/XML gracefully, returning empty entry list without throwing exceptions.
* **No Active Holdings:** User with empty portfolio receives general market/index news.
* **Duplicate Articles:** Article with same title/URL from multiple feeds deduplicated in memory before DB insert.

### 3.2 Manual Testing Checklist
* [ ] Add holdings (e.g. `RELIANCE`, `TCS`, `INFY`) to portfolio.
* [ ] Trigger news fetch job from Admin Scheduler UI.
* [ ] Verify relevant news articles appear on Dashboard news widget.
* [ ] Click news article link and confirm external opening in new tab.

---

## 4. Automated Testing Strategy

### 4.1 Backend Pytest (`backend/app/tests/services/test_news_service.py`)
* Mock RSS XML feed responses using `pytest-mock`.
* Test ticker matching algorithm and deduplication logic.

### 4.2 Frontend Vitest (`src/components/dashboard/__tests__/MarketNewsWidget.test.tsx`)
* Test rendering news list, sentiment badges, and empty state message.

### 4.3 E2E Playwright (`tests/market-news.spec.ts`)
* Test news widget display on Dashboard and filtering by asset ticker.

---

## 5. UX & UI Specifications
* **Widget Layout:** Card section on Dashboard right panel or tab.
* **News Item Card:** Image thumbnail (if present in RSS), article headline, publisher tag, time ago string (e.g. "2 hours ago"), and sentiment pill (Green = Positive, Red = Negative, Slate = Neutral).

---

## 6. Database Schema & Data Security

### 6.1 Database Schema
New table: `market_news_articles`

```sql
CREATE TABLE market_news_articles (
    id VARCHAR PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    summary TEXT NULL,
    url VARCHAR(1000) UNIQUE NOT NULL,
    source VARCHAR(100) NOT NULL,
    published_at TIMESTAMP WITH TIME ZONE NOT NULL,
    symbols JSONB DEFAULT '[]', -- List of associated tickers e.g. ["RELIANCE", "TCS"]
    sentiment VARCHAR(20) DEFAULT 'NEUTRAL', -- POSITIVE, NEGATIVE, NEUTRAL
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_news_published_at ON market_news_articles(published_at DESC);
```

### 6.2 Encryption Requirements
* Public news article data; no encryption required.

---

## 7. Required Documentation Updates

* **README.md:** Add Market News Feed feature summary.
* **docs/code_flow_guide.md:** Document news service integration and RSS feed sources.
* **docs/workflow_history.md:** Add entry upon completion.
* **docs/debugging_guide.md:** Add troubleshooting guide for news RSS parsing issues.
* **docs/project_handoff_summary.md:** Update FR8.2 completion status.
* **docs/requirements.md:** Mark FR8.2 as `✅ Implemented`.

---

## 8. External Data Sources & API Specifications
* Google News RSS: `https://news.google.com/rss/search?q={ticker}+stock+india&hl=en-IN&gl=IN&ceid=IN:en`
* Economic Times RSS: `https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms`
* Yahoo Finance RSS: `https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US`

---

## 9. File & API Endpoint Inventory

### Files to Create / Modify
* **Create:** `backend/app/models/market_news.py`
* **Create:** `backend/app/crud/crud_news.py`
* **Create:** `backend/app/services/news_service.py`
* **Create:** `backend/app/tasks/news_task.py`
* **Create:** `backend/app/api/v1/endpoints/news.py`
* **Create:** `frontend/src/components/dashboard/MarketNewsWidget.tsx`
* **Modify:** `frontend/src/pages/DashboardPage.tsx`

### API Routes
* `GET /api/v1/news/holdings` - Fetch portfolio-linked news articles
* `GET /api/v1/news/asset/{symbol}` - Fetch news for specific ticker
* `POST /api/v1/news/refresh` - Trigger immediate news fetch

---

## 10. Mobile-Friendly UI & Responsive Design
* Mobile news feed list with clean touch-friendly cards and horizontal ticker filter bar.

---

## 11. Android Compatibility & Python Library Constraints
* **RSS Parsing:** Use `feedparser` library (100% pure Python without C-extensions); fully compatible with Chaquopy / Android embedded Python runtimes.
