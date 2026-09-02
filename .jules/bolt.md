## 2026-04-20 - Optimize matching logic in HoldingDetailModal
**Learning:** Finding items in an array repeatedly within a nested loop creates an $O(N^2)$ bottleneck. Constructing a Map/Dictionary for lookups reduces complexity to $O(N)$.
**Action:** Always index collections by ID into a Map before performing repeated lookups in a loop.
## 2024-05-25 - React Chartjs-2 Memoization Overhead
**Learning:** In React components using `react-chartjs-2` (like `AssetAllocationChart` and `PortfolioHistoryChart`), passing unmemoized objects (e.g., `options` or `chartData`) forces expensive internal chart recalculations and triggers redundant O(N) generation logic (like dynamic color mapping) on every parent render.
**Action:** Always wrap `options` and `data`/`chartData` props in `useMemo` hooks when rendering complex third-party charts to stabilize references and prevent performance degradation.
## 2026-06-01 - Optimize rendering of BenchmarkComparison component
**Learning:** In React components using `react-chartjs-2`, passing unmemoized objects (e.g., `options` or `chartData`) defined inside the render function forces expensive internal chart recalculations and triggers redundant O(N) mapping operations on every parent render.
**Action:** Always extract `options` and `data` props into `useMemo` hooks using stable dependencies when rendering complex third-party charts to prevent performance degradation.
## 2024-05-26 - Optimize React render loops with pre-aggregated totals
**Learning:** In React components rendering grouped lists or tables (like `HoldingsTable.tsx`), executing O(N) aggregation operations (e.g., `.reduce()`) inline within a `.map()` function inside the render function forces expensive recalculations of subset totals on every render cycle (like expanding an accordion).
**Action:** Always extract and memoize group aggregations into a single dictionary (e.g., `groupTotals`) using `useMemo` based on the underlying grouped data, rather than calculating them inline during render.
## 2024-05-26 - Optimize React render loops with pre-aggregated totals (Update)
**Learning:** In React components rendering grouped lists or tables (like `HoldingsTable.tsx`), executing O(N) aggregation operations (e.g., `.reduce()`) inline within a `.map()` function inside the render function forces expensive recalculations of subset totals on every render cycle (like expanding an accordion). Furthermore, depending on sorted states for totals recalculation triggers redundant renders when sorting is changed, even if totals are identical.
**Action:** Always extract and memoize group aggregations into a single dictionary (e.g., `groupTotals`) using `useMemo` based on the underlying *raw* data (rather than sorted data), and iterating over it efficiently (e.g. `for...of`) rather than calculating them inline during render.

## 2024-05-30 - Prevent Expensive Array Recalculations on Render
**Learning:** React components dealing with historical data arrays (like `transactions` in `PpfHoldingDetailModal.tsx` and `lotSelections` in `TransactionFormModal.tsx`) often perform multiple chained array operations (`filter`, `reduce`, `sort`, `map`, `reverse`) directly within the render body. Since these components can re-render frequently during UI interactions or parent updates, this leads to unnecessary O(N) and O(N log N) recalculations every render cycle.
**Action:** Always extract complex chained array transformations and aggregations into a `useMemo` block, declaring the source array as the dependency. This guarantees the expensive processing only happens when the underlying data actually changes, yielding measurable render performance improvements for large data sets.
## 2024-08-04 - Memoize sorted transactions in BondDetailModal
**Learning:** `BondDetailModal` was sorting `transactions` on every render without a `useMemo` hook, causing unnecessary O(N log N) recalculations even when `transactions` had not changed.
**Action:** Wrapped the sorting logic in a `useMemo` hook dependent on `transactions`.
## 2024-08-17 - Optimize React table renders with React.memo
**Learning:** Purely presentational table/list components (like `TransactionHistoryTable`, `TransactionList`, `UsersTable`, `InterestRateTable`, `WatchlistTable`, `TopMoversTable`, `PortfolioList`) frequently receive large arrays of data. Re-rendering them when parent components update state that doesn't affect the table's props (e.g. modals opening, unrelated parent re-renders) creates an unnecessary performance overhead.
**Action:** Always wrap the default export of such presentational table/list components in `React.memo()`. Also ensure parent components pass stable function references (using `useCallback`) to make `React.memo` fully effective. Add a comment explaining the memoization.

**Action:** Ensure that the parent components pass stable function references using `useCallback` when using `React.memo` on these presentational components.

## 2025-03-02 - Optimize cashflow analytics prorating in backend
**Learning:** `_get_realized_and_unrealized_cash_flows` had `O(I * (B + S))` complexity where `I` is income flows, `B` is buys, and `S` is sells, because of list comprehensions doing sequential iteration to find quantities for specific dates inside a loop over income flows. This creates a severe performance bottleneck scaling super-linearly with large transaction history.
**Action:** Replaced O(N) subset sums with running cumulative sums and `bisect` logic (`O(log B + log S)`) per income event, bringing the overall performance from quadratic behavior (O(N^2)) to O(N log N). Always favor pre-computed prefix-sums + bisect over nested iteration for time series lookups.
## 2024-05-31 - Memoize event handlers passed to React.memo components
**Learning:** Wrapping a presentational component in `React.memo` (like `TransactionHistoryTable`) is completely ineffective if the parent component passes inline functions as props, because new function references are created on every parent render.
**Action:** Always wrap event handlers (like `onEdit`, `onDelete`) with `useCallback` in the parent component when passing them to memoized child components to ensure stable references and actually prevent unnecessary re-renders.
## 2026-09-01 - Memoize event handlers passed to UsersTable and InterestRateTable
**Learning:** Wrapping a presentational component in `React.memo` (like `UsersTable` and `InterestRateTable`) is completely ineffective if the parent component passes inline functions as props, because new function references are created on every parent render.
**Action:** Always wrap event handlers (like `handleEditUser`, `handleDeleteUser`, `handleOpenEditModal`, `handleOpenDeleteModal`) with `useCallback` in the parent component when passing them to memoized child components to ensure stable references and actually prevent unnecessary re-renders.
