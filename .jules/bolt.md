## 2025-02-18 - [O(N) vs O(NxM) in Holding Calculation]
**Learning:** The application was performing linear scans of `asset_map` values to find assets by ticker symbol inside loops iterating over holdings. This resulted in O(N*M) complexity where N is holdings and M is total assets.
**Action:** Create auxiliary maps (like `ticker_map`) immediately after fetching bulk data to ensure O(1) lookups for secondary keys.

## 2025-02-18 - [O(1) dictionary mapping for available lots logic]
**Learning:** During the FIFO and Specific Matching for linked sell transactions, finding matching lot `buy_transaction_id` using a nested loop in Python lists makes the application iterate continuously at a time complexity of O(N * M).
**Action:** Always maintain mapping variables such as dictionaries initialized with array populations that use `transaction_id` keys mapped directly to lot dictionaries to allow fast O(1) matching.
