# Feature Requirement: Advanced Benchmarking

**Feature ID:** FR6.3  
**Title:** Advanced Benchmarking — Hybrid Indices, Risk-Free Rate Overlay & Category Benchmarking  
**Status:** 🔲 In Progress  
**Priority:** P3  
**Version:** v1.2.0  

**User Story:** As an investor, I want to compare my portfolio's performance against hybrid (blended) benchmarks, see a risk-free rate growth overlay, and independently benchmark the equity and debt portions of my portfolio, so I can evaluate my returns with the right context.

---

## 1. Objective

Extend the existing Benchmark Comparison feature (FR6.3, basic single-index comparison ✅ Done in v1.1.0) to support:

1. **FR6.3.1 – Hybrid Benchmarks:** Allow users to select pre-defined blended benchmarks (e.g., CRISIL Hybrid 35+65) which combine equity and debt index data in a specified ratio.
2. **FR6.3.2 – Risk-Free Rate Overlay:** Display an additional line on the benchmark chart representing a configurable risk-free growth rate (default 7% p.a.), answering "what if I just parked money in an FD?"
3. **FR6.3.3 – Category Benchmarking:** Automatically split the portfolio's holdings by asset class and compare each segment against the most appropriate benchmark (Equity → Nifty 50, Debt/FD → 10-Year G-Sec yield).

---

## 2. Scope

### 2.1 In Scope

| Sub-Feature | Description |
|---|---|
| FR6.3.1 Hybrid Benchmarks | Pre-defined hybrid options: "CRISIL Hybrid 35+65" (35% Nifty 50 + 65% CRISIL Short Term Bond), "Balanced 50/50" (50% Nifty 50 + 50% CRISIL Short Term Bond). Blended values computed as weighted average of individual index histories. |
| FR6.3.2 Risk-Free Rate | A dashed line on the chart showing compound growth at a configurable annual rate (default 7%). Uses the same invested-amount timeline as the benchmark simulation. |
| FR6.3.3 Category Benchmarking | Backend classifies transactions into "Equity" (STOCK, MUTUAL_FUND, ETF, ESPP, RSU) and "Debt" (BOND, FIXED_DEPOSIT, RECURRING_DEPOSIT, PPF) categories. Each runs through the existing benchmark simulation independently. Frontend presents a tabbed view: "Overall", "Equity vs Nifty 50", "Debt vs Risk-Free Rate". |

### 2.2 Out of Scope

- User-defined custom blend ratios (future enhancement).
- Dynamic risk-free rate sourced from RBI repo rate API.
- Comparison against MF category averages.

---

## 3. Detailed Requirements

### 3.1 Backend — `benchmark_service.py`

#### 3.1.1 New Parameter: `benchmark_mode`

The existing `calculate_benchmark_performance()` method gains an optional `benchmark_mode` parameter:

| Mode | Behavior |
|---|---|
| `single` (default) | Current behavior — compare against a single index ticker. |
| `hybrid` | Blend two indices at a specified ratio. Requires `hybrid_config`. |
| `category` | Split transactions by equity/debt and run independent simulations. |

#### 3.1.2 `hybrid_config` presets

```python
HYBRID_PRESETS = {
    "CRISIL_HYBRID_35_65": {
        "label": "CRISIL Hybrid 35+65 (Aggressive)",
        "components": [
            {"ticker": "^NSEI", "weight": 0.35},
            {"ticker": "^CRSLDX", "weight": 0.65},  # Fallback: use risk-free rate for debt component
        ]
    },
    "BALANCED_50_50": {
        "label": "Balanced 50/50",
        "components": [
            {"ticker": "^NSEI", "weight": 0.50},
            {"ticker": "^CRSLDX", "weight": 0.50},
        ]
    },
}
```

> **Note:** Since a freely available debt index ticker may not exist in yfinance, the debt component will fall back to a fixed annual rate (e.g., 7% for CRISIL Short Term Bond proxy) if history cannot be fetched. This keeps the feature functional without paid data subscriptions.

#### 3.1.3 Risk-Free Rate Line

- A new field `risk_free_data` in the response containing daily values of a hypothetical investment growing at a configurable annual rate (default 7%).
- Compound interest formula: `risk_free_value = invested_amount * (1 + rate)^(days_held/365)`.
- Computed using the same transaction cash-flow timeline as the benchmark simulation — each investment "deposit" starts compounding from its date.

#### 3.1.4 Category Benchmarking

- New method `calculate_category_benchmark()` that:
  1. Partitions portfolio transactions into `equity_txns` and `debt_txns`.
  2. Runs `calculate_benchmark_performance()` on each partition separately.
  3. Returns `{ equity: {...}, debt: {...} }`.

