# Feature Plan: CAMS Excel Parser (FR7.1.5)

**Feature ID:** FR7.1.5  
**Title:** CAMS Excel Import Parser  
**Priority:** P1  
**Parent FR:** FR7 (Automated Data Import)

---

## 1. Objective

Enable users to import Mutual Fund transactions from CAMS (Computer Age Management Services) Excel export. CAMS serves ~65% of Indian AMCs including HDFC, ICICI Prudential, DSP, Franklin Templeton, TATA, Kotak, and others.

---

## 2. Source Details

| Attribute | Value |
|-----------|-------|
| Source | camsonline.com |
| Format | Excel (XLS/XLSX) |
| Date Range | Full history available |
| Coverage | CAMS AMCs (~65% of market) |

---

## 3. Field Mapping

| CAMS Column | Internal Field | Notes |
|-------------|----------------|-------|
| MF_NAME | amc_name | For validation |
| INVESTOR_NAME | - | Skip (privacy) |
| PAN | - | Skip (privacy) |
| FOLIO_NUMBER | folio_number | Store as reference |
| PRODUCT_CODE | - | Internal code |
| SCHEME_NAME | scheme_name | Fuzzy match to AMFI |
| Type | - | Fund type |
| TRADE_DATE | transaction_date | |
| TRANSACTION_TYPE | transaction_type | Map to BUY/SELL/DIVIDEND |
| DIVIDEND_RATE | - | For dividend transactions |
| AMOUNT | total_amount | |
| UNITS | quantity | |
| PRICE | price_per_unit | NAV |
| BROKER | - | Skip |

**Transaction Type Mapping:**
| CAMS Type | Our Type |
|-----------|----------|
| Purchase | BUY |
| Additional Purchase | BUY |
| SIP | BUY |
| Redemption | SELL |
| Dividend Payout | DIVIDEND |
| Dividend Reinvestment | BUY |
| Switch In | BUY |
| Switch Out | SELL |

---

## 4. Implementation Plan

### 4.1 Backend

**New Files:**
- `backend/app/services/import_parsers/cams_parser.py`
- `backend/app/tests/services/test_cams_parser.py`
- `backend/app/tests/assets/sample_cams.xlsx`

**Steps:**
1. Create `CamsParser` class extending `BaseParser`
2. Handle both XLS and XLSX formats
3. Implement scheme name → AMFI code fuzzy matching
4. Register parser in `ParserFactory` with key `'cams'`
5. Add unit tests

### 4.2 Frontend

- Add "CAMS Statement" option to statement type dropdown
- No other UI changes needed

---

## 5. Acceptance Criteria

- [x] User can select "CAMS Statement" as statement type
- [x] Parser handles both XLS and XLSX formats
- [x] All transaction types are correctly mapped
- [x] Scheme names matched to AMFI codes (via alias modal)
- [x] IDCW Reinvestment creates DIVIDEND + BUY transactions

---

## 6. Dependencies

- Existing import framework (FR7)
- AMFI asset database
