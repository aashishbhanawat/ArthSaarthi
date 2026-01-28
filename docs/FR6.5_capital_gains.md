# FR6.5: Capital Gains Reporting - Detailed Requirements

**Version:** 1.0  
**Date:** 2026-01-19  
**Target Release:** v1.2.0 (March 1, 2026)

---

## 1. Overview

The Capital Gains feature enables users to:
1. View realized capital gains/losses with STCG/LTCG classification
2. Estimate tax liability based on current Indian tax rules
3. Export structured reports for tax filing or CA consultation

---

## 2. Scope

### 2.1 Asset Types Covered

| # | Asset Type | Category | Notes |
|---|------------|----------|-------|
| 1 | Indian Stocks | Listed Equity | NSE/BSE traded |
| 2 | Indian ETFs | Listed Equity | Same as stocks |
| 3 | MF Equity | Mutual Fund | 65%+ equity allocation |
| 4 | MF Debt | Mutual Fund | <65% equity allocation |
| 5 | MF Hybrid | Mutual Fund | Treat as per category |
| 6 | MF Overseas | Mutual Fund | International/US funds |
| 7 | Bonds (NCD) | Listed Debt | Listed on exchange |
| 8 | Bonds (T-Bill) | Government | Treasury bills |
| 9 | SGB | Government | Sovereign Gold Bonds |
| 10 | Foreign Stocks | Unlisted | US stocks via ESPP/RSU |
| 11 | FD | Fixed Income | Interest is income, not CG |
| 12 | RD | Fixed Income | Interest is income, not CG |
| 13 | PPF | Government | Exempt, no CG |

### 2.2 Out of Scope (v1.2.0)
- Intraday gains calculation
- Speculative income classification
- F&O (futures & options)

---

## 3. Tax Rules by Asset Type

### FR6.5.1: Holding Period Thresholds (Verified)

| Asset Type | LTCG Threshold | Effective | Notes |
|------------|----------------|-----------|-------|
| Listed Equity/ETF | >12 months | All | Verified |
| MF Equity (65%+) | >12 months | All | Verified |
| MF Debt/Other | >24 months* | Post-Jul 2024 | *If not Sec 50AA (Deemed STCG) |
| Listed Bonds | >12 months | All | Verified |
| SGB (Secondary Mkt)| >12 months | Jul 2024 | Listed Security rule |
| SGB (Physical/Unlisted)| >24 months | Jul 2024 | If unlisted/physical gold |
| Unlisted/Foreign | >24 months | All | Verified |
| Immovable Prop. | >24 months | All | Verified |

*> Note: For transfers before 23-07-2024, the general threshold was 36 months.*

### FR6.5.2: Tax Rates (Verified)

| Asset Type | STCG Rate | LTCG Rate | LTCG Exemption |
|------------|-----------|-----------|----------------|
| Listed Equity/ETF | 20% | 12.5% | ₹1.25L p.a. |
| MF Equity | 20% | 12.5% | ₹1.25L p.a. |
| MF Debt (Sec 50AA)| Slab rate | N/A | None |
| Listed Bonds | Slab rate | 12.5% | None |
| SGB (Maturity/RBI)| N/A | Exempt | 100% exempt |
| SGB (Secondary Mkt)| Slab rate | 12.5% | None |
| Physical Gold | Slab rate | 12.5% | None |
| Unlisted/Foreign | Slab rate | 12.5% | None |

### FR6.5.3: Grandfathering (Equity Only)

For listed equity/MF acquired before Feb 1, 2018:
- **Cost of Acquisition** = MAX(Actual Buy Price, Fair Market Value on Jan 31, 2018)
- **Fair Market Value (FMV)** = Highest trading price on Jan 31, 2018

**Corporate Action Adjustments:**
1.  **Bonus Shares:**
    *   *Issued pre-31 Jan 2018:* Cost is FMV on 31 Jan 2018.
    *   *Issued post-31 Jan 2018:* Cost is ZERO. Grandfathering does not apply.
2.  **Stock Splits:**
    *   FMV of Jan 31, 2018 is adjusted proportionally to the split ratio.
    *   *Example:* 1:1 split post-2018 → New FMV = Old FMV / 2.
