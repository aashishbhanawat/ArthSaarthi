# PR Description

## feat(backend): Implement Tax Lot Accounting (Specific Lot Identification)

### Summary
Implements "Specific Lot Identification" for sales, allowing users to optimize tax liability (e.g., specific lot selling vs average cost). This change introduces a `TransactionLink` table to link SELL transactions to specific BUY lots and updates the P&L calculation logic to respect these links.

### Changes
*   **feat(backend):** Added `TransactionLink` model and `TransactionLinkCreate` schema.
*   **feat(backend):** Updated `crud_transaction.py` to implement `get_available_lots` (FIFO fallback) and handle link creation.
*   **feat(backend):** Updated `crud_holding.py` to calculate Realized P&L using specific linked costs.
*   **fix(backend):** Refactored Corporate Action handling (Splits/Bonuses) to use event-sourcing, fixing a double-counting bug.
*   **feat(frontend):** Updated `TransactionFormModal.tsx` to include "Specify Lots" UI with FIFO/LIFO/Highest Cost helpers.
*   **test(e2e):** Added `tax-lot-selection.spec.ts` to verify the UI flow.
*   **test(backend):** Added `test_tax_lot_pnl.py` to verify specific lot P&L calculation.

### Verification
*   **Backend Reviews:** All lint checks passed (`ruff`).
*   **Backend Tests:** All 166 tests passed (including new integration tests).
*   **Frontend Tests:** All 174 tests passed.
*   **E2E Tests:** All 31 tests passed.

### Breaking Changes
*   None. Unlinked transactions fall back to Average Cost (P&L) and FIFO (Availability), preserving behavior for existing data.

### Related Issues
*   Implements FR8.3
*   Fixes Bug 2025-12-14-01 (Corporate Action Double Counting)
