---
name: '🚀 Feature Request'
about: 'Implement a market news feed'
title: 'feat: Implement a market news feed relevant to user holdings'
labels: 'enhancement, feature, epic:market-insights'
assignees: ''
---

### 1. User Story

**As an** investor,
**I want to** see a feed of recent financial news that is relevant to the assets in my portfolio and watchlist,
**so that** I can stay informed about market events and news that could impact my investments.

---

### 2. Functional Requirements

*   [ ] Integrate with a third-party news API to fetch financial news articles.
*   [ ] The system should fetch news specifically related to the tickers present in the user's portfolios and watchlists.
*   [ ] Create a new "Market News" page or a component on the main dashboard to display the news feed.
*   [ ] Each news item in the feed must display a headline, source, publication date, and a brief summary.
*   [ ] Clicking on a news item must open the full article on the original source's website in a new browser tab.

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1:** Given I hold "RELIANCE" stock, when I view the news feed, then I should see recent news articles where "Reliance" is mentioned.
*   [ ] **Scenario 2:** When I click on a news headline in the feed, then the full article should open in a new tab.

---

### 4. Dependencies

*   This feature depends on the financial data API integration (`FR5.1`) or may require a new, dedicated news API service.

---

### 5. Additional Context

*   **Requirement ID:** `(FR8.2)`
*   This is the first new issue for the "Market Insights & Research" epic (as Watchlists are already complete). Caching news results will be important to manage API usage and costs.

