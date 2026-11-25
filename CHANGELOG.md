# Changelog

All notable changes to ArthSaarthi will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.0] - 2026-11-25

### Added

#### Broker API Integration & Data Automation
- **Direct Broker API Sync (`NFR12`):** Integrated Zerodha Kite and ICICI Breeze API sync workflows (`BrokerApiSyncCard.tsx`, `brokers.py`) with AES-256-GCM encrypted credential storage (`broker_credentials`).
- **In-Process Background Job Scheduler (`APScheduler`):** Embedded `AsyncIOScheduler` into FastAPI lifespan (`app/core/scheduler.py`) with concurrency guards, execution audit logs (`scheduled_job_logs`), and an Admin Scheduler Dashboard (`SchedulerDashboard.tsx`).
- **Automated Bond & Stock Corporate Actions (`#562`, `#607`):** Scheduled bond coupon payouts, bond maturity redemptions, and stock dividend/split/bonus ingestion with user notification receipts (`corporate_action_events`, `CorporateActionNotificationModal.tsx`).
- **API Rate Limiting & Caching (`NFR13`):** Added rate-limiting and multi-tier caching across market data, asset seeding, and research endpoints.

#### Market Research & Edge AI Concall Intelligence (`FR8.2`, `FR8.2.1`, `FR8.2.2`)
- **Research Intelligence Feed (`#618`):** Multi-source aggregation of NSE/BSE corporate filings, Trendlyne concall audio/transcripts, Yahoo Finance `.NS` RSS feeds, and broker research reports (`market_news_articles`, `ResearchIntelligenceFeed.tsx`).
- **On-Device Concall Transcription & FinBERT-Tone NLP:** Integrated CTranslate2 INT8 `faster-whisper` (via PyAV, no system `ffmpeg` required) with Indian financial phonetic normalization, official PDF transcript auto-priority, and `yiyanghkust/finbert-tone` INT8 ONNX sentiment analysis (`ConcallAnalysisModal.tsx`).
- **Quantitative Concall Analytics:** Prepared vs Q&A Tone Divergence Alerts, Loughran-McDonald Hedging & Uncertainty Index, 4-Aspect Financial Sentiment Scorecards (Demand, Margins, Guidance, CapEx), and Extractive Red Flags.
- **AI Model Management:** Added `AIModelManagementCard.tsx` and `/api/v1/ml/*` endpoints to download and manage local Whisper and FinBERT ONNX models.

#### Desktop & UX
- **Desktop Update Notifications (`FR-Desktop-2`):** Automatic startup check against GitHub Releases for new desktop versions.

### Security
- **PII Log Removal (`#601`):** Removed raw Zerodha/ICICI holdings and trade item `logger.debug` dumps from `broker_api_parser.py`.
- **Diagnostic Script Guard (`#602`):** Added `ENVIRONMENT=production` exit guard to `backend/scripts/inspect_icici_raw.py`.
- **System Endpoint Auth (`#603`):** Enforced admin JWT authentication on `GET /api/v1/system/logs` and `POST /api/v1/system/snapshots/run-daily` in server and desktop modes while preserving Android WorkManager local loopback access.

### Fixed
- **Concall Polling & Pool Exhaustion:** Added `_in_flight_concalls` deduplication, `check_only` polling, and early DB session release before long-running Whisper/FinBERT execution.
- **Docker Build Dependencies:** Resolved `click` vs `huggingface-hub` dependency conflict (`click==8.5.1`).

---

## [1.4.0] - 2026-09-02

### Added

