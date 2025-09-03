---
name: '🚀 Feature Request'
about: 'Implement Time-weighted (TWR) and Money-weighted (MWR) return calculations'
title: 'feat: Implement Time-weighted (TWR) and Money-weighted (MWR) return calculations'
labels: 'enhancement, feature, epic:analytics'
assignees: ''
---

### 1. User Story

**As a** sophisticated investor,
**I want to** see both Time-weighted (TWR) and Money-weighted (MWR) returns for my portfolio,
**so that** I can accurately assess my investment performance, independent of the timing of my cash flows.

---

### 2. Functional Requirements

*   [ ] Implement a backend function to calculate Time-weighted Return (TWR) for a given portfolio and time period.
*   [ ] Implement a backend function to calculate Money-weighted Return (MWR) for a given portfolio and time period. (Note: XIRR is already a form of MWR, so this may be an enhancement).
*   [ ] Expose these calculations via a new or existing analytics API endpoint.
*   [ ] Display TWR and MWR on the portfolio analytics dashboard.

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1:** Given a portfolio with several cash inflows and outflows, when I view the analytics dashboard, then I should see both the TWR and MWR (or XIRR) values displayed.
*   [ ] **Scenario 2:** The calculated TWR should not be significantly affected by the size or timing of deposits/withdrawals, reflecting the performance of the underlying asset choices.

---

### 4. Dependencies

*   This feature builds upon the existing analytics framework (`FR6`).

---

### 5. Additional Context

*   **Requirement ID:** `(FR6.1)`
*   This feature adds more sophisticated performance metrics for advanced users. It will require careful handling of cash flows and time periods in the calculation logic.