### 3.2 API Endpoint Changes

#### Existing: `GET /api/v1/portfolios/{portfolio_id}/benchmark-comparison`

**New query parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `benchmark_ticker` | str | `^NSEI` | (existing) Single index ticker. |
| `benchmark_mode` | str | `single` | `single`, `hybrid`, or `category`. |
| `hybrid_preset` | str | `null` | Preset key (e.g., `CRISIL_HYBRID_35_65`). Required when `mode=hybrid`. |
| `risk_free_rate` | float | `7.0` | Annual rate (%) for risk-free overlay line. |

**Updated response shape:**

```json
{
  "portfolio_xirr": 12.5,
  "benchmark_xirr": 10.2,
  "chart_data": [
    {
      "date": "2024-01-01",
      "benchmark_value": 10500,
      "invested_amount": 10000,
      "risk_free_value": 10019.18
    }
  ],
  "risk_free_xirr": 7.0,
  "category_data": {
    "equity": { "portfolio_xirr": 15.0, "benchmark_xirr": 12.0, "benchmark_label": "Nifty 50", "chart_data": [...] },
    "debt":   { "portfolio_xirr": 8.0,  "benchmark_xirr": 7.0,  "benchmark_label": "Risk-Free (7%)", "chart_data": [...] }
  }
}
```

- `risk_free_value` is always included in `chart_data` (for all modes).
- `category_data` is only populated when `benchmark_mode=category`.

### 3.3 Frontend — `BenchmarkComparison.tsx`

#### 3.3.1 UI Enhancements

1. **Benchmark selector dropdown** extended with new options:
   - `Nifty 50`, `Sensex` (existing)
   - `CRISIL Hybrid 35+65`, `Balanced 50/50` (new — triggers `mode=hybrid`)
   - `Category Comparison` (new — triggers `mode=category`)

2. **Risk-Free Rate toggle/input:** A small checkbox "Show Risk-Free Rate (7%)" with an editable rate input, controlling the `risk_free_value` dashed line overlay on the chart.

3. **Category tabs:** When "Category Comparison" is selected, render a tabbed view with "Equity" and "Debt" sub-charts and metric cards.

4. **Chart updates:**
   - Risk-free line: dashed green line (always available when toggled on).
   - Hybrid mode: the "Benchmark" line represents the blended index.

#### 3.3.2 Metric Cards

Extend the current 3-card grid:
- **Your Portfolio XIRR** (existing)
- **Benchmark XIRR** (existing, label changes dynamically)
- **Alpha** (existing)
- **Risk-Free XIRR** (new, shown when risk-free overlay enabled)

---

## 4. Testing Plan

### 4.1 Backend Unit Tests (`test_benchmark_service.py`)

| Test | Description |
|---|---|
| `test_hybrid_benchmark_blended_values` | Mock two index histories, run hybrid mode, assert blended values = weighted avg. |
| `test_hybrid_benchmark_debt_fallback` | Mock equity history only (debt returns empty), assert debt component uses risk-free fallback. |
| `test_risk_free_rate_calculation` | Single BUY transaction, assert `risk_free_value` grows at the expected compound rate. |
| `test_risk_free_rate_custom` | Test custom rate (e.g., 5%) produces different values than default 7%. |
| `test_category_benchmark_splits_correctly` | Portfolio with STOCK + FD transactions, assert equity/debt split and independent simulations. |
| `test_category_benchmark_equity_only` | Portfolio with only STOCK transactions, assert debt category is empty. |

### 4.2 Frontend Unit Tests

| Test | Description |
|---|---|
| `BenchmarkComparison renders hybrid options` | Verify new dropdown options are present. |
| `BenchmarkComparison shows risk-free line` | Toggle risk-free checkbox, verify chart dataset count increases. |
| `BenchmarkComparison renders category tabs` | Select category mode, verify tabs render. |

### 4.3 E2E Tests (`analytics.spec.ts`)

| Test | Description |
|---|---|
| `should display advanced benchmark comparison with risk-free overlay` | Create portfolio, add transactions, navigate to benchmark section, toggle risk-free, verify the line appears on chart. |

---

## 5. Non-Functional Considerations

- **Performance:** Hybrid mode fetches 2 index histories — cache ensures this doesn't double API calls.
- **Graceful Degradation:** If debt index data is unavailable, fall back to risk-free rate for that component. Never block the entire benchmark feature due to missing data.
- **Backward Compatibility:** The API remains fully backward-compatible; existing calls without the new params behave identically.
