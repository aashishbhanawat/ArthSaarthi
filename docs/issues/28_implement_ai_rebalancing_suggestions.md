---
name: '🚀 Feature Request'
about: 'Implement AI-powered rebalancing suggestions'
title: 'feat: Implement AI-powered rebalancing suggestions'
labels: 'enhancement, feature, epic:ai-insights'
assignees: ''
---

### 1. User Story

**As a** user with a defined risk profile,
**I want** the system to use AI to analyze my portfolio's alignment with my risk tolerance and suggest concrete rebalancing actions,
**so that** I can easily maintain a balanced portfolio that matches my long-term goals.

---

### 2. Functional Requirements

*   [ ] Implement a backend function that prepares a user's portfolio data (current asset allocation) and their risk profile (e.g., "Moderate") for the AI engine.
*   [ ] Develop a prompt for the AI model that asks it to provide specific, actionable rebalancing steps.
*   [ ] The AI's suggestions should be concrete (e.g., "Sell 5 shares of STOCK_A, Buy 10 units of MUTFUND_B").
*   [ ] The AI should be prompted to consider minimizing transaction costs and potential tax implications in its suggestions.
*   [ ] Create a new UI component to display these rebalancing suggestions, including the rationale behind them.

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1:** Given my personal risk profile is "Moderate" but my portfolio has drifted to become "Aggressive" (e.g., 90% equity), when I request rebalancing suggestions, then the AI should suggest selling some equity and buying assets in other classes (e.g., debt, gold) to align with a moderate allocation.
*   [ ] **Scenario 2:** Given my portfolio is already well-aligned with my risk profile, when I request suggestions, then the AI should confirm the alignment and suggest no major changes are needed.

---

### 4. Dependencies

*   This feature depends on the completion of the AI Engine Configuration (`FR10.1`, Issue #26).
*   It critically depends on the Risk Profile Management epic, requiring both the user's calculated risk score (`FR12.2`) and the portfolio's risk assessment (`FR12.3`).

---

### 5. Additional Context

*   **Requirement ID:** `(FR10.3)`, `(FR10.5)`
*   This feature provides highly actionable advice. The prompt engineering must be robust, providing the AI with the user's risk profile, the portfolio's current state, and clear instructions on the desired output format.

