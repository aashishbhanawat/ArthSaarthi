# Feature Plan: Dividend Statement Import (FR7.1.9)

**Feature ID:** FR7.1.9  
**Title:** Dividend Statement Import (Zerodha & ICICI)  
**Priority:** P2  
**Parent FR:** FR7 (Automated Data Import)

---

## 1. Objective

Enable users to import dividend statements from brokers to automatically log dividend income transactions.

---

## 2. Sources

### 2.1 Zerodha Dividend Statement

| Attribute | Value |
|-----------|-------|
| Source | console.zerodha.com → Reports → Dividends |
| Format | Excel (XLSX) |
| Contains | Stock symbol, dividend date, amount, quantity held |

**Expected Columns (to be confirmed):**
- Symbol / ISIN
- Dividend Date
- Record Date
- Dividend per Share
- Quantity Held
- Total Dividend Amount
- Tax Deducted (TDS)
- Net Amount

### 2.2 ICICI Direct Dividend Statement

| Attribute | Value |
|-----------|-------|
| Source | ICICI Direct app / website |
| Format | PDF |
| Contains | Similar dividend details |

---

## 3. Implementation

### 3.1 Backend

**New Files:**
- `backend/app/services/import_parsers/zerodha_dividend_parser.py`
- `backend/app/services/import_parsers/icici_dividend_parser.py`
- Test files and sample statements

**Transaction Mapping:**
Each dividend row creates a DIVIDEND transaction:
```python
Transaction(
    asset_id=matched_asset.id,
    transaction_type=TransactionType.DIVIDEND,
    transaction_date=dividend_date,
    quantity=shares_held,  # Number of shares that received dividend
    price_per_unit=dividend_per_share,
    # total = quantity * price_per_unit
)
```

### 3.2 Frontend

- Add "Zerodha Dividend" and "ICICI Dividend" to statement type dropdown

---

## 4. Acceptance Criteria

- [ ] User can import Zerodha dividend XLSX
- [ ] User can import ICICI dividend PDF
- [ ] Dividend transactions created correctly
- [ ] TDS amounts recorded (if available)
- [ ] Duplicate dividend detection

---

## 5. Notes

- Dividends may already be partially tracked via manual entry
- Import should detect and flag potential duplicates
