# Feature Plan: Historical Price Caching for MF & Bonds (NFR-Analytics-1)

**Feature ID:** NFR-Analytics-1  
**Title:** Historical Price Caching for Non-Stock Assets  
**Priority:** Future (v1.2+)  
**Category:** Non-Functional / Analytics

---

## 1. Problem Statement

### Current Limitations

1. **Portfolio History Chart** - Only shows movement for stocks because:
   - yfinance provides historical prices for stocks
   - MF NAV history not fetched/cached
   - Bond price history not available

2. **Sharpe Ratio Calculation** - Only accurate for stock-heavy portfolios:
   - Requires historical returns data
   - MF/Bond holdings excluded from calculation
   - Results skewed for diversified portfolios

---

## 2. Proposed Solution

### 2.1 Daily Price Snapshot Caching

For each portfolio, cache daily valuations:

```python
class DailyPortfolioSnapshot(Base):
    id: UUID
    portfolio_id: UUID
    snapshot_date: date
    total_value: Decimal
    # Breakdown by asset class
    equity_value: Decimal
    mf_value: Decimal
    bond_value: Decimal
    fd_value: Decimal
    # Individual holdings snapshot (JSON)
    holdings_snapshot: dict
```

### 2.2 MF NAV History

- Fetch from AMFI for last N days on demand
- Cache in database or file cache
- Update daily via background job

### 2.3 Bond Valuation

- Bonds typically valued at face value or purchase price
- For traded bonds, cache NSE closing prices
- For non-traded bonds, use amortized cost method

---

## 3. Implementation Approach

### Phase 1: Daily Snapshot Job
- Background job runs daily
- Captures current portfolio value
- Stores breakdown by asset class

### Phase 2: MF NAV History
- Add AMFI historical NAV endpoint
- Cache NAV data for 1 year
- Backfill on first access

### Phase 3: Enhanced Sharpe Ratio
- Use cached history for calculations
- Include all asset classes
- Per-portfolio calculation

---

## 4. Data Retention

| Data Type | Retention Period |
|-----------|------------------|
| Daily snapshots | 5 years |
| MF NAV history | 1 year rolling |
| Bond prices | 1 year rolling |

---

## 5. Dependencies

- Background job scheduler
- Additional database storage
- AMFI historical NAV API

---

## 6. Related Issues

- Portfolio history chart accuracy
- Sharpe ratio calculation accuracy
- Performance metrics for MF holdings
