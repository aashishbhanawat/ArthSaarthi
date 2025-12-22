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

- [ ] User can select "Zerodha Coin (MF)" as statement type
- [ ] Parser handles both Excel and CSV formats
- [ ] All MF transaction types correctly mapped
- [ ] Scheme names matched to AMFI codes

---

## 6. Notes

- Existing Zerodha parser is for equity tradebook
- This is a separate parser for MF transactions from Coin
