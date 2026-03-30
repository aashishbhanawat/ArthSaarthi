# Changelog

All notable changes to ArthSaarthi will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-03-31

### Added

#### Asset Classes
- **Bonds (v2)** - Enhanced bond tracking with accurate historical price fallback and improved asset seeder classification
- **Fixed/Recurring Deposits (v2)** - Stabilized lifecycle management (matured assets), synthetic transaction history, and color-coded UI labels

#### Data Import
- **FD/RD PDF Import** - Support for importing Fixed Deposit statements from HDFC, ICICI, and SBI password-protected PDFs
- **Symbol Alias Management** - Admin UI to manage mapping between broker-specific symbols and exchange tickers
- **KFintech MF Mergers** - Enhanced support for parsing KFintech switch-in/out and merger transactions as BUY/SELL

#### Analytics & Benchmarking
- **Advanced Benchmarking** - Hybrid benchmark indices (CRISIL Hybrid 35+65, Balanced 50/50), risk-free rate overlay with configurable annual rate, and category benchmarking (Equity vs Nifty, Debt vs Bond Yields)
- **Daily Portfolio Snapshots** - Background caching of daily valuations for rapid historical chart loading

#### Reports
- **Dividend Export** - Dedicated CSV export for the consolidated dividend report
- **Demerger Cost Lookup** - Systemic support for demerger cost reduction in capital gains calculations
- **Schedule 112A Improvements** - Inclusion of expenditure and fees in Long Term Capital Gains (LTCG) reporting

#### Performance (Bolt)
- **FIFO Optimization** - Reduced capital gains calculation complexity from O(N*N) to O(N) for large portfolios
- **Prefetching** - Optimized historical data loading for PPF and non-market assets to eliminate N+1 query bottlenecks

### Fixed

- **Portfolio Realized P&L** - Systemic fix for calculation distortions in historical P&L
- **FD/RD/PPF/Bond History** - Significant accuracy improvements for non-market assets on the historical chart
- **Import Error Propagation** - Clearer validation error messaging (propagate 400 instead of 500)
- **Goal Redirection** - Correct 409 Conflict handling and UI notification when deleting a linked portfolio
- **E2E Test Stability** - Resolved race conditions in Playwright test suite

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
