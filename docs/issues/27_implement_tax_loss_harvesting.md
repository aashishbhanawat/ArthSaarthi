---
name: '🚀 Feature Request'
about: 'Implement AI-powered tax-loss harvesting suggestions'
title: 'feat: Implement AI-powered tax-loss harvesting suggestions'
labels: 'enhancement, feature, epic:ai-insights'
assignees: ''
---

### 1. User Story

**As a** tax-conscious investor,
**I want** the system to use AI to analyze my portfolio and suggest tax-loss harvesting opportunities,
**so that** I can offset my capital gains and optimize my tax liability.

---

### 2. Functional Requirements

*   [ ] Implement a backend function that prepares a user's portfolio data (holdings with unrealized gains/losses, buy dates, cost basis) for the AI engine.
*   [ ] Develop a prompt for the AI model that asks it to identify and suggest specific tax-loss harvesting opportunities.
*   [ ] The AI's suggestions should include which assets to sell and the potential tax savings.
*   [ ] Create a new UI component or page to display these AI-generated suggestions to the user.
*   [ ] The suggestions should include a clear disclaimer that they do not constitute financial advice.

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1:** Given my portfolio has several stocks with significant short-term unrealized losses, when I request tax-loss harvesting suggestions, then the AI should suggest selling those specific stocks to offset gains.
*   [ ] **Scenario 2:** Given my portfolio has no significant unrealized losses, when I request suggestions, then the system should inform me that no suitable opportunities were found.

---

### 4. Dependencies

*   This feature depends on the completion of the AI Engine Configuration (`FR10.1`, Issue #26).
*   It requires accurate unrealized capital gains data, which is related to `FR6.5`.

---

### 5. Additional Context

*   **Requirement ID:** `(FR10.2)`
*   The prompt engineering for this feature is critical. The prompt must provide the AI with a clear, structured overview of the portfolio's state and ask for specific, actionable recommendations.

