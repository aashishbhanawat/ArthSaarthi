# Feature Plan: Capital Gains View (FR6.5)

**Feature ID:** FR6.5  
**Title:** Capital Gains View for Tax Planning  
**Priority:** P3  
**GitHub Issue:** #194

---

## 1. Objective

Display unrealized and realized capital gains with short-term vs long-term classification to help users with tax planning.

---

## 2. Design

### Classification (India Tax Law)
- **Short-term:** Held < 12 months (for listed equity)  
- **Long-term:** Held ≥ 12 months

### Summary View

| Metric | Short-Term | Long-Term | Total |
|--------|------------|-----------|-------|
| Unrealized Gains | ₹X | ₹Y | ₹Z |
| Unrealized Losses | ₹X | ₹Y | ₹Z |
| Realized Gains | ₹X | ₹Y | ₹Z |
| Realized Losses | ₹X | ₹Y | ₹Z |

---

## 3. Technical Design

### Backend: New Endpoint

`GET /api/v1/portfolios/{id}/capital-gains?tax_year=2024`

Response:
```json
{
  "unrealized": {
    "short_term": { "gains": 1000, "losses": -200 },
    "long_term": { "gains": 5000, "losses": -100 }
  },
  "realized": {
    "short_term": { "gains": 500, "losses": 0 },
    "long_term": { "gains": 2000, "losses": -300 }
  },
  "holdings_breakdown": [
    {
      "asset_name": "RELIANCE",
      "holding_period_days": 400,
      "term": "long_term",
      "cost_basis": 10000,
      "current_value": 15000,
      "unrealized_gain": 5000
    }
  ]
}
```

### Frontend: CapitalGainsCard Component

- Summary table with short/long-term breakdown
- Collapsible holdings detail
- Color coding for gains (green) / losses (red)

---

## 4. Files to Modify

| File | Changes |
|------|---------|
| `backend/app/crud/crud_analytics.py` | Add `get_capital_gains()` method |
| `backend/app/schemas/analytics.py` | Add `CapitalGainsResponse` schema |
| `backend/app/api/v1/endpoints/analytics.py` | Add endpoint |
| `frontend/src/components/Portfolio/CapitalGainsCard.tsx` | NEW - Summary display |
| `frontend/src/types/analytics.ts` | Add `CapitalGains` type |
| `frontend/src/services/portfolioApi.ts` | Add API call |

---

## 5. Acceptance Criteria

- [ ] Show unrealized gains breakdown by short/long-term
- [ ] Show realized gains breakdown by short/long-term  
- [ ] Separate gains and losses
- [ ] Holdings detail view
- [ ] Works in Portfolio Analytics section
