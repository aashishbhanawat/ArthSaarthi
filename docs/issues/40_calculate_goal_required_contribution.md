---
name: '🚀 Feature Request'
about: 'Calculate required contribution rates (SIPs) to hit goal targets'
title: 'feat: Calculate Goal Required Contribution Rate (SIP) (FR13.3)'
labels: 'enhancement, feature, epic:goal-tracking'
assignees: ''
---

**Release: v1.3.0-part2 (Goal Projections & Analytics)**

### 1. User Story

**As a** user tracking a financial goal,
**I want to** see the required monthly contribution (SIP) needed to reach my goal,
**so that** I can adjust my savings and budget accordingly.

---

### 2. Functional Requirements

*   [ ] Implement a backend function/endpoint to calculate the required monthly contribution rate (SIP) to reach the target amount by the target date.
*   [ ] The formula should factor in:
    *   Target amount (`target_amount`)
    *   Target date (`target_date`)
    *   Current value of linked assets (`current_value`)
    *   Expected annual rate of return (can default to a standard rate, e.g., 10% for equity/mixed, or use the weighted average historical return/XIRR of linked assets).
*   [ ] Return this calculation in the goal details API response.
*   [ ] Update the Goal Detail UI to display the calculated required monthly contribution.

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1:** Given a goal with target ₹10,00,000 in 5 years, with ₹0 current value and an assumed 12% annual return, the system calculates a monthly contribution of approximately ₹12,000 - ₹12,500.
*   [ ] **Scenario 2:** When viewing a Goal's detail page, the user should clearly see: "Required Monthly Contribution: ₹X,XXX / month".

---

### 4. Dependencies

*   Depends on the existing Goal Management and Asset Linking foundations (FR13.1, FR13.2).

---

### 5. Additional Context

*   **Requirement ID:** `(FR13.3)`
*   This is part of Release v1.3.0 (Goal Projections & Analytics).
