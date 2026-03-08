## 2025-02-18 - [O(N) vs O(NxM) in Holding Calculation]
**Learning:** The application was performing linear scans of `asset_map` values to find assets by ticker symbol inside loops iterating over holdings. This resulted in O(N*M) complexity where N is holdings and M is total assets.
**Action:** Create auxiliary maps (like `ticker_map`) immediately after fetching bulk data to ensure O(1) lookups for secondary keys.

## YYYY-MM-DD - Resolve N+1 query in `crud_dashboard.py` Summary Calculations
**Learning:** Iterating over portfolios to call `get_portfolio_holdings_and_summary` triggers N*4 database queries per user dashboard load, leading to N+1 performance degradation when users have many portfolios.
**Action:** When aggregating data across multiple portfolios, implement and utilize bulk retrieval methods like `get_multiple_portfolios_holdings_and_summary` that use underlying `.in_(portfolio_ids)` queries. Process the grouped data in application memory to reduce database interaction from O(N) queries to O(1) queries.
