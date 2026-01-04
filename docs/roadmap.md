# ArthSaarthi Roadmap

This document outlines planned features and improvements for future releases.

## v1.1 - Q1 2025

### P0: Bug Fixes (Critical)

| Issue | Description |
|-------|-------------|
| Privacy setting for PPF/Bond | Privacy toggle not being applied on portfolio page |
| Bond edit modal type | Edit modal shows "Stock" instead of "Bond" |
| **Sharpe ratio per-portfolio** | Same value for all portfolios (using combined history) |

---

### P1: Desktop UX Improvements

| Feature | Description |
|---------|-------------|
| **Splash screen for asset seeding** | Show splash with progress bar during initialization instead of banner |
| **Update notification** | Check GitHub Releases on startup, notify user if new version available with download link |

---

### P1: MF Import - CAMS & MFCentral

Support importing Mutual Fund transactions from major sources.

| Source | Format | Coverage |
|--------|--------|----------|
| **MFCentral** | Excel | 2022+ (all RTAs) |
| **CAMS** | Excel | Full history (HDFC, ICICI Pru, DSP, Franklin, TATA, Kotak, etc.) |

**Field mapping:**
| Our Field | MFCentral | CAMS |
|-----------|-----------|------|
| Date | Date | TRADE_DATE |
| Scheme | Scheme Name | SCHEME_NAME |
| Txn Type | Transaction Description | TRANSACTION_TYPE |
| Amount | Amount | AMOUNT |
| Units | Units | UNITS |
| NAV | NAV | PRICE |

---

### P2: MF Import - KFintech & Others

| Source | Format | Coverage |
|--------|--------|----------|
| **KFintech** | PDF | Full history (SBI, Axis, UTI, Nippon, Mirae, etc.) |
| **Zerodha Coin** | Excel/CSV | Direct MF via Zerodha |

Requires PDF parsing with multi-section structure (KFintech).

---

### P2: Dividend Statement Import ✅

| Source | Format | Status |
|--------|--------|--------|
| Zerodha Dividend | Excel (XLSX) | ✅ Done |
| ICICI DEMAT Dividend | PDF | ✅ Done |

Creates DIVIDEND transactions with TDS tracking.

---

### P2: Corporate Actions

| Feature | Description |
|---------|-------------|
| **Manual corporate action entry** | New transaction type for merger, demerger, ticker rename |
| **Documentation** | User guide section explaining how to handle corporate actions |

**Supported action types:**
- Merger (multiple old tickers → new ticker with ratio)
- Demerger (old ticker → multiple new tickers with ratio)
- Ticker rename/symbol change

**Import behavior:** Unrecognized tickers during import are skipped; user must manually log corporate actions.

---

### P3: Desktop Enhancements

| Feature | Description |
|---------|-------------|
| **System tray integration** | Minimize to tray instead of taskbar |

---

### P3: UX Improvements

| Feature | Description |
|---------|-------------|
| **System theme preference** | Add "System" option to follow OS light/dark mode changes dynamically |

---

### P3: Analytics Enhancements

| Feature | Description |
|---------|-------------|
| **Investment Style (Growth vs Value)** | Classify holdings by P/E, P/B ratios; on-demand fetch and cache |
| **Benchmark comparison (basic)** | Compare portfolio returns against Nifty 50 / Sensex |

---

### P4: Future Considerations

| Feature | Description |
|---------|-------------|
| Windows ARM64 native | Currently uses x64 via emulation |
| ICICI Direct MF PDF | Lower priority if CAMS covers same AMCs |

---

## v1.2.0 (Target: Feb 2026)

### Capital Gains View (FR6.5)

| Feature | Description |
|---------|-------------|
| **Capital gains summary** | Unrealized/realized gains with short-term vs long-term breakdown |
| **Asset-type-specific thresholds** | Listed equity (12mo), unlisted (24mo), debt/gold (36mo), SGBs (36mo + maturity exemption) |
| **Tax calculation** | STCG/LTCG rates per asset class |

---

### Historical Price Caching (NFR-Analytics-1)
- **Daily Portfolio Snapshots** - Cache daily valuations for history chart
- **MF NAV History** - Fetch and cache from AMFI for 1 year
- **Bond Price History** - Cache NSE prices or use amortized cost
- **Enhanced Sharpe Ratio** - Use cached history for all asset types

### Analytics & Reporting
- Capital gains report for tax filing (ITR format)
- **Advanced Benchmarking**:
    - **Hybrid Benchmarks**: Support mixed indices (e.g., CRISIL Hybrid 35+65) for balanced portfolios.
    - **Risk-Free Rate**: Overlay "Risk-Free" growth line (e.g., 6-7% p.a.) on comparison charts.
    - **Category Benchmarking**: Compare Equity portion vs Nifty, Debt vs Bond Yields independently.

### Goal Planning
- Link assets to financial goals
- Progress tracking with projections

### AI-Powered Features
- Tax-loss harvesting suggestions
- Portfolio rebalancing recommendations
- Personalized daily digest

### Market Insights
- News feeds for holdings
- Deep-dive asset research

---

## Contributing

See [Contributing Guide](contributing.md) for how to contribute to these features.
