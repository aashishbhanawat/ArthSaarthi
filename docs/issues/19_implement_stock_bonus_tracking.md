---
name: '🚀 Feature Request'
about: 'Implement tracking for stock bonus issues'
title: 'feat: Implement tracking for stock bonus issues'
labels: 'enhancement, feature, epic:income-actions'
assignees: ''
---

### 1. User Story

**As a** user whose stocks have issued a bonus,
**I want to** log this corporate action,
**so that** my share quantity is increased and my average cost basis is accurately recalculated.

---

### 2. Functional Requirements

*   [ ] Users must be able to manually add a "bonus" transaction for a specific stock.
*   [ ] The bonus transaction must capture: asset ticker, bonus ratio (e.g., 1:1), and effective date.
*   [ ] When a bonus is logged, the system must automatically create a new "buy" transaction for the bonus shares with a price of zero.
*   [ ] The date of this new zero-cost transaction should be the effective date of the bonus issue.

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1:** Given I hold 10 shares of "STOCK_A" with a total invested amount of $1000, when I log a 1:1 bonus issue, then my holdings should update to 20 shares.
*   [ ] **Scenario 2:** Given the bonus in Scenario 1, when I view my transactions, then a new "buy" transaction for 10 shares at a price of $0 should be visible.
*   [ ] **Scenario 3:** Given the bonus in Scenario 1, when I view my consolidated holdings, then the average cost basis for "STOCK_A" should be correctly recalculated to $50/share ($1000 / 20 shares).

---

### 4. Dependencies

*   This feature depends on the core transaction management system (`FR4.4`).

---

### 5. Additional Context

*   **Requirement ID:** `(FR4.6)`
*   This is a critical corporate action. Creating a zero-cost acquisition for bonus shares is essential for accurate capital gains calculations, as the holding period for bonus shares starts from the bonus issue date.

