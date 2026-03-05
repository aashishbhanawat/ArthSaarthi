## 2025-02-18 - [O(N) vs O(NxM) in Holding Calculation]
**Learning:** The application was performing linear scans of `asset_map` values to find assets by ticker symbol inside loops iterating over holdings. This resulted in O(N*M) complexity where N is holdings and M is total assets.
**Action:** Create auxiliary maps (like `ticker_map`) immediately after fetching bulk data to ensure O(1) lookups for secondary keys.

## 2025-02-18 - [Parallel vs Serial API Calls in Loops]
**Learning:** The application was performing serial synchronous network calls (yfinance) and repeated large data deserialization (AMFI) inside a holding calculation loop. This led to O(N) latency where N is the number of unenriched assets.
**Action:** Always identify loop-independent operations (like fetching a full dataset) and hoist them out. For item-dependent IO operations, use `concurrent.futures.ThreadPoolExecutor` to parallelize them if async is not available.

## $(date +%Y-%m-%d) - [O(N*M) FIFO Loop Optimization]
**Learning:** During FIFO lot matching, iterating through the list of buys starting from the beginning `for lot in buys:` for every sell transaction creates O(N*M) complexity since earlier lots are repeatedly checked and skipped once exhausted.
**Action:** Use a persistent `fifo_index` initialized before the sell loop. Inside the sell loop, use `while fifo_index < len(buys):` and advance `fifo_index` whenever a lot is fully consumed. This ensures each lot is checked at most once, resulting in amortized O(1) time per sell.
