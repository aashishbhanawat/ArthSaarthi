# Feature Plan: KFintech PDF Parser (FR7.1.6)

**Feature ID:** FR7.1.6  
**Title:** KFintech PDF Import Parser  
**Priority:** P2  
**Parent FR:** FR7 (Automated Data Import)

---

## 1. Objective

Enable users to import Mutual Fund transactions from KFintech (formerly Karvy) PDF statements. KFintech serves ~35% of Indian AMCs including SBI, Axis, UTI, Nippon India, Mirae Asset, Canara Robeco, and others.

---

## 2. Source Details

| Attribute | Value |
|-----------|-------|
| Source | kfintech.com / mfs.kfintech.com |
| Format | PDF |
| Date Range | Full history available |
| Coverage | KFintech AMCs (~35% of market) |

---

## 3. PDF Structure

KFintech PDF has sections per mutual fund with the following structure:

```
[AMC Name] - Folio No: XXXXXXXX
[Scheme Name]

Date       Transaction    Amount    Units    Price/Unit
-------------------------------------------------------
01-Jan-24  Purchase       10,000    123.45   81.00
15-Feb-24  Redemption     5,000     61.72    81.00

Current Balance: 61.73 units @ ₹82.50 = ₹5,092.73
```

---

## 4. Field Mapping

| PDF Column | Internal Field | Notes |
|------------|----------------|-------|
| Section Header | scheme_name | Parse from header |
| Folio No | folio_number | Parse from header |
| Date | transaction_date | |
| Transaction | transaction_type | Map to BUY/SELL/DIVIDEND |
| Amount | total_amount | |
| Units | quantity | |
| Price/Unit | price_per_unit | NAV |

---

## 5. Implementation Plan

### 5.1 Backend

**New Files:**
- `backend/app/services/import_parsers/kfintech_parser.py`
- `backend/app/tests/services/test_kfintech_parser.py`
- `backend/app/tests/assets/sample_kfintech.pdf`

**Steps:**
1. Add `pdfplumber` dependency (if not already added)
2. Create `KFintechParser` class extending `BaseParser`
3. Implement multi-section PDF parsing:
   - Detect section headers (AMC + Folio)
   - Parse scheme names
   - Extract transaction tables
4. Handle password-protected PDFs
5. Implement scheme name → AMFI code matching
6. Register parser in `ParserFactory` with key `'kfintech'`
7. Add unit tests

### 5.2 Frontend

- Add "KFintech Statement" option to statement type dropdown
- Support password input for protected PDFs (existing mechanism)

---

## 6. Technical Challenges

| Challenge | Solution |
|-----------|----------|
| Multi-section parsing | Use regex to detect section boundaries |
| Table extraction | Use pdfplumber table detection |
| Password protection | Existing PASSWORD_REQUIRED flow |
| Scheme name variations | Fuzzy matching + alias UI |

---

## 7. Acceptance Criteria

- [x] User can select "KFintech Statement" as statement type
- [x] Parser handles password-protected PDFs
- [ ] Multi-section parsing works correctly (basic support)
- [x] All transaction types mapped
- [x] Scheme names matched to AMFI codes (via alias modal)

---

## 8. Dependencies

- Existing import framework (FR7)
- pdfplumber library
- AMFI asset database
