---
name: '🚀 Feature Request'
about: 'Implement tracking for National Pension System (NPS)'
title: 'feat: Implement tracking for National Pension System (NPS)'
labels: 'enhancement, feature, epic:advanced-assets'
assignees: ''
---

### 1. User Story

**As a** user investing for retirement,
**I want to** track my National Pension System (NPS) account within the application,
**so that** I can monitor this critical component of my long-term savings portfolio.

---

### 2. Functional Requirements

*   [ ] Users must be able to add a new NPS asset, capturing details like PRAN, fund manager, and scheme preferences (e.g., Tier I, Tier II).
*   [ ] The value of the NPS asset will be user-driven via a `current_balance` field.
*   [ ] Users must be able to log contributions to their NPS account using the `CONTRIBUTION` transaction type.
*   [ ] Creating a `CONTRIBUTION` transaction must automatically update the `current_balance` of the NPS asset.
*   [ ] The NPS asset must be displayed correctly in the main holdings table, showing its current balance.

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1:** Given I am on my portfolio page, when I use the "Add New Asset" flow and select "NPS", then I should see a form to enter my NPS account details.
*   [ ] **Scenario 2:** Given I have an NPS asset, when I add a "Contribution" transaction for it, then the `current_balance` of the NPS holding in the table should increase by the contribution amount.

---

### 4. Dependencies

*   This feature is a prerequisite for the eNPS statement import parser (`FR7.1.3`).

---

### 5. Additional Context

*   **Requirement ID:** `(FR4.3.5)`
*   For the MVP, the complex NAV-based valuation across different fund choices will be deferred. The value will be driven by user updates and contributions.