# FR6.4: Diversification Analysis Visualizations

**Status: 🔄 Draft - Pending User Review**

## 1. User Story

As a diligent investor, I want to see a visual breakdown of my portfolio's diversification across various categories (Sector, Geography, Market Cap), so I can identify concentration risks and ensure my investments align with my strategy.

## 2. Problem Statement

The current system does not store or display any **sector**, **industry**, **geography**, or **market cap** metadata for assets. Users cannot visualize their portfolio's diversification, making it hard to identify concentration risks.

---

## 3. Data Source Analysis

> [!IMPORTANT]
> This is the key decision point. Please review the options below.

### Option A: Yahoo Finance (`yfinance`) - **Recommended**
- **Already Integrated:** The `yfinance` library is already used for price fetching.
- **Rich Metadata:** The `ticker.info` dictionary contains:
  - `sector` (e.g., "Technology", "Financial Services")
  - `industry` (e.g., "Software - Infrastructure", "Banks - Regional")
  - `country` (e.g., "United States", "India")
  - `marketCap` (numeric value for market cap classification)
- **Coverage:** Works for most global equities (NSE, BSE, NASDAQ, NYSE). Does NOT cover Mutual Funds, Bonds, FDs, or other non-equity assets.
- **Rate Limits:** No explicit API key, but aggressive usage can get IP blocked. Caching is essential.

### Option B: NSE/BSE Official Sector Lists
- **Pro:** Authoritative for Indian stocks.
- **Con:** Requires periodic manual download/scraping. No single API endpoint.
- **Use Case:** Could be a secondary source for validation or fallback.

### Option C: Open-Source Indian Stock API (GitHub)
- **Pro:** Free, no API key, includes sector/industry.
- **Con:** Reliability is unknown, not as well-maintained as yfinance.

### Recommendation
Use **Yahoo Finance (Option A)** as the primary source. It provides the richest metadata with minimal integration effort since the library is already in use.

---

## 3. Data Source Analysis

### 3.1. Equities (Stocks, ETFs) - Yahoo Finance
- **Source:** `yfinance` library (already integrated)
- **Fields Available:** `sector`, `industry`, `country`, `marketCap`
- **Coverage:** Global equities (NSE, BSE, NASDAQ, NYSE)

### 3.2. Mutual Funds - AMFI NAVALL.txt
- **Source:** `https://www.amfiindia.com/spages/NAVAll.txt`
- **Category Extraction:** The file contains category headers like:
  ```
  Open Ended Schemes(Equity Scheme - Large Cap Fund)
  Open Ended Schemes(Debt Scheme - Corporate Bond Fund)
  Open Ended Schemes(Hybrid Scheme - Aggressive Hybrid Fund)
  ```
- **Strategy:** Parse the header lines to extract:
  - **Primary Category:** "Equity Scheme", "Debt Scheme", "Hybrid Scheme", "Other Scheme"
  - **Sub-Category (optional):** "Large Cap Fund", "Corporate Bond Fund", etc.

### 3.3. Fixed Income (Bonds, FDs, RDs, PPF)
- **Source:** Hardcoded classification
- **Category:** All mapped to **"Fixed Income"** or **"Debt"**

---

## 4. Proposed Solution

### 4.1. Data Model Changes

Add new nullable columns to the `Asset` model:

| Column | Type | Description |
|--------|------|-------------|
| `sector` | `String` | Sector (for equities) or scheme type (for MFs) |
| `industry` | `String` | Industry (for equities) or scheme sub-type (for MFs) |
| `country` | `String` | Country of domicile |
| `market_cap` | `BigInteger` | Market cap (for equities only) |

### 4.2. Backend: Integrated Enrichment (via "Sync Assets")

> [!NOTE]
> Enrichment is integrated into the existing `seed-assets` command (triggered by "Sync Assets" in Admin UI). This ensures desktop mode users can populate metadata without CLI access.

**When user clicks "Sync Assets":**
1. **Existing behavior:** Update prices for all assets.
2. **NEW behavior:** For any asset with `sector = NULL`:
   - **Equities (STOCK, ETF):** Query `yfinance` for `sector`, `industry`, `country`, `marketCap`.
   - **Mutual Funds:** Lookup `mf_category` from enhanced NAVALL.txt parser.
   - **Fixed Income (BOND, FD, RD, PPF):** Set `sector = "Fixed Income"`.

**Rate Limiting:** To avoid IP blocks, enrich max 50 assets per sync. Subsequent syncs continue from where left off.

### 4.3. AMFI Provider Enhancement

Modify `_fetch_and_parse_amfi_data()` in `amfi_provider.py` to:
1. Track the current category header when parsing.
2. Store `mf_category` and `mf_sub_category` in the parsed data.

**Example Header Parsing:**
```python
# Input: "Open Ended Schemes(Equity Scheme - Large Cap Fund)"
# Output: mf_category = "Equity Scheme", mf_sub_category = "Large Cap Fund"
```

### 4.4. Frontend: Multi-Level Visualizations

**Level 1: Asset Class Breakdown**
- Pie chart: Equity vs Debt vs Hybrid vs Other

**Level 2: Within Asset Class**
- **Equities:** Sector breakdown (Technology, Finance, Healthcare, etc.)
- **Mutual Funds:** Scheme type breakdown (Large Cap, Mid Cap, Debt, Hybrid)
- **Fixed Income:** Instrument type (Bond, FD, RD, PPF)

**Level 3: Geographic Allocation**
- Country-based pie chart (for equities with `country` data)

---

## 5. Implementation Phases

| Phase | Description | Effort |
|-------|-------------|--------|
| 1 | Schema migration (add sector/industry/country/market_cap) | 0.5 day |
| 2 | Enhance AMFI parser to extract MF categories | 0.5 day |
| 3 | `enrich-assets` CLI command | 1 day |
| 4 | API endpoint: `/portfolios/{id}/diversification` | 1 day |
| 5 | Frontend: Multi-level diversification charts | 2 days |

**Total Estimated Effort:** ~5 days

---

## 6. Acceptance Criteria

- [x] "Sync Assets" populates `sector`/`industry` for equities from yfinance.
- [x] "Sync Assets" populates `mf_category` for Mutual Funds from NAVALL.txt.
- [x] Bonds, FDs, RDs, PPF are automatically categorized as "Debt".
- [x] Portfolio Analytics shows Asset Class pie chart (Equity/Debt/Hybrid).
- [x] Portfolio Analytics shows Sector, Industry, Market Cap charts (equities only).
- [x] Portfolio Analytics shows Geography chart (all assets).
- [x] Hovering over chart segments displays name and percentage.

### Future Enhancements
- [ ] Drill-down: Clicking "Equity" shows Sector breakdown
- [ ] Drill-down: Clicking "Mutual Funds" shows Scheme Type breakdown
- [ ] Market Cap: Apply live FX conversion for non-USD foreign stocks

### Known Limitations
- **Foreign stock market cap**: yfinance returns market cap in the stock's trading currency (EUR for AIR.PA, GBP for ULVR.L). Current thresholds assume USD-equivalent values, which is approximately correct for major currencies.
