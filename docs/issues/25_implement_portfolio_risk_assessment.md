---
name: '🚀 Feature Request'
about: 'Implement portfolio risk assessment and alignment check'
title: 'feat: Implement portfolio risk assessment and alignment check'
labels: 'enhancement, feature, epic:risk-management'
assignees: ''
---

### 1. User Story

**As a** user with a defined risk profile,
**I want to** see an assessment of my portfolio's actual risk level,
**so that** I can understand if my investments are aligned with my personal risk tolerance.

---

### 2. Functional Requirements

*   [ ] Define and store risk factors for different asset classes (e.g., Equity=5, Bonds=2, FD=1).
*   [ ] Implement a backend function to calculate the weighted-average risk score for a user's portfolio based on its asset allocation.
*   [ ] Map the calculated portfolio risk score to a risk category (e.g., Conservative, Moderate, Aggressive), similar to the user's profile.
*   [ ] Create a "Risk Alignment" dashboard or UI component.
*   [ ] This dashboard must display the user's personal risk profile alongside the calculated portfolio risk profile.
*   [ ] The UI must clearly indicate if there is a mismatch between the two profiles.

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1:** Given my personal risk profile is "Conservative" and my portfolio is 90% in high-risk stocks, when I view the Risk Alignment dashboard, then it should display "Your Profile: Conservative" and "Portfolio Risk: Aggressive" and indicate a "Mismatch".
*   [ ] **Scenario 2:** Given my personal risk profile is "Aggressive" and my portfolio is 90% in high-risk stocks, when I view the Risk Alignment dashboard, then it should indicate that my portfolio is "Aligned" with my profile.

---

### 4. Dependencies

*   This feature depends on the completion of Risk Score Calculation (`FR12.2`, Issue #24).

---

### 5. Additional Context

*   **Requirement ID:** `(FR12.3)`, `(FR12.4)`
*   This feature connects the user's personal assessment to their actual investments, providing actionable insight. The initial implementation can use a simple, predefined mapping of asset class to risk score.

