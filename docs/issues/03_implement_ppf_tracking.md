---
name: '🚀 Feature Request'
about: 'Implement tracking for Public Provident Fund (PPF)'
title: 'feat: Implement tracking for Public Provident Fund (PPF)'
labels: 'enhancement, feature, epic:advanced-assets'
assignees: ''
---

### 1. User Story

**As a** user with long-term savings goals,
**I want to** track my Public Provident Fund (PPF) account,
**so that** I have a complete view of my retirement and tax-saving instruments.

---

### 2. Functional Requirements

*   [ ] Users must be able to add a new PPF asset, capturing details like institution name, account number, and opening date.
*   [ ] The value of the PPF asset will be user-driven via a `current_balance` field.
*   [ ] Users must be able to log contributions to their PPF account using a new `CONTRIBUTION` transaction type.
*   [ ] Creating a `CONTRIBUTION` transaction must automatically update the `current_balance` of the PPF asset.
*   [ ] The PPF asset must be displayed correctly in the main holdings table, showing its current balance and maturity date (15 years from opening date).

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1:** Given I am on my portfolio page, when I use the "Add New Asset" flow and select "PPF", then I should see a form to enter my PPF account details.
*   [ ] **Scenario 2:** Given I have a PPF asset, when I add a "Contribution" transaction for it, then the `current_balance` of the PPF holding in the table should increase by the contribution amount.

---

### 4. Dependencies

*   This feature depends on the foundational "Advanced Asset Support" framework (e.g., the FD implementation).

---

### 5. Additional Context

*   **Requirement ID:** `(FR4.3.3)`
*   For the MVP, the complex official interest calculation will be deferred. The value will be driven by user updates and contributions.