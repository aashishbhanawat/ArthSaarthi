# ArthSaarthi Roadmap

This document outlines planned features and improvements for future releases.

---

## v1.1.0 - Released January 15, 2026 ✅

### P0: Bug Fixes (Critical) ✅

| Issue | Description | Status |
|-------|-------------|--------|
| Privacy setting for PPF/Bond | Privacy toggle not being applied on portfolio page | ✅ Fixed |
| Bond edit modal type | Edit modal shows "Stock" instead of "Bond" | ✅ Fixed |
| Sharpe ratio per-portfolio | Same value for all portfolios (using combined history) | ✅ Fixed |

---

### P1: Desktop UX Improvements ✅

| Feature | Description | Status |
|---------|-------------|--------|
| Splash screen for asset seeding | Show splash with progress bar during initialization | ✅ Done |
| Update notification | Check GitHub Releases on startup, notify user if new version available | ✅ Done |

---

### P1: MF Import - CAMS & MFCentral ✅

| Source | Format | Status |
|--------|--------|--------|
| **MFCentral** | Excel | ✅ Done |
| **CAMS** | Excel | ✅ Done |

---

### P2: MF Import - KFintech & Others ✅

| Source | Format | Status |
|--------|--------|--------|
| **KFintech** | PDF | ✅ Done |
| **Zerodha Coin** | Excel/CSV | ✅ Done |
| **ICICI Securities MF** | PDF | ✅ Done |

---

### P2: Dividend Statement Import ✅

| Source | Format | Status |
|--------|--------|--------|
| Zerodha Dividend | Excel (XLSX) | ✅ Done |
| ICICI DEMAT Dividend | PDF | ✅ Done |

---

### P2: Corporate Actions ✅

| Feature | Description | Status |
|---------|-------------|--------|
| Manual corporate action entry | Merger, demerger, ticker rename | ✅ Done |
| Transaction type filters | Filter by COUPON, DRIP, MERGER, DEMERGER | ✅ Done |

---

### P3: Desktop Enhancements ✅

| Feature | Description | Status |
|---------|-------------|--------|
| System tray integration | Minimize to tray instead of taskbar | ✅ Done |

---

### P3: UX Improvements ✅

| Feature | Description | Status |
|---------|-------------|--------|
| System theme preference | Follow OS light/dark mode dynamically | ✅ Done |
| Dark theme toggle | Manual light/dark mode switch | ✅ Done |

---

### P3: Analytics Enhancements ✅

| Feature | Description | Status |
|---------|-------------|--------|
| Investment Style (Growth vs Value) | Classify holdings by P/E, P/B ratios | ✅ Done |
| Benchmark comparison (basic) | Compare portfolio returns against Nifty 50/Sensex | ✅ Done |
| Diversification analysis | Sector, geography, asset class breakdown | ✅ Done |

---

## v1.2.0 - Target: March 1, 2026

### Capital Gains & Tax Reporting (Core Focus)

| Feature | Description | Priority | Status |
|---------|-------------|----------|--------|
| **Capital Gains View** | STCG/LTCG breakdown with holding period calculation | P0 | 🔲 Planned |
| **Tax Threshold Logic** | Asset-class-specific thresholds (12mo equity, 24mo unlisted, 36mo debt) | P0 | 🔲 Planned |
| **Tax Calculation** | STCG/LTCG rates per asset class (10%/12.5%/20% LTCG) | P0 | 🔲 Planned |
| **Capital Gains Report** | CSV/PDF export for ITR tax filing | P1 | 🔲 Planned |

---

### Historical Data & Analytics

| Feature | Description | Priority | Status |
|---------|-------------|----------|--------|
| **Daily Portfolio Snapshots** | Cache daily valuations for history chart | P2 | 🔲 Planned |
| **MF NAV History** | Fetch and cache from AMFI for 1 year | P2 | 🔲 Planned |
| **Advanced Benchmarking** | Hybrid indices, risk-free rate overlay | P3 | 🔲 Planned |

---

## v1.3.0+ - Future Releases

### AI-Powered Features

| Feature | Description | Status |
|---------|-------------|--------|
| Tax-loss harvesting suggestions | AI-powered optimization recommendations | 🔲 Planned |
| Portfolio rebalancing recommendations | Re-allocation suggestions | 🔲 Planned |
| Personalized daily digest | Summary of portfolio changes | 🔲 Planned |

### Mobile App

| Feature | Description | Status |
|---------|-------------|--------|
| iOS App | Native iPhone app | 🔲 Planned |
| Android App | Native Android app | 🔲 Planned |

### Other

| Feature | Description | Status |
|---------|-------------|--------|
| Windows ARM64 native | Currently uses x64 via emulation | 🔲 Planned |
| News feeds for holdings | Market news integration | 🔲 Planned |

---

## Contributing

See [Contributing Guide](contributing.md) for how to contribute to these features.
