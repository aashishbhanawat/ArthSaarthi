## 2025-02-18 - [O(N) vs O(NxM) in Holding Calculation]
**Learning:** The application was performing linear scans of `asset_map` values to find assets by ticker symbol inside loops iterating over holdings. This resulted in O(N*M) complexity where N is holdings and M is total assets.
**Action:** Create auxiliary maps (like `ticker_map`) immediately after fetching bulk data to ensure O(1) lookups for secondary keys.

## $(date +%Y-%m-%d) - Prevent N+1 query in dashboard history loop
**Learning:** Accessing relationships (like `t.asset.ticker_symbol`) inside a loop over fetched ORM objects triggers an N+1 query if not eagerly loaded.
**Action:** Use `.options(joinedload(...))` on the initial query when related objects will be accessed in a loop over the results.
