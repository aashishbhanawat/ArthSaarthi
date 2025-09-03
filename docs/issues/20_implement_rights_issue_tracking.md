---
name: '🚀 Feature Request'
about: 'Implement tracking for rights issues'
title: 'feat: Implement tracking for rights issues'
labels: 'enhancement, feature, epic:income-actions'
assignees: ''
---

### 1. User Story

**As a** shareholder who has subscribed to a rights issue,
**I want to** log my participation in the rights issue,
**so that** my new shares are added at the correct issue price and my overall holdings are accurately reflected.

---

### 2. Functional Requirements

*   [ ] Users must be able to manually add a "rights" transaction for a specific stock.
*   [ ] The rights transaction must capture: asset ticker, number of shares subscribed, issue price, and payment date.
*   [ ] When a rights issue is logged, the system must automatically create a new "buy" transaction for the subscribed shares at the specified issue price and date.

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1:** Given I hold "STOCK_A", when I log that I subscribed to 5 new shares via a rights issue at $90/share, then a new "buy" transaction for 5 shares at $90 should be created.
*   [ ] **Scenario 2:** Given the action in Scenario 1, when I view my consolidated holdings for "STOCK_A", then the total quantity and average cost basis should be updated to reflect the new purchase.

---

### 4. Dependencies

*   This feature depends on the core transaction management system (`FR4.4`).

---

### 5. Additional Context

*   **Requirement ID:** `(FR4.6)`
*   This feature adds another type of manual corporate action entry. It is distinct from a bonus (which is zero-cost) and a split (which adjusts existing lots). A rights issue is effectively a preferential new purchase.

