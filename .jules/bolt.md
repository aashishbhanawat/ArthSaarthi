## 2026-04-20 - Optimize matching logic in HoldingDetailModal
**Learning:** Finding items in an array repeatedly within a nested loop creates an (N^2)$ bottleneck. Constructing a Map/Dictionary for lookups reduces complexity to (N)$.
**Action:** Always index collections by ID into a Map before performing repeated lookups in a loop.
