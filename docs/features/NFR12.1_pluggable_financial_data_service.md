# Non-Functional Requirement: Pluggable Financial Data Service

**Status: ✅ Done (Phases 1 & 2)**
**Feature ID:** NFR12.1
**Title:** Refactor FinancialDataService to be Pluggable

---

## 1. Objective

The current `FinancialDataService` is a monolithic class that directly contains the logic for fetching data from different sources (`yfinance`, `amfiindia.com`, etc.). This makes it difficult to add new data sources, test providers in isolation, or switch between providers for different asset classes.

The objective of this refactoring is to re-architect the service using a **Strategy Pattern**. This will create a pluggable system where each data source is an independent "provider" class that adheres to a common interface.

---

## 2. High-Level Requirements

-   Define a common `FinancialDataProvider` abstract base class or interface.
-   Refactor the existing `yfinance` logic into a `YFinanceProvider` class.
-   Refactor the existing AMFI logic into an `AmfiIndiaProvider` class.
-   The main `FinancialDataService` will act as a facade or a registry, delegating calls to the appropriate provider based on the asset type.

---

## 3. Detailed Implementation Plan

### 3.1. Define the Provider Interface

Create a new file `backend/app/services/providers/base.py`.

```python
from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

class FinancialDataProvider(ABC):
    @abstractmethod
    def get_current_prices(self, assets: List[Dict[str, Any]]) -> Dict[str, Dict[str, Decimal]]:
        """Fetches current and previous day's close price for a list of assets."""
        pass

    @abstractmethod
    def get_historical_prices(self, assets: List[Dict[str, Any]], start_date: date, end_date: date) -> Dict[str, Dict[date, Decimal]]:
        """Fetches historical prices for a list of assets over a date range."""
        pass

    @abstractmethod
    def get_asset_details(self, ticker_symbol: str) -> Optional[Dict[str, Any]]:
        """Fetches details for a single asset."""
        pass

    @abstractmethod
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Searches for assets supported by the provider."""
        pass
```

### 3.2. Refactor Existing Logic into Providers

1.  **Create `YFinanceProvider`:**
    *   Create `backend/app/services/providers/yfinance_provider.py`.
    *   Move all `yfinance`-related logic from `financial_data_service.py` into a new `YFinanceProvider` class that implements `FinancialDataProvider`.

2.  **Create `AmfiIndiaProvider`:**
    *   Create `backend/app/services/providers/amfi_provider.py`.
    *   Move all AMFI-related logic into a new `AmfiIndiaProvider` class.

### 3.3. Refactor `FinancialDataService`

*   The main `FinancialDataService` class in `financial_data_service.py` will be simplified.
*   It will instantiate the provider classes (`self.yfinance_provider = YFinanceProvider(...)`, etc.).
*   Its public methods (`get_current_prices`, etc.) will now contain logic to inspect the asset type and delegate the call to the appropriate provider. For example, if an asset is a "Mutual Fund", it will call `self.amfi_provider.get_current_prices()`; otherwise, it will call `self.yfinance_provider.get_current_prices()`.

---

## 4. Benefits

-   **Extensibility:** Adding a new data source (e.g., a dedicated bond API) becomes as simple as creating a new provider class.
-   **Testability:** Each provider can be unit-tested in isolation.
-   **Maintainability:** Code for each data source is self-contained and easier to manage.

---

## 5. Testing Strategy

Given the critical nature of this service, a rigorous testing strategy will be employed to prevent regressions, as outlined in the project's main `testing_strategy.md`.

1.  **Characterization Tests (Golden Master):**
    *   A new test suite, `test_holding_characterization.py`, will be created.
    *   This suite will set up a portfolio with a mix of assets (Stocks, Mutual Funds).
    *   It will mock the **current** `FinancialDataService` to return a fixed, predictable set of price data.
    *   It will then call `crud.holding.get_portfolio_holdings_and_summary()` and assert the final calculated values (e.g., `total_value`, `days_pnl`, `unrealized_pnl`). These assertions will capture the "golden master" output of the current system.

2.  **Refactoring with Parallel Validation:**
    *   As the `FinancialDataService` is refactored to use the new provider-based architecture, we will run these same characterization tests against the new implementation.
    *   The goal is to make the new implementation pass the *exact same tests* that were written to capture the behavior of the old implementation. Any deviation indicates a regression.

3.  **Full-Stack Verification:**
    *   After the refactoring is complete and all unit/integration tests pass, the **full E2E test suite must be executed** (`./run_local_tests.sh e2e`).
    *   A **manual E2E smoke test** will also be performed, focusing on the Dashboard and Portfolio Holdings pages to visually confirm that all values are being calculated and displayed correctly.

---


This architecture enables a clear roadmap for enhancing data sourcing capabilities in the future.

### Phase 1: Initial Refactor (Current Task)
*   **`AmfiIndiaProvider`:** Refactor existing AMFI logic for Indian Mutual Funds.
*   **`YFinanceProvider`:** Refactor existing `yfinance` logic for international equities and as a general fallback.

### Phase 2: Indian Market Default Provider
*   **`NseBhavcopyProvider`:** Create a new provider that scrapes the daily NSE Bhavcopy.
    *   **Pros:** Authoritative, free, provides closing prices for all listed Indian equities and bonds.
    *   **Cons:** Relies on web scraping, which can be brittle. Only provides closing prices.
    *   **Role:** Will serve as the default, out-of-the-box provider for Indian market data.

### Future Enhancements: Optional High-Quality Providers
*   **`ZerodhaKiteProvider` / `IciciBreezeProvider`:** Create providers for popular broker APIs.
    *   **Pros:** Highly reliable, provides real-time and historical data via stable APIs.
    *   **Cons:** Requires the user to have an account with the broker and provide their own API keys.
    *   **Role:** Will be an optional, high-quality data source that users can enable in their settings for superior data accuracy and reliability. The `FinancialDataService` will be configured to prioritize these providers if they are enabled by the user.