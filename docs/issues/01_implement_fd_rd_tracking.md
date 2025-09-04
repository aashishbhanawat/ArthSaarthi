---
name: '🚀 Feature Request'
about: 'Implement tracking for Fixed Deposits (FDs)'
title: 'feat: Implement tracking for Fixed Deposits (FDs)'
labels: 'enhancement, feature, epic:advanced-assets'
assignees: ''
---

### 1. User Story

**As a** user with diverse investments,
**I want to** track my Fixed Deposits (FDs) within the application,
**so that** I can have a complete, holistic view of my entire investment portfolio in one place.

---

### 2. Functional Requirements

*   [ ] Users must be able to add a new Fixed Deposit asset.
*   [ ] The system must capture key FD details: institution name, principal amount, interest rate, start date, maturity date, payout type (reinvestment/payout), and compounding frequency.
*   [ ] The system must calculate the current value of a reinvestment-type FD based on compound interest.
*   [ ] The system must display the principal amount as the current value for a payout-type FD.
*   [ ] FDs must be displayed correctly in the main holdings table with relevant metrics (Interest Rate, Maturity Date).

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1:** Given I am on my portfolio page, when I use the "Add New Asset" flow and select "Fixed Deposit", then I should see a form to enter all FD details.
*   [ ] **Scenario 2:** Given I have created a reinvestment-type FD, when I view my holdings, then the current value should be correctly calculated based on the compound interest formula.
*   [ ] **Scenario 3:** Given I have created a payout-type FD, when I view my holdings, then the current value should be equal to the principal amount.

---

### 4. Dependencies

*   This feature is a prerequisite for tracking interest income from FDs (`FR4.5`).

---

### 5. Additional Context

*   **Requirement ID:** `(FR4.3.2)`
*   This is the first issue under the "Advanced Asset Support" epic. The implementation should be designed to be extensible for other fixed-income assets like Bonds and PPF.