#### Tax Readiness & Income Management
- **Unrealized Capital Gains & Sec 112A Pooling:** FIFO lot-level STCG/LTCG unrealized gains calculator with grandfathering support and Section 112A ₹1,25,000 LTCG exemption headroom pooling (FR6.5 Phase 2 / #516).
- **Intra-Head Capital Loss Set-Off:** Section 70/71/74 statutory capital loss set-off rules (STCL against STCG/LTCG; LTCL against LTCG only) and effective rate alignment (FR6.5 Phase 3 / #526).
- **Income Source & Entry Data Management:** Custom income sources (Salary, Freelance, Rental, Dividends, Business) and income entry transactions with gross, TDS, net, and AES-256 encrypted fields (`EncryptedString`) (FR16.1, FR16.2 / #517).
- **Salary Component Breakdown & Sec 10(13A) HRA Exemption:** Detailed salary components (Basic, DA, HRA, Flexible Allowances, Rent Paid, Metro toggle) and statutory HRA exemption engine (`SalaryExemptionService`) with 100% mathematical parity against benchmark Excel spreadsheet `local/TaxCalc_2027.xlsx` cell D101 (FR16.5 / #532).
- **Tax-Deductible Expense & Investment Logging:** Chapter VI-A investment logging (Section 80C ₹1.5L, Section 80D medical, Section 80CCD(1B) NPS, Section 80TTA/80TTB interest) with statutory ceiling limit progress meters and capping (FR16.3 / #518).
- **Structured Tax Readiness Summary & Regime Comparison:** Consolidated Financial Year tax readiness report comparing Old Tax Regime vs New Tax Regime (Section 115BAC), displaying potential tax savings, non-advisory legal notice banners, and CSV/PDF report exporters (FR16.4, FR16.4.1 / #519).

#### Security & Desktop/Mobile Protection
- **`SECRET_KEY` Persistence:** Local file persistence of application `SECRET_KEY` to `secret.key` in app data directory to prevent JWT session invalidation across app restarts.
- **SQLite Bytes Decoding:** Dynamic string decoding in `EncryptedString` database decorator for mobile SQLite drivers.

---

## [1.3.0] - 2026-08-15

### Added

#### Goals & Analytics
- **Required Monthly Contribution (SIP Calculator):** Ordinary annuity monthly SIP calculation accounting for target date duration, PV compounding, zero-rate fallbacks, and past target dates (FR13.3).
- **Goal Projections & Track Status:** Future value compounding using linked asset dynamic XIRR, target path chart plotting, and dynamic status badges (`On Track` / `Off Track`) (FR13.4).

#### Market Data & Asset Master
- **Upstox V3 Provider Integration:** Free zero-cost unauthenticated historical candles (`GET /v3/historical-candle/...`) and trading holidays API (`GET /v2/market/holidays`) with rate limiting (#498).
- **CDN Asset Master Seeding:** Download and cache `NSE.json.gz` from Upstox CDN for 0-cost $O(1)$ ISIN $\leftrightarrow$ Symbol lookups.

#### Risk Profiling
- **Grable & Lytton 13-Question Risk Scale:** Upgraded risk questionnaire with score calculation (/47 points) classifying users into Conservative, Moderate, Growth, and Aggressive risk profiles with target asset allocation (FR12.1 / #76).

#### Android & Mobile Enablement
- **Background Portfolio Snapshot:** Native WorkManager `SnapshotWorker.kt` for daily background portfolio valuations (#492).
- **Native Settings Toggle:** Integrated `AndroidSettingsCard` in user profile page.
- **Pydantic V1 & Chaquopy Compatibility:** Restored SQLite/DiskCache compatibility layer for embedded Android Python environment (#495).

#### Security & Tenant Isolation
- **Tax Report Endpoint Authorization:** Enforced user authentication and strict tenant filtering on Capital Gains and Dividend report endpoints (#423).
- **Goal Asset IDOR Protection:** Secured goal asset linking endpoints against IDOR vulnerability (#434, #467).
- **PPF Immutability & Scoping:** Restricted update/delete on system-generated PPF interest credits and introduced user-scoped PPF account tickers (`PPF-{user_id_short}-{account_number}`).

### Fixed
- **Transaction Enum Serialization:** Added `FD_DEPOSIT` and `FD_MATURITY` to `TransactionType` schema to fix FastAPI `ResponseValidationError` (#510).
- **Sell Modal Tax Lot Scoping & Splits:** Filtered sell modal available tax lots to active portfolio and replayed corporate action splits chronologically (#442, #443).
- **Asset Seeding Classification:** Fixed misclassifying equity stocks with month-like names as bonds (#438).

## [1.2.0] - 2026-02-27

### Added

#### Analytics
- **Advanced Benchmarking** - Hybrid benchmark indices (CRISIL Hybrid 35+65, Balanced 50/50), risk-free rate overlay with configurable annual rate, and category benchmarking (Equity vs Nifty, Debt vs Bond Yields)

### Fixed

- Category benchmark portfolio XIRR now correctly calculated from subset cash flows
- Dark mode visibility for risk-free rate input
- Dropdown width for benchmark selector preventing text truncation

## [1.1.0] - 2026-01-15

### Added

#### Analytics
- **Benchmark Comparison** - Compare portfolio returns against Nifty 50/Sensex (#199)
- **Investment Style Classification** - Growth vs Value analysis with P/E, P/B metrics (#197)
- **Diversification Analysis** - Asset allocation charts with sector breakdown (#183)
- **Realized P&L Tracking** - Track locked-in profits and dividend income (#182)

#### Data Import
- **MFCentral CAS Parser** - Import MF transactions from MFCentral Excel (#173)
- **CAMS MF Parser** - Import from CAMS consolidated statements (#174)
- **KFintech PDF Parser** - Import KFintech MF statements (#176)
- **Zerodha Coin Parser** - Import direct MF from Zerodha Coin (#175)
- **ICICI Securities MF Parser** - Import ICICI MF transactions (#178)
- **Zerodha Dividend Parser** - Import equity dividends from Zerodha XLSX (#179)
- **ICICI DEMAT Dividend Parser** - Import dividend statements from ICICI PDF (#179)

#### Desktop App
- **System Tray Integration** - Minimize to tray instead of taskbar (#191)
- **Update Notifications** - Check for new versions on startup (#188)
- **Splash Screen** - Progress indicator during asset database seeding (#187)

#### UI/UX
- **Dark Theme** - Toggle between light and dark modes (#172)
- **System Theme Option** - Follow OS light/dark preference (#193)
- **Transaction Type Filters** - Filter by COUPON, DRIP, MERGER, DEMERGER

#### Other
- **Corporate Actions** - Improved merger/demerger/rename handling (#180)
- **PPF Rate Q1-2026** - Extended 7.1% rate through March 2026

### Fixed

- E2E tests for search-stocks endpoint (#205)
- Benchmark XIRR for foreign stocks (#202)
- Backup/restore for foreign stocks & RSU sell-to-cover (#201)
- Dark mode visibility for inputs and charts (#200)
- Sharpe ratio calculation per portfolio (#163)
- Bond edit modal showing wrong asset type (#169)
- Privacy mode for PPF/Bond holdings (#168)
- PPF contribution edit pre-fill (#171)

### Security

- Updated urllib3 to 2.6.3 (CVE-2026-21441)
- Updated react-router-dom to 7.1.1 (CVE-2025-68470, CVE-2026-22029)

## [1.0.0] - 2025-12-15

Initial public release.
