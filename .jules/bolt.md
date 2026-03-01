## 2025-02-18 - [O(N) vs O(NxM) in Holding Calculation]
**Learning:** The application was performing linear scans of `asset_map` values to find assets by ticker symbol inside loops iterating over holdings. This resulted in O(N*M) complexity where N is holdings and M is total assets.
**Action:** Create auxiliary maps (like `ticker_map`) immediately after fetching bulk data to ensure O(1) lookups for secondary keys.

## 2025-02-18 - [O(1) Python object reference tracking in Arrays vs Dicts]
**Learning:** In python, you can index a dictionary for quick O(1) loopups while preserving the same memory references used in an array/list. This helps lower algorithm complexity for searches inside loops down from O(N*M) to O(N), without affecting logic that relies on list-order iteration down the line.
**Action:** Initialize a `lots_map` inside loops updating `available_quantity` attributes and retrieve them for updating to reduce time complexity without impacting functionality that relies on FIFO list processing.