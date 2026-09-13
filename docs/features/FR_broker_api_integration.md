# Functional Requirement Specification: Broker API Integration (NFR12)

**Feature ID:** FR-NFR12-BrokerAPI  
**GitHub Issue:** [#558](https.github.com/aashishbhanawat/ArthSaarthi/issues/558)  
**Title:** Pluggable Broker Data Providers (Zerodha Kite & ICICI Breeze) with OAuth Login Flow  
**Target Release:** v1.5.0  

---

## 1. Sub-component Breakdown & Micro-Phases

### Phase 1.1: Core Abstract Provider Interface & Encryption Storage
* Define `ZerodhaKiteProvider` and `IciciBreezeProvider` extending `FinancialDataProvider`.
* Create `BrokerCredential` database model to store API keys, API secrets, access tokens, and token expiration timestamps securely.
* Implement symmetric encryption (Fernet AES-256) for API secrets and session access tokens stored in SQLite/Postgres DB.

### Phase 1.2: OAuth User Login Flow & Session Management
* Backend routes for OAuth redirect URL generation, authorization code exchange, and token refresh.
* Frontend OAuth configuration settings modal and daily login UI indicator for Zerodha Kite / ICICI Breeze.
* Background token expiry monitoring and session state indicator.

### Phase 1.3: Real-time Price & Historical Data Routing
* Route stock, ETF, and bond market data requests from `FinancialDataService` to user's active broker provider.
* Implement graceful fallback to AMFI/NSE Bhavcopy/Upstox if broker API session is unauthenticated or encounters an error.

---

## 2. Technical Specification (Backend & Frontend)

### 2.1 Backend Implementation Details
* **Provider Classes:**
  * `backend/app/services/providers/zerodha_provider.py`: Wrapper using pure-Python HTTP calls to Kite Connect REST API v3 endpoints (`https://api.kite.trade`).
  * `backend/app/services/providers/icici_breeze_provider.py`: Wrapper using HTTP calls to ICICI Breeze API v2 endpoints (`https://api.icicidirect.com/breezeapi/v1`).
* **Encryption Layer:**
  * Utilize `app/core/security.py` with `cryptography.fernet.Fernet` driven by application `SECRET_KEY`.
* **OAuth Routes:**
  * `/api/v1/broker/zerodha/login-url` & `/api/v1/broker/zerodha/callback`
  * `/api/v1/broker/icici/login-url` & `/api/v1/broker/icici/callback`

### 2.2 Frontend Implementation Details
* **Settings Component (`src/components/settings/BrokerSettings.tsx`):**
  * Section to enter API Key and API Secret for Zerodha / ICICI Direct.
  * "Connect Account" button triggering daily OAuth login popup/redirect.
  * Status badge: "Active (Expires in 14h 20m)" or "Expired - Re-authenticate".
* **Dashboard / Header Badge:**
  * Compact pill badge showing current broker data connection status.

---

## 3. Comprehensive Test Plan & Edge Cases

### 3.1 Edge Cases & Failure Scenarios
* **Expired Access Token:** Access token generated at 8:30 AM expires at midnight. The service must catch HTTP 403/401, log warning, mark status as `EXPIRED`, and fall back to public providers (AMFI/NSE/Upstox).
* **Missing API Key / Unconfigured:** User hasn't configured Kite/Breeze. Service skips broker provider and uses public fallbacks cleanly without throw/crash.
* **Network Timeout / Broker Outage:** API endpoint timeout after 3 seconds; fallback triggered seamlessly.
* **Invalid Symbol Mapping:** Symbol `RELIANCE` mapped to NSE `RELIANCE.NS` in yfinance format; provider translates symbols to Kite (`NSE:RELIANCE`) and ICICI Breeze formats.

### 3.2 Manual Testing Checklist
* [ ] Enter Zerodha API Key & Secret in Broker Settings.
* [ ] Click "Login to Zerodha", authenticate via Kite login screen, redirect back to callback.
* [ ] Verify encrypted credentials stored in DB.
* [ ] Verify real-time stock prices on Dashboard update via Kite API.
* [ ] Test token expiration behavior by artificially setting `token_expiry` to past timestamp.

---

## 4. Automated Testing Strategy

### 4.1 Backend Pytest (`backend/app/tests/services/test_broker_providers.py`)
* Mock Kite Connect / Breeze HTTP responses using `httpx` mock / `pytest-mock`.
* Test `get_current_prices()` and `get_historical_prices()` for single and batch symbols.
* Test Fernet encryption and decryption of API secrets.

### 4.2 Frontend Vitest (`src/components/settings/__tests__/BrokerSettings.test.tsx`)
* Render settings component with unconfigured state.
* Mock OAuth redirect flow and verify state updates on callback.

### 4.3 E2E Playwright (`tests/broker-integration.spec.ts`)
* Test navigating to Settings -> Broker Integration tab.
* Verify form inputs, validation, and error alert displays.

---

## 5. UX & UI Specifications
* **Modal / Settings Card:** Clean tabbed interface under `Settings -> Data Providers`.
* **Broker Cards:** Dedicated cards for Zerodha Kite and ICICI Breeze with broker logo, status pill (Connected / Disconnected / Expired), and action buttons.
* **Daily Auth Alert Banner:** Dismissible top banner appearing on dashboard if default provider token is expired in morning hours.

---

## 6. Database Schema & Data Security

### 6.1 Database Schema
New table: `broker_credentials`

```sql
CREATE TABLE broker_credentials (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider_name VARCHAR(50) NOT NULL, -- zerodha_kite, icici_breeze
    api_key VARCHAR(255) NOT NULL,
    encrypted_api_secret TEXT NOT NULL,
    encrypted_access_token TEXT NULL,
    token_issued_at TIMESTAMP WITH TIME ZONE NULL,
    token_expires_at TIMESTAMP WITH TIME ZONE NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, provider_name)
);
```

### 6.2 Encryption Requirements
* **Encrypted Columns:** `encrypted_api_secret`, `encrypted_access_token`.
* **Encryption Algorithm:** AES-256-GCM via Python `cryptography` package Fernet symmetric encryption.
* **Key Derivation:** App `SECRET_KEY` + Salt. Plaintext keys/tokens MUST NEVER be saved to SQLite or Postgres database files unencrypted.

---

## 7. Required Documentation Updates

* **README.md:** Add section on configuring optional Zerodha / ICICI Breeze API integration.
* **docs/code_flow_guide.md:** Document `FinancialDataService` provider routing and `BrokerCredential` security flow.
* **docs/workflow_history.md:** Log implementation details upon feature completion.
* **docs/debugging_guide.md:** Add troubleshooting steps for OAuth redirect errors, CORS issues, and invalid API key errors.
* **docs/project_handoff_summary.md:** Update active provider list and feature completion matrix.
* **docs/requirements.md:** Mark NFR12 as `✅ Implemented`.

---

## 8. External Data Sources & API Specifications

* **Zerodha Kite Connect:**
  * Login Auth URL: `https://kite.zerodha.com/connect/login?v=3&api_key={api_key}`
  * Token Exchange: `POST https://api.kite.trade/session/token` (checksum = sha256(api_key + request_token + api_secret))
  * Quote API: `GET https://api.kite.trade/quote?i=NSE:INFY&i=NSE:TCS`
* **ICICI Breeze API:**
  * Login Auth URL: `https://api.icicidirect.com/apihandler/index.html?API_KEY={api_key}`
  * Token Exchange: `POST https://api.icicidirect.com/breezeapi/v1/customerdetails`
  * Quote API: `GET https://api.icicidirect.com/breezeapi/v1/stockquotes`

---

## 9. File & API Endpoint Inventory

### Files to Create / Modify
* **Create:** `backend/app/models/broker_credential.py`
* **Create:** `backend/app/crud/crud_broker.py`
* **Create:** `backend/app/services/providers/zerodha_provider.py`
* **Create:** `backend/app/services/providers/icici_breeze_provider.py`
* **Create:** `backend/app/api/v1/endpoints/broker.py`
* **Create:** `frontend/src/components/settings/BrokerSettings.tsx`
* **Modify:** `backend/app/services/financial_data_service.py`
* **Modify:** `frontend/src/pages/SettingsPage.tsx`

### API Routes
* `GET /api/v1/broker/credentials` - Get user's configured broker statuses
* `POST /api/v1/broker/credentials` - Save API Key & Secret
* `POST /api/v1/broker/authenticate` - Complete OAuth token exchange
* `DELETE /api/v1/broker/credentials/{provider}` - Delete broker credentials

---

## 10. Mobile-Friendly UI & Responsive Design
* Touch-friendly OAuth button triggers (minimum 44px target height).
* Responsive form layout switching from 2-column grid on desktop to single column stacked on mobile viewports (< 768px).
* Webview / mobile browser compatible redirect handling for Android native app environment.

---

## 11. Android Compatibility & Python Library Constraints
* **Pure Python Dependencies Only:** Avoid C-extension libraries. Use standard `httpx` or `requests` for REST calls instead of native binaries.
* **Kite Connect / Breeze SDK:** Avoid complex native dependencies; use direct REST client implementation using standard `httpx` to guarantee compatibility with Chaquopy / Android embedded Python runtimes.
* **Cryptography:** Use standard Python `cryptography` wheel supported across ARM64 Android targets.
