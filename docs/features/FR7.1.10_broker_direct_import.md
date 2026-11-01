# Functional Requirement Specification: Direct Portfolio & Trade Statement Import via Broker APIs

**Feature ID:** FR7.1.10  
**GitHub Issue:** [#569](https://github.com/aashishbhanawat/ArthSaarthi/issues/569)  
**Title:** Direct Broker API Import (Zerodha Kite & ICICI Breeze) for Holdings and Trade Statements  
**Target Release:** v1.5.0  
**Parent Requirements:** FR7.1 (Automated Import), NFR12 (Pluggable Financial Data Service)  

---

## 1. Breakdown into Smaller Micro-Phases

### Phase 1.1: Broker API Direct Fetch Infrastructure (Backend)
* Extend `ZerodhaKiteProvider` and `IciciBreezeProvider` with direct methods to fetch current holdings (`/portfolio/holdings`) and historical/daily trade books (`/trades`, `/orders`).
* Standardize broker raw JSON payloads into ArthSaarthi's unified `ImportSession` schema (fields: `date`, `symbol`, `name`, `type`, `quantity`, `price`, `amount`, `fees`, `asset_type`, `exchange`, `isin`).

### Phase 1.2: Import Session Integration & Deduplication Backend Endpoint
* Create API endpoint `POST /api/v1/import/broker/sync` taking `provider_name` (`zerodha_kite` / `icici_breeze`), `portfolio_id`, `import_type` (`holdings` / `trade_book`), and `date_range` (`from_date`, `to_date`).
* Reuse existing `ImportSession` workflow (status tracking: `PARSED` -> `PREVIEW` -> `COMMITTED`).
* Integrate duplicate detection algorithm against existing transactions (matching date, symbol, quantity, unit price within ±0.01 margin).

### Phase 1.3: Frontend UI / UX & Integration
* Enhance the `ImportPage` (`frontend/src/pages/ImportPage.tsx`) with a dedicated "Broker Direct API Sync" card alongside file upload options.
* Provide dynamic UI state showing active broker session status (Authenticated, Daily OAuth Expired, Unconfigured).
* Re-use the unified `ImportPreviewModal` / table view allowing symbol alias mapping, transaction selection/deselection, and batch commit to target portfolios.

### Phase 1.4: Mobile (Capacitor/Android) & Offline Fallback Handling
* Ensure full responsiveness for mobile screens and mobile webview touch targets.
* Implement clear retry, token re-authentication dialog, and grace fallbacks when offline or when broker API token has expired.

---

## 2. Technical Architecture & Component Responsibilities

### 2.1 Backend Responsibilities
* **Provider Extensions (`backend/app/services/providers/`):**
  * `ZerodhaKiteProvider.fetch_holdings()`: Call `GET https://api.kite.trade/portfolio/holdings`. Parse ISIN, exchange symbol, average price, quantity, and current price.
  * `ZerodhaKiteProvider.fetch_trade_book(from_date, to_date)`: Call `GET https://api.kite.trade/trades`. Parse trade timestamp, buy/sell action, quantity, price, order ID.
  * `IciciBreezeProvider.fetch_holdings()`: Call `GET https://api.icicidirect.com/breezeapi/v1/portfolioholdings`.
  * `IciciBreezeProvider.fetch_trade_book(from_date, to_date)`: Call `GET https://api.icicidirect.com/breezeapi/v1/trades`.
* **Broker Import Converter (`backend/app/services/import_parsers/broker_api_parser.py`):**
  * Maps broker-specific asset symbols (e.g. `NSE:INFY` or ICICI stock code `INFTEC`) to ArthSaarthi Master Assets / ISINs.
  * Generates temporary parsed JSON payload stored in `import_sessions` staging folder.
* **Import Session Controller (`backend/app/api/v1/endpoints/import_sessions.py`):**
  * Spawns new `ImportSession` with `source="zerodha_api"` or `source="icici_breeze_api"`.
  * Evaluates existing user holdings/transactions to flag duplicated trades (`is_duplicate: true`).

### 2.2 Frontend Responsibilities
* **Broker Sync Card (`frontend/src/components/import/BrokerApiSyncCard.tsx`):**
  * Render broker selection dropdown / toggle pills (Zerodha Kite vs. ICICI Breeze).
  * Check user authentication status with active broker token before allowing sync.
  * Date range selector for trade statement sync (e.g. "Last 30 Days", "Current Financial Year", "Custom Range").
  * Trigger sync button displaying progress spinner and status messages.
* **Import Session Preview Component (`frontend/src/components/import/ImportSessionPreview.tsx`):**
  * Render parsed trades/holdings in an editable table.
  * Symbol resolution dropdown allowing user to assign unknown tickers or set symbol aliases.
  * "Commit to Portfolio" action updating target portfolio holdings.

---

## 3. Comprehensive Test Plan & Corner Cases

### 3.1 Edge Cases & Technical Corner Cases
1. **Token Expired / Missing Daily Authentication:**
   * User triggers direct sync when access token is expired (> 24h old or midnight invalidation).
   * *Behavior:* API returns HTTP 401/403 with detailed error `BROKER_TOKEN_EXPIRED`. Frontend displays direct "Re-authenticate with [Broker]" OAuth popup trigger.
2. **Partial / Zero Holdings Return:**
   * User account has active credentials but 0 holdings or 0 trades in selected date range.
   * *Behavior:* Gracefully handle empty list response without crashing; inform user "No new transactions found in selected date range".
3. **Symbol Ticker Mismatch (Unmapped ISIN/Ticker):**
   * Broker symbol (e.g., `GOLDBEES` or corporate name change) is not in ArthSaarthi's master asset database.
   * *Behavior:* Mark row as `UNMAPPED_SYMBOL` in preview UI; prompt user to search/select matching security or auto-create alias.
4. **Duplicate Trade Prevention:**
   * User syncs API trade statement twice in the same day or syncs trades after already uploading a broker PDF/CSV statement.
   * *Behavior:* Deduplication logic flags existing trades based on `(portfolio_id, symbol, date, quantity, unit_price)` match; pre-unchecks them in preview table.
5. **Partial Execution / Multi-fill Orders:**
   * An order of 100 shares filled in 3 separate trades (e.g. 20, 30, 50 shares) on the same day.
   * *Behavior:* Preserve individual trade executions with exact timestamps and trade IDs to maintain correct tax lot tracking.
6. **Corporate Actions & Restructuring:**
   * Holding average price adjusted by broker due to bonus/split.
   * *Behavior:* Parse average price provided by broker API; flag potential discrepancy if cumulative transactions differ from API holdings average.

### 3.2 Manual Testing Checklist
* [ ] **OAuth Pre-requisite:** Verify Zerodha / ICICI credentials are configured and authenticated in `Settings -> Broker Integration`.
* [ ] **Holdings Sync Test:** Click "Sync Holdings from Zerodha", select target portfolio, verify preview table populates with active holdings.
* [ ] **Trade Statement Sync Test:** Select custom date range (e.g., FY 2025-26), click "Sync Trade Statement", verify all buy/sell transactions appear with correct dates and quantities.
* [ ] **Deduplication Check:** Re-run sync for the same date range; verify all previously committed transactions are marked duplicate and unchecked.
* [ ] **Commit Test:** Confirm commit action; navigate to Portfolio detail page and verify holdings & transaction history update correctly.
* [ ] **Expired Token Check:** Manually invalidate access token in `broker_credentials` DB table; verify app prompts for daily OAuth login gracefully.

---

## 4. Automated Testing Strategy

### 4.1 Backend Pytest Suite
* **Unit Tests (`backend/app/tests/services/test_broker_import_parser.py`):**
  * Mock Zerodha `/portfolio/holdings` JSON response and test parsing into ArthSaarthi standardized schema.
  * Mock ICICI Breeze `/trades` response for multi-fill buy and sell orders.
  * Test duplicate detection helper functions with exact and fuzzy matching.
* **API Integration Tests (`backend/app/tests/api/v1/test_broker_sync_endpoints.py`):**
  * Test `POST /api/v1/import/broker/sync` with mocked `ZerodhaKiteProvider` / `IciciBreezeProvider`.
  * Verify HTTP 401 returned when credentials are invalid or expired.
  * Verify `ImportSession` database record creation and staging JSON output.

### 4.2 Frontend Vitest Suite
* **Component Test (`frontend/src/components/import/__tests__/BrokerApiSyncCard.test.tsx`):**
  * Render card with authenticated broker status; verify date pickers and sync button are enabled.
  * Test unauthenticated broker state displaying connection prompt.
  * Mock API error response and verify warning alert display.

### 4.3 E2E Playwright Suite
* **E2E Test (`e2e/tests/broker-direct-import.spec.ts`):**
  * Navigate to Import page -> Select Broker Sync tab.
  * Trigger mock direct sync flow for Zerodha Kite.
  * Verify preview table rows display correctly.
  * Click "Commit Transactions" and verify redirect to Portfolio Detail page with updated holdings.

---

## 5. UX & UI Specifications

* **Layout:** Tabbed interface inside `Import Page` (`/import`):
  * Tab 1: **File Upload (PDF / CSV / Excel)**
  * Tab 2: **Direct Broker API Sync (Zerodha / ICICI)**
* **Broker Sync Card Elements:**
  * **Broker Selector:** Interactive toggle pills with broker logos (Zerodha Kite & ICICI Breeze).
  * **Authentication Status Badge:** 
    * `Connected` (Green pill with expiration countdown timer: e.g., "Active - expires in 12h")
    * `Needs Login` (Yellow pill with "Daily Login Required" button)
    * `Not Configured` (Gray pill linking to Settings)
  * **Import Mode Selection:**
    * Radio 1: *Current Portfolio Holdings* (Snapshots current position & average buy price)
    * Radio 2: *Trade History Statement* (Imports historical granular Buy/Sell transactions)
  * **Target Portfolio Dropdown:** Select target goal portfolio (e.g. "Retirement", "Trading").
* **Preview & Review Drawer / Table:**
  * Displays parsed rows with indicators: `New`, `Duplicate (Skip)`, `Unmapped Ticker`.
  * Select All / Deselect All checkboxes.
  * Sticky bottom action bar with total selected count and "Commit Import" primary button.

---

## 6. Database Schema & Security Requirements

### 6.1 Database Schema Updates

No new table required if using `broker_credentials` (NFR12), but update `import_sessions` to support API source metadata:

```sql
-- Update import_sessions table source check constraint or enum:
-- source values: 'zerodha_csv', 'icici_pdf', 'cams_pdf', 'zerodha_api', 'icici_breeze_api'

ALTER TABLE import_sessions 
ADD COLUMN broker_sync_metadata JSON NULL; -- Stores sync date range, raw response status, and batch IDs
```

### 6.2 Data Security & Encryption Standards
* **Encrypted Columns (SQLite & PostgreSQL):**
  * `broker_credentials.encrypted_api_secret` (AES-256 Fernet)
  * `broker_credentials.encrypted_access_token` (AES-256 Fernet)
* **Key Management:** Encrypted via `app/core/security.py` using symmetric key derived from application `SECRET_KEY`. Plaintext tokens MUST NEVER be stored on disk or logged in server output logs.
* **Transient Staging File Security:** Temporary parsed import JSON files (`import_sessions/parsed_{session_id}.json`) must be restricted to file permission `0600` and deleted automatically after commit or 24-hour expiration.

---

## 7. Documentation Update Requirements

1. **README.md:**
   * Add section detailing Direct Broker API Sync capabilities for Zerodha Kite and ICICI Breeze.
2. **`docs/code_flow_guide.md` & `docs/uml_design.md`:**
   * Document sequence diagram for `Frontend UI` -> `Import API Endpoint` -> `Broker Provider` -> `Import Session Staging` -> `Transaction Commit`.
3. **`docs/workflow_history.md`:**
   * Record entry upon feature delivery outlining files modified and test execution output.
4. **`docs/troubleshooting.md` / `docs/debugging_guide.md`:**
   * Add troubleshooting guide for OAuth token expiry, CORS errors on mobile, rate limit responses from Kite/Breeze, and symbol mapping failures.
5. **`docs/project_handoff_summary.md`:**
   * Update feature matrix marking direct broker import as active.
6. **`docs/requirements.md`:**
   * Update `FR7.1.1` and add `FR7.1.10` with `✅ Done` / `📝 Planned` status.

---

## 8. Required External Data Sources & API Endpoints

### 8.1 Zerodha Kite Connect REST API (v3)
* **Holdings API:** `GET https://api.kite.trade/portfolio/holdings`
  * Header: `Authorization: token {api_key}:{access_token}`
* **Trades API:** `GET https://api.kite.trade/trades`
  * Header: `Authorization: token {api_key}:{access_token}`
* **Orders API:** `GET https://api.kite.trade/orders`

### 8.2 ICICI Breeze REST API (v2)
* **Portfolio Holdings API:** `GET https://api.icicidirect.com/breezeapi/v1/portfolioholdings`
  * Headers: `X-ApiKey`, `X-SessionToken`, `X-Timestamp`, `X-Checksum`
* **Trade Book API:** `GET https://api.icicidirect.com/breezeapi/v1/trades`

---

## 9. File & API Endpoint Inventory

### Files to Create / Modify
* **Backend:**
  * Create: `backend/app/services/import_parsers/broker_api_parser.py`
  * Modify: `backend/app/services/providers/zerodha_provider.py` (Add `fetch_holdings`, `fetch_trades`)
  * Modify: `backend/app/services/providers/icici_breeze_provider.py` (Add `fetch_holdings`, `fetch_trades`)
  * Modify: `backend/app/api/v1/endpoints/import_sessions.py` (Add `/broker/sync` endpoint)
  * Create: `backend/app/tests/services/test_broker_import_parser.py`
  * Create: `backend/app/tests/api/v1/test_broker_sync_endpoints.py`
* **Frontend:**
  * Create: `frontend/src/components/import/BrokerApiSyncCard.tsx`
  * Modify: `frontend/src/pages/ImportPage.tsx`
  * Modify: `frontend/src/services/api.ts` (Add broker sync service methods)
  * Create: `e2e/tests/broker-direct-import.spec.ts`

### New / Updated API Routes
* `POST /api/v1/import-sessions/broker/sync` - Trigger direct API sync from broker to create import session.
* `GET /api/v1/import-sessions/{session_id}/broker-preview` - Get parsed broker holdings/trades preview with duplicate detection metadata.

---

## 10. Mobile-Friendly UI & Responsive Design

* **Target Touch Controls:** Buttons and dropdown selectors optimized for mobile touch targets (minimum 44x44px).
* **Viewport Adaptability:** Responsive flexbox/grid layout adjusting from 2-column desktop cards to single-column stacked view on mobile screens (< 768px width).
* **Capacitor / Mobile Webview Compatibility:** 
  * OAuth authentication triggers handle in-app browser tabs / native deep-links smoothly.
  * Status banners designed for high readability on small screens without overlapping navigation bars.

---

## 11. Android Compatibility & Python Library Constraints

* **Pure Python Dependencies:** All broker API clients and parsers must use standard `httpx` / `urllib` HTTP libraries.
* **No Binary Native C Extensions:** Standardize on libraries that compile cleanly with `Chaquopy` / Android embedded Python runtimes.
* **Cryptography Compatibility:** Use standard Python `cryptography` package with pre-built Android ARM64 wheels for Fernet symmetric encryption.