3.  **Demergers:**
    *   **Logic:** Reuse existing `details.total_cost_allocated` field from Demerger transaction.
    *   **Demerged Company Cost:** Reduced by allocated amount. Ratio = (Original Cost - Allocated Cost) / Original Cost.
    *   **Resulting Company Cost:** Derived from allocated amount.
    *   **Grandfathering:** Jan 31 2018 FMV is adjusted using the same ratio.
    *   *Note:* Ensure `capital_gains_service` logic matches `HoldingDetailModal.tsx` calculation.

---

## 4. Functional Requirements

### FR6.5.4: Capital Gains View Page

**FR6.5.4.1:** The system must provide a dedicated "Capital Gains" page accessible from the main navigation.

**FR6.5.4.2:** The page must display summary cards showing:
- Total Short-Term Capital Gains (STCG)
- Total Long-Term Capital Gains (LTCG)
- Total STCG Tax Estimate
- Total LTCG Tax Estimate
- Net Tax Liability

**FR6.5.4.3:** The page must allow filtering by:
- Financial Year (e.g., FY 2025-26, FY 2024-25)
- Portfolio (All / specific portfolio)
- Asset Type (All / Equity / Debt / Foreign)

**FR6.5.4.4:** The page must display a detailed table of all realized gains with columns:
- Asset Name / Ticker
- Asset Type
- Buy Date
- Sell Date
- Holding Days
- Quantity
- Buy Price (per unit)
- Sell Price (per unit)
- Total Proceeds
- Cost of Acquisition (with grandfathering if applicable)
- Capital Gain/Loss
- Gain Type (STCG / LTCG)
- Tax Rate Applied

**FR6.5.4.5:** The table must be sortable by any column and searchable by asset name/ticker.

---

### FR6.5.5: Capital Gains Calculation

**FR6.5.5.1:** Capital gain must be calculated as:
```
Capital Gain = (Sell Price × Quantity) - (Adjusted Cost × Quantity) - Fees
```

**FR6.5.5.2:** Adjusted Cost must account for:
- Original buy price
- Grandfathering adjustment (for eligible equity)
- Demerger cost adjustments
- STT (Securities Transaction Tax) paid

**FR6.5.5.3:** For partial sells, the system must use FIFO (First-In-First-Out) unless user has specified Tax Lot selection (FR4.4.3).

**FR6.5.5.4:** For each sell transaction, the system must:
- Identify matched buy lots (via TransactionLink)
- Calculate holding period for each lot
- Classify as STCG or LTCG based on threshold
- Apply grandfathering if eligible

---

### FR6.5.6: Tax Estimation

**FR6.5.6.1:** Tax estimate must be calculated using rates from FR6.5.2.

**FR6.5.6.2:** For gains subject to slab rate, the system must:
- Allow user to input their estimated income slab (optional)
- Default to highest slab (30%) if not specified

**FR6.5.6.3:** LTCG exemption of ₹1.25 lakh must be applied to eligible equity gains:
- Pool all equity LTCG for the FY
- Exempt first ₹1.25 lakh
- Tax remaining at 12.5%

**FR6.5.6.5:** Display specific warning "Complex corporate action involved. Please consult a tax professional to verify Cost of Acquisition" for any gain calculation involving Bonus, Split, or Demerger.

---

### FR6.5.7: Unrealized Gains View

**FR6.5.7.1:** The system must display unrealized capital gains alongside realized gains.

**FR6.5.7.2:** Unrealized gains must show:
- Current holding classification (would be STCG / would be LTCG if sold today)
- Estimated tax impact if sold

**FR6.5.7.3:** This helps users make tax-optimized sell decisions.

---

### FR6.5.8: Export & Reports

**FR6.5.8.1:** The system must support exporting capital gains in CSV format with all columns from FR6.5.4.4.

**FR6.5.8.2:** The system must support exporting in PDF format with:
- Summary section
- Detailed transaction table
- Footer with disclaimers

**FR6.5.8.3:** Export filenames must follow pattern: `CapitalGains_FY{YEAR}_{Portfolio}_{Date}.{ext}`

**FR6.5.8.4:** The export must be structured to facilitate ITR-2 Schedule CG filing (informational only).

---

### FR6.5.9: Advance Tax Reporting (ITR-2 Schedule CG Format)

**FR6.5.9.1:** The Capital Gains report must include a detailed matrix breakdown matching the ITR-2 "Capital Gains" schedule.

**FR6.5.9.2:** **Columns (Time Periods):**
1.  Up to 15/6
2.  16/6 to 15/9
3.  16/9 to 15/12
4.  16/12 to 15/3
5.  16/3 to 31/3

