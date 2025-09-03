---
name: '🚀 Feature Request'
about: 'Implement user-managed watchlists'
title: 'feat: Implement user-managed watchlists'
labels: 'enhancement, feature, epic:market-insights'
assignees: ''
---

### 1. User Story

**As an** investor,
**I want to** create and manage watchlists of assets I'm interested in,
**so that** I can monitor their performance without having to add them to my portfolio.

---

### 2. Functional Requirements

*   [ ] Users must be able to create multiple, named watchlists (e.g., "Tech Stocks", "EV Watch").
*   [ ] Users must be able to add assets (Stocks, MFs, etc.) to any of their watchlists.
*   [ ] A dedicated "Watchlists" page must be created to display all user-created watchlists.
*   [ ] Each watchlist should be displayed as a table showing its assets with key metrics (e.g., Current Price, Day's Change).
*   [ ] Users must be able to remove assets from a watchlist.
*   [ ] Users must be able to delete an entire watchlist.

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1:** Given I am on the Watchlists page, when I create a new watchlist named "Tech Stocks", then it should appear on the page.
*   [ ] **Scenario 2:** Given I have a "Tech Stocks" watchlist, when I add "GOOGL" to it, then "GOOGL" and its market price should appear in the watchlist's table.
*   [ ] **Scenario 3:** Given "GOOGL" is in my watchlist, when I click the "remove" button for it, then it should disappear from the list.

---

### 4. Dependencies

*   This feature depends on the financial data API integration (`FR5.1`) to fetch prices for the assets in the watchlist.

---

### 5. Additional Context

*   **Requirement ID:** `(FR8.1)`
*   This is a core feature for market research and monitoring, allowing users to engage with market data beyond their own holdings.

