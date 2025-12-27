# Feature Plan: Zerodha Coin MF Parser (FR7.1.7)

**Feature ID:** FR7.1.7  
**Title:** Zerodha Coin MF Import Parser  
**Priority:** P2  
**Parent FR:** FR7 (Automated Data Import)

---

## 1. Objective

Enable users to import Mutual Fund transactions from Zerodha Coin (direct MF platform) exports.

---

## 2. Source Details

| Attribute | Value |
|-----------|-------|
| Source | Zerodha Coin (coin.zerodha.com) |
| Format | Excel (XLSX) / CSV |
| Date Range | Full history |
| Coverage | Direct MF purchased via Zerodha |

---

## 3. Field Mapping

*Note: Exact columns to be confirmed from sample file*

| Zerodha Column | Internal Field |
|----------------|----------------|
| Scheme Name | scheme_name |
| Trade Date | transaction_date |
| Type | transaction_type |
| Quantity | quantity |
| Price | price_per_unit |
| Amount | total_amount |
| Folio | folio_number |

---

## 4. Implementation Plan

### 4.1 Backend

**New Files:**
- `backend/app/services/import_parsers/zerodha_coin_parser.py`
- `backend/app/tests/services/test_zerodha_coin_parser.py`
- `backend/app/tests/assets/sample_zerodha_coin.xlsx`

**Steps:**
1. Obtain sample Zerodha Coin export file
2. Analyze column structure
3. Create `ZerodhaCoinParser` class
4. Implement scheme name → AMFI code matching
5. Register in ParserFactory with key `'zerodha_coin'`

### 4.2 Frontend

- Add "Zerodha Coin (MF)" option to statement type dropdown

---

## 5. Acceptance Criteria

- [x] User can select "Zerodha Coin (MF)" as statement type
- [x] Parser handles both Excel and CSV formats
- [x] All MF transaction types correctly mapped (buy/sell)
- [x] Scheme names matched to AMFI codes (via alias modal)

---

## 6. Notes

- Existing Zerodha parser is for equity tradebook
- This is a separate parser for MF transactions from Coin

### XLSX File Format
- Zerodha Coin XLSX exports have 14 header rows of branding/info
- Actual data headers start at row 14
- The import system automatically skips these rows (`skiprows=14`)

### ISIN-Based Matching
- Parser extracts ISIN column if present in the file
- Uses `ISIN:{code}` format for ticker_symbol (e.g., `ISIN:INF179K01XD8`)
- Enables automatic asset matching via AMFI database
- Falls back to scheme name if ISIN not available

### Column Normalization
- XLSX column names are normalized to lowercase with underscores
- Example: `Trade Date` → `trade_date`, `Trade Type` → `trade_type`

---

## 7. Changelog

| Date | Change |
|------|--------|
| 2025-12-27 | Added ISIN-based auto-matching for assets |
| 2025-12-27 | Added XLSX header row handling (skiprows=14) |
| 2025-12-27 | Added column name normalization for XLSX |
