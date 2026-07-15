---
name: '🚀 Feature Request'
about: 'Project future value of linked assets and determine On-Track status'
title: 'feat: Project Goal Future Value and Track Status (FR13.4)'
labels: 'enhancement, feature, epic:goal-tracking'
assignees: ''
---

**Release: v1.3.0-part2 (Goal Projections & Analytics)**

### 1. User Story

**As a** user tracking a financial goal,
**I want to** see a projection of my linked assets' future value based on their current performance (XIRR),
**so that** I can see if my goal is "On Track" or "Off Track".

---

### 2. Functional Requirements

*   [ ] Calculate the current XIRR of all linked assets combined.
*   [ ] Project the future value of these linked assets at the goal's target date using that XIRR (or a fallback expected return if historical return is unavailable or extremely high/low).
*   [ ] Compare the projected future value against the target amount.
*   [ ] Determine the status:
    *   **On Track:** Projected future value >= Target amount
    *   **Off Track:** Projected future value < Target amount
*   [ ] Display the status and future value projection chart on the Goal Dashboard/Detail page.

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1:** Given a goal with target ₹5,00,000 in 3 years, if the projected value of linked assets at the target date is ₹5,50,000, then the status must show as "On Track".
*   [ ] **Scenario 2:** Given a goal with target ₹5,00,000 in 3 years, if the projected value is ₹4,20,000, then the status must show as "Off Track".
*   [ ] **Scenario 3:** The Goal details page displays a projection chart showing the growth path of investments towards the target.

---

### 4. Dependencies

*   Depends on the existing Goal Management and Asset Linking foundations (FR13.1, FR13.2).

---

### 5. Additional Context

*   **Requirement ID:** `(FR13.4)`
*   This is part of Release v1.3.0 (Goal Projections & Analytics).
