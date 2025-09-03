---
name: '🚀 Feature Request'
about: 'Calculate and display user risk score and profile'
title: 'feat: Calculate and display user risk score and profile'
labels: 'enhancement, feature, epic:risk-management'
assignees: ''
---

### 1. User Story

**As a** user who has completed the risk questionnaire,
**I want to** see my calculated risk score and resulting profile (e.g., Conservative, Moderate, Aggressive),
**so that** I can clearly understand my investment personality.

---

### 2. Functional Requirements

*   [ ] Implement a backend function to calculate a numerical risk score based on the user's saved questionnaire answers.
*   [ ] The scoring logic should assign weighted points to each multiple-choice answer.
*   [ ] The system must map the final score to a predefined risk category (e.g., Conservative, Moderate, Aggressive).
*   [ ] The calculated score and category must be stored in the user's profile data.
*   [ ] A results page or component must be created to display the final risk profile to the user immediately after they complete the questionnaire.

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1:** Given a user submits answers that are predominantly cautious, when the score is calculated, then they should be assigned to the "Conservative" risk category.
*   [ ] **Scenario 2:** Given a user submits answers that indicate a high tolerance for risk, when the score is calculated, then they should be assigned to the "Aggressive" risk category.
*   [ ] **Scenario 3:** After submitting the questionnaire, I should be immediately redirected to a page that clearly states my calculated risk profile, for example, "Your Risk Profile: Moderate".

---

### 4. Dependencies

*   This feature depends on the completion of the Risk Profile Questionnaire (`FR12.1`, Issue #23).

---

### 5. Additional Context

*   **Requirement ID:** `(FR12.2)`
*   The specific questions, answers, and the scoring algorithm will need to be defined as part of this task. The initial implementation can use a simple additive scoring model.

