# Feature Plan: Pluggable Financial Data Service

**Feature ID:** NFR12 (Architecture)
**Title:** Refactor FinancialDataService to be Pluggable
**User Story:** As a developer, I want to refactor the `FinancialDataService` to support multiple data providers, so that the system can be easily extended to use different APIs for different asset classes (e.g., a dedicated bond API, a commodity API for SGBs).
**Status:** 📝 Planned

---

## 1. Objective

To replace the current monolithic `FinancialDataService` with a more flexible, pluggable architecture using the **Strategy Pattern**. This will decouple the application's core logic from any single data provider (like `yfinance`) and allow for a more robust, multi-layered data fetching strategy with clear fallback mechanisms.

This is a prerequisite for properly implementing advanced bond pricing and other specialized asset valuations.

---

## 2. High-Level Technical Design

1.  **`FinancialDataProvider` Interface:**
    *   An abstract base class will be created in `backend/app/services/providers/base.py`.
    *   It will define a common interface with methods like `get_current_prices`, `get_historical_prices`, and `get_asset_details`.

2.  **Concrete Provider Implementations:**
    *   The existing `yfinance` logic will be refactored into a `YFinanceProvider` class that implements the `FinancialDataProvider` interface.
    *   The existing `AmfiIndiaProvider` logic will be refactored to implement the same interface.
    *   **Future:** New providers (e.g., `SebiBondApiProvider`, `GoldPriceProvider`) can be easily added by creating new classes that adhere to the interface.

3.  **`FinancialDataService` Facade:**
    *   The main `FinancialDataService` class will be refactored to act as a **facade**.
    *   It will maintain a registry of available providers.
    *   When a request for data is made (e.g., `get_current_prices`), the service will look at the `asset_type` of the requested assets.
    *   It will then delegate the call to the appropriate registered provider based on a predefined strategy (e.g., "for `MUTUAL_FUND`, use `AmfiIndiaProvider`; for `STOCK`, use `YFinanceProvider`").

4.  **Fallback Logic:**
    *   The service will implement a fallback chain. For example, for a bond, it might first try a dedicated bond API. If that fails, it could fall back to trying `yfinance`. If that also fails, it will return a default value, preventing crashes.

---

## 3. Implementation Plan

1.  Create a new directory `backend/app/services/providers/`.
2.  Define the `FinancialDataProvider` abstract base class in `base.py`.
3.  Move and refactor the `yfinance` logic into a new `YFinanceProvider` class in `yfinance_provider.py`.
4.  Move and refactor the `amfi` logic into a new `AmfiIndiaProvider` class in `amfi_provider.py`.
5.  Refactor the main `FinancialDataService` in `financial_data_service.py` to act as a facade, managing and delegating to the different provider instances.
6.  Update all parts of the application that use the old service to use the new one.
7.  Update all relevant tests to mock the new provider structure.

---