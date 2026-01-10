# Changelog

All notable changes to ArthSaarthi will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-01-14

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

- Updated urllib3 to 2.7.0 (CVE-2026-21441)
- Updated react-router-dom to 7.1.1 (CVE-2025-68470, CVE-2026-22029)

## [1.0.0] - 2025-12-15

Initial public release.
