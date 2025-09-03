# Feature Plan: Holdings Table Redesign

**Status: 📝 Planned**
---
**Feature ID:** FR4.7.2
**Title:** Redesign Holdings View with Collapsible Sections
**User Story:** As a user, I find the single holdings table confusing when viewing different asset types. I want to see my assets grouped by class with relevant columns for each, so I can understand my portfolio at a glance.

---

## 1. Objective

The current single-table view for all holdings uses generic "Key Metric" columns, which is confusing and not scalable. This plan details a full UI/UX revamp to group assets by class into collapsible sections, each with its own dedicated, relevant columns.

---

## 2. UI/UX Redesign: Sectioned Holdings Table

The `HoldingsTable.tsx` component will be refactored to render sections instead of a single flat table.

### 2.1. Mockup UI

The main holdings view will be redesigned to use an accordion or collapsible section layout. Each section will display a summary and have columns tailored to that specific asset class.

```
  [v] Equities & Mutual Funds (Total Value: ₹8,78,349.99)
  | Asset      | Qty | Avg. Price | LTP      | Value      | Day's P&L | Unrealized P&L |
  |------------|-----|------------|----------|------------|-----------|----------------|
  | INFY       | 25  | ₹392.81    | ₹1479.10 | ₹36,977.50 | -₹490.00  | +₹27,157.23    |
  | ...        | ... | ...        | ...      | ...        | ...       | ...            |

  [v] Deposits (Total Value: ₹117,007.77)
  | Asset        | Type | Interest Rate | Maturity   | Invested   | Current Value |
  |--------------|------|---------------|------------|------------|---------------|
  | HDFC Bank FD | FD   | 7.50%         | 2026-03-12 | ₹100,000   | ₹104,557.77   |
  | SBI RD       | RD   | 6.50%         | 2027-01-01 | ₹12,000    | ₹12,450.00    |

  [v] Bonds & Debentures (Total Value: ₹10,500.00)
  | Asset        | ISIN         | Coupon | Maturity   | Invested   | Mkt. Value    |
  |--------------|--------------|--------|------------|------------|---------------|
  | NHAI Bond    | INE906B07CB9 | 8.00%  | 2030-01-01 | ₹10,100    | ₹10,500.00    |

  [v] Government Schemes (Total Value: ₹100,000.00)
  | Asset       | Institution     | Opening Date | Current Balance |
  |-------------|-----------------|--------------|-----------------|
  | PPF Account | State Bank of India | 2020-01-01   | ₹100,000.00     |
```

### 2.2. User Flow

1.  The user navigates to their portfolio detail page.
2.  The holdings are displayed in the new sectioned view, with all sections expanded by default.
3.  The user can click on a section header to collapse or expand it. The state (open/closed) is remembered during their session.
4.  Clicking the "Add New Asset" button will present options grouped by category (e.g., "Equity/MF", "Deposits", "Bonds").


---
## 3. Frontend Implementation Details
*   Refactor `HoldingsTable.tsx` to group the `holdings` array by asset class before rendering.
*   Create new, specialized row components for each section (e.g., `EquityHoldingRow`, `DepositHoldingRow`) with strongly-typed props to ensure the correct data is shown in the correct column.
*   Use a UI library component (e.g., from Radix UI, Headless UI, or a custom implementation) to create the collapsible/accordion sections.
*   The state of each section (collapsed/open) should be persisted in local state.

---
## 4. Backend Requirements

*   The main `GET /holdings` endpoint must be updated to return data in a way that is easily groupable on the frontend. Adding a `group` or `category` field to each holding object in the response would be ideal.
    *   Example: `{"asset_name": "...", "asset_type": "STOCK", "group": "EQUITIES", ...}`

---
## 5. Testing Plan
*   **E2E Tests:** A new Playwright test will be created to verify the new collapsible UI. It will assert that:
    *   Each section exists.
    *   Each section contains the correct columns.
    *   Assets are rendered in the correct section.
    *   Sections can be collapsed and expanded.
*   **Frontend Component Tests:** The new sectioned `HoldingsTable` and its child row components will be tested to ensure they render correctly based on different sets of mock holdings data.
