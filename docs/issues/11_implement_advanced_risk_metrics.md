---
name: '🚀 Feature Request'
about: 'Implement advanced risk metrics (Volatility, Beta, Alpha, etc.)'
title: 'feat: Implement advanced risk metrics (Volatility, Beta, Alpha, etc.)'
labels: 'enhancement, feature, epic:analytics'
assignees: ''
---

### 1. User Story

**As a** data-driven investor,
**I want to** see advanced risk metrics like Volatility, Beta, and Alpha for my portfolio,
**so that** I can better understand the risk profile of my investments and how they perform relative to the market.

---

### 2. Functional Requirements

*   [ ] Implement backend functions to calculate portfolio Volatility (Standard Deviation of returns).
*   [ ] Implement backend functions to calculate portfolio Beta and Alpha against a selected benchmark (e.g., Nifty 50).
*   [ ] Expose these calculations via the analytics API endpoint.
*   [ ] Display these new risk metrics on the portfolio analytics dashboard.

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1:** Given a portfolio and a selected benchmark, when I view the analytics dashboard, then I should see the calculated Volatility, Beta, and Alpha values.
*   [ ] **Scenario 2:** A Beta value greater than 1 should indicate that the portfolio is more volatile than the benchmark.

---

### 4. Dependencies

*   This feature depends on the completion of portfolio benchmarking (`FR6.3`).

---

### 5. Additional Context

*   **Requirement ID:** `(FR6.2)`
*   This will require historical price data for both the portfolio and the selected benchmark index. The implementation will need to handle date alignment and return calculations carefully.

