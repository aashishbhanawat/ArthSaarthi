# ArthSaarthi Roadmap

This document outlines planned features and improvements for future releases.

## v1.1 - Q1 2025

### P0: Bug Fixes (Critical)

| Issue | Description |
|-------|-------------|
| Privacy setting for PPF/Bond | Privacy toggle not being applied on portfolio page |
| Bond edit modal type | Edit modal shows "Stock" instead of "Bond" |

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

### P2: MF Import - KFintech

| Source | Format | Coverage |
|--------|--------|----------|
| **KFintech** | PDF | Full history (SBI, Axis, UTI, Nippon, Mirae, etc.) |

Requires PDF parsing with multi-section structure.

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
| System tray integration | Minimize to tray instead of taskbar |

---

### P4: Future Considerations

| Feature | Description |
|---------|-------------|
| Windows ARM64 native | Currently uses x64 via emulation |
| Zerodha Coin MF parser | Direct Coin export import |
| ICICI Direct MF PDF | Lower priority if CAMS covers same AMCs |

---

## Future Versions (v1.2+)

### Analytics & Reporting
- Capital gains report for tax filing
- Benchmark comparison (Nifty, Sensex)
- Sector/geography diversification analysis

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
