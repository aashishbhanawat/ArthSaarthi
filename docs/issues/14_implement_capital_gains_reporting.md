---
name: '🚀 Feature Request'
about: 'Implement Capital Gains Reporting in ITR format'
title: 'feat: Implement Capital Gains Reporting in ITR format'
labels: 'enhancement, feature, epic:analytics'
assignees: ''
---

### 1. User Story

**As an** Indian investor,
**I want to** generate a detailed capital gains report for a financial year,
**so that** I can easily and accurately file my Income Tax Returns (ITR).

---

### 2. Functional Requirements

*   [ ] The system must calculate and generate reports for realized long-term, short-term, and intra-day capital gains.
*   [ ] The report must be available for download in a format compatible with ITR filing (e.g., CSV/Excel).
*   [ ] The calculation logic must correctly account for complex tax provisions like LTCG Grandfathering and Indexation for debt funds.
*   [ ] Users must be able to view their unrealized capital gains to estimate potential tax liability.
*   [ ] The system must correctly determine the holding period to classify gains as short-term or long-term for different asset classes (Equity vs. Debt).

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1:** Given I have sold some stocks during a financial year, when I generate a capital gains report, then the report should correctly classify the gains/losses as long-term or short-term.
*   [ ] **Scenario 2:** Given I have sold debt mutual funds held for more than 3 years, when I generate the report, then the long-term capital gains should be calculated after applying indexation benefits.

---

### 4. Dependencies

*   This feature requires accurate transaction data, including buy/sell dates and prices.
*   It depends on the system's ability to track corporate actions (splits, bonuses) correctly to adjust the cost basis.

---

### 5. Additional Context

*   **Requirement ID:** `(FR6.5)`
*   This is a highly complex feature that requires a deep understanding of Indian tax laws. The implementation must be thoroughly tested for accuracy.