**FR6.5.9.3:** **Rows (Tax Categories - Steady State):**
1.  Short-term capital gains taxable at 20% (Equity/Equity MF)
2.  Short-term capital gains taxable at applicable rates (Slab - Debt/Gold/Other)
3.  Long-term capital gains taxable at 12.5% (Equity/Gold/Immovable/Foreign)
4.  Long-term capital gains taxable at applicable rates / Other (Residual)

**FR6.5.9.4:** The system must bucket each transaction into the correct Period (by Sell Date) and correct Category (by Asset Type + Tax Rule).

### FR6.5.10: Schedule 112A Reporting (Grandfathered Equity)

**FR6.5.10.1:** The system must generate a detailed report for Schedule 112A (LTCG on Equity) with the following specific columns:
1.  **Acquisition Date Filter:** Acquired (On or before / after 31st Jan 2018)
2.  **Transfer Date Filter:** Transferred (Before / on or After 23rd July 2024)
3.  **ISIN Code**
4.  **Name of Share/Unit**
5.  **No. of Shares/Units**
6.  **Sale Price per Share/Unit**
7.  **Full Value of Consideration**
8.  **Cost of Acquisition (without indexation)**
9.  **FMV per share as on 31st Jan 2018**
10. **Total FMV**
11. **Cost of Acquisition (Computed per Sec 55(2)(ac))**
12. **Expenditure involved in transfer**
13. **Total Deductions**
14. **Balance (Capital Gain)**

**FR6.5.10.2:** This report is mandatory for verifying Grandfathering calculations.

---

## 5. User Stories

### US1: View FY Capital Gains
> As a user, I want to see all my realized gains for the current financial year so I can estimate my tax liability.

### US2: Classify STCG vs LTCG
> As a user, I want my gains automatically classified as short-term or long-term based on holding period so I know which tax rate applies.

### US3: Grandfathering for Old Holdings
> As a user who bought equity before 2018, I want the system to apply grandfathering rules so my cost basis is correctly adjusted.

### US4: Estimate Tax
> As a user, I want to see an estimated tax amount so I can plan my finances.

### US5: Export for CA
> As a user, I want to export my capital gains report so I can share it with my chartered accountant.

### US6: Tax-Loss Harvesting Planning
> As a user, I want to see unrealized losses so I can decide to book them before year-end to offset gains.

---

## 6. UI/UX Considerations

### 6.1 Page Layout
- Summary cards at top (responsive grid)
- Filter bar below summary
- Full-width data table with pagination
- Export button in header

### 6.2 Color Coding
- Green for gains, Red for losses
- Badge for STCG (orange) vs LTCG (green)

### 6.3 Mobile Responsive
- Cards stack vertically
- Table scrolls horizontally

---

## 7. Edge Cases

| Scenario | Handling |
|----------|----------|
| No realized gains in FY | Show empty state with message |
| Buy date missing | Use earliest available transaction date |
| Grandfathering price unavailable | Use original buy price, show warning |
| Demerger reduces cost basis | Apply cost reduction from demerger details |
| Sell-to-cover RSU | Treat as exercise + immediate sell |
| ESPP discount | Use FMV at purchase as cost basis |

---

## 8. Technical Dependencies

- Existing `TransactionLink` model for buy-sell matching
- Existing `crud_analytics.py` for P&L calculation
- New service: `capital_gains_service.py`
- Historical price API for Jan 31, 2018 prices

---

## 9. Testing Requirements

### 9.1 Unit Tests
- [ ] STCG classification (each asset type)
- [ ] LTCG classification (each asset type)
- [ ] Grandfathering calculation (multiple scenarios)
- [ ] Tax estimation accuracy
- [ ] Partial sell with FIFO

### 9.2 Integration Tests
- [ ] API returns correct summary
- [ ] Filtering works correctly
- [ ] Export produces valid file

### 9.3 Manual Tests
- [ ] Verify calculations against known tax scenarios
- [ ] End-to-end user flow
- [ ] PDF readability

---

## 10. Acceptance Criteria

- [ ] Capital Gains page loads in <2 seconds
- [ ] All 13 asset types handled correctly
- [ ] Grandfathering applied automatically for eligible equity
- [ ] CSV export contains all required columns
- [ ] Tax estimates match manual calculations (within 1%)
- [ ] Disclaimer displayed on estimates and exports
