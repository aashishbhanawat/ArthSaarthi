---
name: '🚀 Feature Request'
about: 'Implement tracking for Recurring Deposits (RDs)'
title: 'feat: Implement tracking for Recurring Deposits (RDs)'
labels: 'enhancement, feature, epic:advanced-assets'
assignees: ''
---

### 1. User Story

**As a** user who makes systematic investments,
**I want to** track my Recurring Deposits (RDs) within the application,
**so that** I can monitor my regular savings and see their projected growth.

---

### 2. Functional Requirements

*   [ ] Users must be able to add a new Recurring Deposit asset.
*   [ ] The system must capture key RD details: institution name, monthly installment amount, interest rate, start date, and tenure (in months) or maturity date.
*   [ ] The system must calculate the total amount invested to date based on the start date and monthly installment.
*   [ ] The system must calculate the projected maturity value based on the RD compounding formula.
*   [ ] RDs must be displayed correctly in the main holdings table with relevant metrics (e.g., Monthly Installment, Maturity Date).

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1:** Given I am on my portfolio page, when I use the "Add New Asset" flow and select "Recurring Deposit", then I should see a form to enter all RD details.
*   [ ] **Scenario 2:** Given I have created an RD, when I view my holdings, then the current value should reflect the total principal deposited so far, and the maturity value should be correctly projected.

---

### 4. Dependencies

*   This feature depends on the completion of the foundational "Advanced Asset Support" framework (e.g., the FD implementation).

---

### 5. Additional Context

*   **Requirement ID:** `(FR4.3.3)`
*   This is a sub-issue under the "Advanced Asset Support" epic and should be implemented after Fixed Deposits.