---
name: '🚀 Feature Request'
about: 'Implement tracking for stock splits'
title: 'feat: Implement tracking for stock splits'
labels: 'enhancement, feature, epic:income-actions'
assignees: ''
---

### 1. User Story

**As a** user whose stocks have undergone a split,
**I want to** log this corporate action,
**so that** my share quantity and cost basis are automatically and accurately adjusted.

---

### 2. Functional Requirements

*   [ ] Users must be able to manually add a "split" transaction for a specific stock.
*   [ ] The split transaction must capture: asset ticker, split ratio (e.g., 2 for 1), and effective date.
*   [ ] When a split is logged, the system must adjust the quantity of all existing buy transactions for that asset that occurred before the split date.
*   [ ] The system must also adjust the purchase price of those same transactions to keep the total invested amount for each transaction constant.

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1:** Given I hold 10 shares of "STOCK_A" bought at $100/share, when I log a 2-for-1 stock split, then my holdings should update to 20 shares and the average cost basis should become $50/share.
*   [ ] **Scenario 2:** Given the split in Scenario 1, when I view the drill-down for "STOCK_A", then the original buy transaction should now show a quantity of 20 and a price of $50, while the total invested amount remains $1000.

---

### 4. Dependencies

*   This feature depends on the core transaction management system (`FR4.4`).

---

### 5. Additional Context

*   **Requirement ID:** `(FR4.6)`
*   This is a critical corporate action. The logic must adjust the cost basis of individual buy lots (FIFO) correctly to ensure accurate capital gains reporting in the future.
*   The initial implementation will focus on manual entry. Automatic tracking can be a future enhancement.

