## 2025-02-18 - [O(N) vs O(NxM) in Holding Calculation]
**Learning:** The application was performing linear scans of `asset_map` values to find assets by ticker symbol inside loops iterating over holdings. This resulted in O(N*M) complexity where N is holdings and M is total assets.
**Action:** Create auxiliary maps (like `ticker_map`) immediately after fetching bulk data to ensure O(1) lookups for secondary keys.
