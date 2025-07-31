# Feature Plan: Advanced Portfolio Analytics

**Feature ID:** FR6
**Status:** Done

---

## 1. Overview

This feature will enhance the application by providing users with advanced performance metrics for their portfolios. The initial implementation will focus on two key industry-standard metrics: **XIRR (Extended Internal Rate of Return)** and the **Sharpe Ratio**. This moves the application beyond simple profit/loss tracking to provide true, time-weighted and risk-adjusted performance analysis.

---

## 2. User Story

*As a sophisticated investor, I want to see advanced performance metrics like XIRR and the Sharpe Ratio for my portfolios, so I can accurately assess my investment performance against benchmarks and understand my returns relative to the risk taken.*

---

## 3. Functional Requirements

*   **FR6.1:** The system shall calculate the time-weighted rate of return (XIRR) for each individual portfolio.
*   **FR6.2:** The system shall calculate the risk-adjusted return (Sharpe Ratio) for each individual portfolio.
*   **FR6.3:** The calculated XIRR and Sharpe Ratio shall be displayed clearly on the Portfolio Detail page.

---

## 4. Non-Functional Requirements

*   **NFR6.1 (Accuracy):** All financial calculations must be accurate to at least four decimal places.
*   **NFR6.2 (Performance):** The analytics calculation for a portfolio with up to 1,000 transactions should complete within 2 seconds.

---

## 5. Backend Implementation Plan

*   **Dependencies:**
    *   Add the `py-xirr` library to `backend/requirements.txt` for efficient and accurate XIRR calculation.
*   **API Endpoint:**
    *   Create a new endpoint: `GET /api/v1/portfolios/{portfolio_id}/analytics`.
*   **CRUD/Service Layer:**
    *   Create a new module: `backend/app/crud/crud_analytics.py`.
    *   Implement a function `get_portfolio_analytics(db: Session, portfolio_id: int)` that:
        1.  Fetches all transactions for the given portfolio.
        2.  Fetches the current total market value of the portfolio's holdings.
        3.  Constructs a series of cash flows (negative for buys, positive for sells) and their dates, including the final portfolio value as a positive cash flow on the current date.
        4.  Uses the `py-xirr` library to calculate the XIRR from these cash flows.
        5.  Fetches the portfolio's historical daily values (reusing logic from `crud_dashboard`), calculates daily returns, and computes the Sharpe Ratio (assuming a risk-free rate of 0% for simplicity in this MVP).
*   **Schemas:**
    *   Create a new file: `backend/app/schemas/analytics.py`.
    *   Define an `AnalyticsResponse(BaseModel)` with fields `xirr: float` and `sharpe_ratio: float`.

---

## 6. Frontend Implementation Plan

*   **API Service:**
    *   Add a `getPortfolioAnalytics(portfolioId: number)` function to `frontend/src/services/portfolioApi.ts`.
*   **React Query Hook:**
    *   Add a `usePortfolioAnalytics(portfolioId: number)` hook to `frontend/src/hooks/usePortfolios.ts`.
*   **UI Components:**
    *   Create a new component `frontend/src/components/Portfolio/AnalyticsCard.tsx` to display the XIRR and Sharpe Ratio with labels and tooltips explaining each metric.
    *   Integrate the `AnalyticsCard.tsx` into the `PortfolioDetailPage.tsx`, placing it in a prominent position.

---

## 7. Testing Plan (QA)

*   **Backend:**
    *   Create a new test file `backend/app/tests/api/v1/test_analytics.py`.
    *   Write unit tests for the XIRR and Sharpe Ratio calculation logic in `crud_analytics.py` using predefined transaction data and asserting against known, correct results.
    *   Write integration tests for the `GET /api/v1/portfolios/{portfolio_id}/analytics` endpoint, covering success, not found, and unauthorized access scenarios.
*   **Frontend:**
    *   Create a new test file for `AnalyticsCard.test.tsx` that verifies correct rendering of loading, error, and success states, and ensures numbers are formatted correctly (e.g., as percentages).
