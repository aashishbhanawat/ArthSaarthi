# Feature Plan: ICICI Direct MF PDF Parser (FR7.1.8)

**Feature ID:** FR7.1.8  
**Title:** ICICI Direct MF PDF Import Parser  
**Priority:** P3  
**Parent FR:** FR7 (Automated Data Import)

---

## 1. Objective

Enable users to import Mutual Fund transactions from ICICI Direct PDF statements.

---

## 2. Source Details

| Attribute | Value |
|-----------|-------|
| Source | ICICI Direct app |
| Format | PDF |
| Date Range | Full history |
| Coverage | MF purchased via ICICI Direct |

---

## 3. PDF Structure

```
[AMC Name]                    Folio No : XXXXXXXX/XX
[Scheme Name]

Opening Balance As On [Date]    [Units]

Date        TxnNo      Type       Price    Units      Gross    TDS  STT  Net
---------------------------------------------------------------------------
11-Mar-2022 118491072  Dividend   22.98    2,039.63   46,871   0    0    0

Current Unit Balance As On [Date]  [Price]  [Units]  [Value]
```

---

## 4. Field Mapping

| PDF Column | Internal Field |
|------------|----------------|
| Section Header (AMC) | amc_name |
| Section Header (Scheme) | scheme_name |
| Folio No | folio_number |
| Date | transaction_date |
| Type | transaction_type |
| Price | price_per_unit (NAV) |
| Units | quantity |
| Net Amount | total_amount |

**Transaction Type Mapping:**
| ICICI Type | Our Type |
|------------|----------|
| Purchase / SIP | BUY |
| Redemption | SELL |
| Dividend | DIVIDEND |
| Switch In | BUY |
| Switch Out | SELL |

---

## 5. Implementation Plan

### 5.1 Backend

**New Files:**
- `backend/app/services/import_parsers/icici_mf_parser.py`
- `backend/app/tests/services/test_icici_mf_parser.py`
- `backend/app/tests/assets/sample_icici_mf.pdf`

**Steps:**
1. Use pdfplumber for text extraction
2. Implement section-based parsing (per AMC/Fund)
3. Handle multi-line scheme names
4. Scheme name → AMFI code matching
5. Register in ParserFactory with key `'icici_mf'`

---

## 6. Priority Note

**Priority P3** because:
- CAMS Excel (P1) likely covers same AMCs with easier parsing
- Only needed if user exclusively uses ICICI Direct and doesn't have CAMS access

---

## 7. Acceptance Criteria

- [ ] User can select "ICICI Direct MF" as statement type
- [ ] Multi-section PDF parsing works correctly
- [ ] All transaction types mapped
- [ ] Scheme names matched to AMFI codes
