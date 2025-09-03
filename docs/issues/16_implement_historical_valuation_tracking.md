---
name: '🚀 Feature Request'
about: 'Implement historical end-of-month valuation tracking'
title: 'feat: Implement historical end-of-month valuation tracking'
labels: 'enhancement, feature, epic:analytics'
assignees: ''
---

### 1. User Story

**As a** long-term investor,
**I want** the system to automatically record my portfolio's value at regular intervals (e.g., end of month),
**so that** I can accurately track and visualize my performance over long periods, even if I don't log in every day.

---

### 2. Functional Requirements

*   [ ] Implement a new database table to store historical portfolio valuations (e.g., `portfolio_history`).
*   [ ] Create a background job or scheduled task that runs periodically (e.g., daily or monthly) to calculate and store the total value of each user's portfolio.
*   [ ] The historical performance chart on the main dashboard (`FR3.7`) should be refactored to use this pre-calculated data instead of calculating it on the fly.

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1:** Given a user has a portfolio, when the scheduled task runs, then a new entry with the portfolio's current total value and the date should be saved to the database.
*   [ ] **Scenario 2:** Given historical valuation data exists, when I view the main dashboard, then the portfolio history chart should correctly display the trend based on the stored data.

---

### 4. Dependencies

*   This feature is a prerequisite for accurate long-term benchmarking (`FR6.3`).

---

### 5. Additional Context

*   **Requirement ID:** `(FR6.7)`
*   This will likely require adding a dependency for a background task scheduler, such as `apscheduler`. This improves performance by pre-calculating data instead of computing it on every page load.

