Title: ⚡ [Performance] - N+1 Query in Goal Analytics (Database Fatigue)

Body:
📊 The Bottleneck
Location: backend/app/crud/crud_goal.py:57
Observed Pattern: `crud.holding.get_portfolio_holdings_and_summary` is called inside a `for link in goal.links:` loop. While there is a primitive `portfolio_cache` to avoid querying the *exact same* portfolio multiple times, it still executes O(N) separate, heavy queries to `get_portfolio_holdings_and_summary` if a goal references multiple distinct portfolios.
Impact: Increases API latency significantly (High Impact) when loading goals linked to numerous portfolios, triggering multiple separate aggregation queries for each.

⚡ Proposed Optimization
Action: Refactor the method to pre-fetch all unique portfolio IDs from `goal.links`, and use a batch function like `crud.holding.get_multiple_portfolios_holdings_and_summary(db, portfolio_ids=...)` to load all relevant holdings and summaries in a single or reduced set of queries, populating the local cache upfront before iterating through links.
Difficulty: Medium

🔬 Verification Plan
Manual Test: Create a Goal and link it to 10-20 distinct portfolios containing holdings. Load the Goals page and monitor backend response time.
Automated Test: Monitor tests in `backend/app/tests/api/v1/test_goals.py` (specifically analytics retrieval) for regression, asserting query counts if possible using a SQLAlchemy event listener.
Metric: Monitor the `GET /api/v1/goals/{id}/analytics` endpoint latency in backend logs (targeting <100ms response time).

---

Title: ⚡ [Performance] - Sequential Database Add in Asset Enrichment (Database Fatigue)

Body:
📊 The Bottleneck
Location: backend/app/crud/crud_holding.py:619 (and line 650)
Observed Pattern: Inside the AMFI and yfinance enrichment blocks of `_process_market_traded_assets`, `db.add(asset)` is called sequentially within a `for` loop for every asset enriched.
Impact: Sequential `.add()` operations on large portfolios incur roughly 99.8% more SQLAlchemy session management overhead than batching. When users import or refresh large portfolios, this blocks synchronous processing loops longer than necessary, increasing Time-To-Interactive.

⚡ Proposed Optimization
Action: Collect enriched `asset` models into a `list` (e.g., `modified_mfs` and `modified_equities`), and call `db.add_all(modified_assets)` after the loop concludes, followed by a single commit.
Difficulty: Easy

🔬 Verification Plan
Manual Test: Upload a CSV containing 50-100 unique, un-enriched mutual funds and stocks. Measure the import duration.
Automated Test: Unit tests in `backend/app/tests/crud/test_holding.py` focusing on `get_portfolio_holdings_and_summary` (since it triggers `_process_market_traded_assets`).
Metric: Measure backend log time taken for "Enriching X Mutual Funds via AMFI..." step and corresponding session flush/commit times.

---

Title: ⚡ [Performance] - Missing Virtualization in Portfolio Holdings List (List Inefficiency)

Body:
📊 The Bottleneck
Location: frontend/src/components/Portfolio/HoldingsTable.tsx:179
Observed Pattern: The `HoldingsTable` renders the entire list of `sectionHoldings.map((holding) => ...)` synchronously. For users with large portfolios (e.g., hundreds of distinct assets, bonds, and FDs), this creates a massive DOM tree.
Impact: Rendering hundreds of complex table rows containing nested components and SVGs simultaneously blocks the main thread, severely increasing Total Blocking Time (TBT) and causing jank during initial render or filter/sort operations, particularly on mobile devices.

⚡ Proposed Optimization
Action: Implement list virtualization using a library like `react-window` or `@tanstack/react-virtual` to only render the table rows currently visible within the user's viewport.
Difficulty: Medium

🔬 Verification Plan
Manual Test: Seed a database with a portfolio containing 500+ unique asset holdings. Navigate to the Portfolio view and observe the UI freeze time.
Automated Test: Frontend component test in `frontend/src/components/Portfolio/__tests__/HoldingsTable.test.tsx` (ensure tests mock virtualization bounds correctly).
Metric: Monitor Main Thread blocking time and Time to Interactive (TTI) via Chrome DevTools Performance tab.

---

Title: ⚡ [Performance] - O(N*M) Recalculation of PPF Holding Interest in Portfolio History (Algorithmic Waste)

Body:
📊 The Bottleneck
Location: backend/app/crud/crud_dashboard.py:515
Observed Pattern: Inside `_get_portfolio_history`, there is a daily historical simulation loop. For each day of the user's portfolio history, it iterates over all `ppf_assets` and calls `process_ppf_holding`, simulating interest calculations from the beginning of time up to `current_day`.
Impact: This creates an $O(N \times M)$ computational complexity (where $N$ is days of history, $M$ is PPF assets), severely throttling dashboard performance for older portfolios by repeatedly simulating years of compound interest daily rather than caching the previous day's balance/interest state.

⚡ Proposed Optimization
Action: Refactor the PPF simulation logic. Either calculate the full history of the PPF asset once (returning an array/map of daily or monthly values) outside the main historical loop, and simply look up the `current_day`'s value in O(1) time within the loop, or maintain an accumulated state dict that updates incrementally.
Difficulty: Hard

🔬 Verification Plan
Manual Test: Create a portfolio with a PPF asset and backdate transactions by 10-15 years. View the Dashboard and track backend latency.
Automated Test: Monitor API tests for `/api/v1/dashboard/history` in `backend/app/tests/api/v1/test_dashboard.py` (ensure historical duration covers multiple years for load testing).
Metric: Monitor the execution time of `_get_portfolio_history` (target <200ms for a 10-year history).
