## 2026-04-20 - Optimize matching logic in HoldingDetailModal
**Learning:** Finding items in an array repeatedly within a nested loop creates an $O(N^2)$ bottleneck. Constructing a Map/Dictionary for lookups reduces complexity to $O(N)$.
**Action:** Always index collections by ID into a Map before performing repeated lookups in a loop.
## 2024-05-25 - React Chartjs-2 Memoization Overhead
**Learning:** In React components using `react-chartjs-2` (like `AssetAllocationChart` and `PortfolioHistoryChart`), passing unmemoized objects (e.g., `options` or `chartData`) forces expensive internal chart recalculations and triggers redundant O(N) generation logic (like dynamic color mapping) on every parent render.
**Action:** Always wrap `options` and `data`/`chartData` props in `useMemo` hooks when rendering complex third-party charts to stabilize references and prevent performance degradation.
## 2026-06-01 - Optimize rendering of BenchmarkComparison component
**Learning:** In React components using `react-chartjs-2`, passing unmemoized objects (e.g., `options` or `chartData`) defined inside the render function forces expensive internal chart recalculations and triggers redundant O(N) mapping operations on every parent render.
**Action:** Always extract `options` and `data` props into `useMemo` hooks using stable dependencies when rendering complex third-party charts to prevent performance degradation.
