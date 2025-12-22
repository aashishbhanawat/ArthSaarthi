# Feature Plan: MFCentral Excel Parser (FR7.1.4)

**Feature ID:** FR7.1.4  
**Title:** MFCentral Excel Import Parser  
**Priority:** P1  
**Parent FR:** FR7 (Automated Data Import)

---

## 1. Objective

Enable users to import Mutual Fund transactions from MFCentral Excel export. MFCentral provides data from both CAMS and KFintech RTAs, but only from January 2022 onwards.

---

## 2. Source Details

| Attribute | Value |
|-----------|-------|
| Source | mfcentral.com |
| Format | Excel (XLSX) |
| Date Range | 2022-01-01 onwards |
| Coverage | All RTAs (CAMS + KFintech) |

---

## 3. Field Mapping

| MFCentral Column | Internal Field | Notes |
|------------------|----------------|-------|
| Scheme Name | scheme_name | Requires fuzzy match to AMFI code |
| Transaction Description | transaction_type | Map to BUY/SELL/DIVIDEND |
| Date | transaction_date | |
| NAV | price_per_unit | |
| Units | quantity | |
| Amount | total_amount | |

**Transaction Type Mapping:**
| MFCentral Description | Our Type |
|-----------------------|----------|
| Purchase / SIP | BUY |
| Redemption | SELL |
| Dividend Payout | DIVIDEND |
| Dividend Reinvestment | BUY (with dividend flag) |
| Switch In | BUY |
| Switch Out | SELL |

---

## 4. Implementation Plan

### 4.1 Backend

**New Files:**
- `backend/app/services/import_parsers/mfcentral_parser.py`
- `backend/app/tests/services/test_mfcentral_parser.py`
- `backend/app/tests/assets/sample_mfcentral.xlsx`

**Steps:**
1. Create `MfCentralParser` class extending `BaseParser`
2. Implement Excel parsing using `openpyxl` or `pandas`
3. Implement scheme name → AMFI code fuzzy matching
4. Register parser in `ParserFactory` with key `'mfcentral'`
5. Add unit tests with sample file

### 4.2 Frontend

- Add "MFCentral" option to statement type dropdown on import page
- No other UI changes needed (uses existing preview/commit flow)

---

## 5. Testing Plan

### Unit Tests
- Parse sample MFCentral Excel file
- Verify correct transaction count
- Verify field mapping accuracy
- Test scheme name matching

### Integration Tests
- Upload MFCentral file via API
- Verify preview returns correct data
- Verify commit creates transactions

### E2E Tests
- Full import flow with MFCentral file

---

## 6. Acceptance Criteria

- [ ] User can select "MFCentral" as statement type
- [ ] Parser correctly extracts all transaction types
- [ ] Scheme names are matched to AMFI codes
- [ ] Unmatched schemes trigger asset alias mapping UI
- [ ] Transactions are correctly committed to portfolio

---

## 7. Dependencies

- Existing import framework (FR7)
- AMFI asset database for scheme matching
