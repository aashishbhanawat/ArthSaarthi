# Feature Plan: Corporate Actions Manual Entry (FR4.6.2)

**Feature ID:** FR4.6.2  
**Title:** Manual Corporate Action Entry  
**Priority:** P2  
**Parent FR:** FR4.6 (Corporate Actions)

---

## 1. Objective

Enable users to manually log corporate actions (mergers, demergers, ticker renames) that affect their holdings, ensuring accurate portfolio tracking when importing historical data.

---

## 2. Scope

### In Scope
- Manual entry of merger/demerger/rename transactions
- Automatic adjustment of holdings based on conversion ratios
- Support for common Indian market scenarios

### Out of Scope (Future)
- Automated detection from official sources
- Historical corporate action database

---

## 3. Supported Action Types

| Action Type | Description | Example |
|-------------|-------------|---------|
| **Merger** | Multiple companies merge into one | HDFC + HDFC Bank → HDFCBANK |
| **Demerger** | Company splits into multiple | Reliance → RIL + JIOFIN |
| **Ticker Rename** | Symbol change only | VEDL → VEDANTA |

---

## 4. Data Model

### New Transaction Type Extension

```python
class TransactionType(str, Enum):
    # Existing types
    BUY = "BUY"
    SELL = "SELL"
    # ...
    
    # New corporate action types
    MERGER = "MERGER"
    DEMERGER = "DEMERGER"
    RENAME = "RENAME"
```

### Corporate Action Details (JSON in transaction.details)

```json
// Merger Example
{
  "action_type": "MERGER",
  "record_date": "2023-07-01",
  "old_tickers": ["HDFC", "HDFCBANK"],
  "new_ticker": "HDFCBANK",
  "conversion_ratios": {
    "HDFC": 1.68,      // 1 HDFC = 1.68 HDFCBANK
    "HDFCBANK": 1.0    // 1 HDFCBANK = 1 HDFCBANK
  }
}

// Demerger Example
{
  "action_type": "DEMERGER",
  "record_date": "2023-07-20",
  "old_ticker": "RELIANCE",
  "new_tickers": ["RELIANCE", "JIOFIN"],
  "ratios": {
    "RELIANCE": 1.0,   // Keep existing shares
    "JIOFIN": 1.0      // 1 new share per old share
  }
}
```

---

## 5. User Interface

### 5.1 Entry Point
- New option in "Add Transaction" dropdown: "Corporate Action"
- Or dedicated "Corporate Actions" section in portfolio

### 5.2 Form Fields

**For Merger:**
- Record Date
- Old Ticker(s) - multi-select from holdings
- New Ticker - asset lookup
- Conversion Ratio for each old ticker

**For Demerger:**
- Record Date
- Old Ticker - select from holdings
- New Ticker(s) - asset lookup
- Ratio for each new ticker

**For Rename:**
- Effective Date
- Old Ticker - select from holdings
- New Ticker - asset lookup

---

## 6. Processing Logic

### Merger
1. Calculate total equivalent shares in new ticker
2. Mark old holdings as "merged"
3. Create new holding with aggregated shares
4. Preserve cost basis (sum of all merged holdings)

### Demerger
1. Keep original holding
2. Create new holding(s) for demerged shares
3. Allocate cost basis proportionally (user can adjust)

### Rename
1. Update ticker_symbol on existing asset
2. Or create alias mapping

---

## 7. Acceptance Criteria

- [x] User can create merger transaction
- [x] User can create demerger transaction
- [x] User can create rename transaction
- [x] Holdings recalculated correctly after action
- [x] Cost basis preserved/allocated appropriately
- [x] Transaction appears in history
- [x] Original acquisition dates preserved for XIRR
- [x] Multi-entity demergers handled correctly
- [x] No holdings on record date rejects transaction
- [x] Asset lookup enabled for new ticker

---

## 8. Import Behavior Note

When importing transactions with old/unrecognized tickers:
- Import skips unrecognized tickers (existing behavior)
- User must manually create corporate action to map old → new
- Documentation explains this workflow
