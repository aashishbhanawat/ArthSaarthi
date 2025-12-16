# Feature Plan: Manual Asset Seeding Trigger

**Status:** ✅ Done
**Feature ID:** FR2.3
**Title:** Manual Trigger for Asset Master Seeding via UI

## 1. Objective

Enable administrators to update the system's asset master data (Stocks, Mutual Funds, Bonds) on-demand from the user interface, eliminating the need to restart the application container to fetch the latest market data.

## 2. User Story

As an **Administrator**, I want to **click a button in the Admin Settings** to **download and parse the latest asset files from NSDL, BSE, and AMFI**, so that **newly listed assets are available for users immediately without server downtime**.

## 3. Functional Requirements

1.  **Admin-Only Access:** Only users with `is_admin=True` can trigger this action.
2.  **UI Control:** A dedicated "Update Asset Master" button in the Admin Dashboard or Settings page.
3.  **Feedback Mechanism:**
    *   The UI should show a "Processing..." state or disable the button while the request is being initiated.
    *   Since seeding involves downloading and parsing large files (Bhavcopies), the actual processing must happen in the background to avoid timeouts.
    *   The UI should display a notification (Toast) confirming that the background task has started.
4.  **Concurrency Control:** The system should prevent multiple seeding jobs from running simultaneously to avoid database contention or duplicate processing.

## 4. Technical Implementation

### 4.1. Backend

*   **New Endpoint:** `POST /api/v1/admin/assets/sync`
*   **Permissions:** Restricted to Superusers (`deps.get_current_active_superuser`).
*   **Rate Limiting:** Max 1 request per 5 minutes. Use `CacheService` to store the timestamp.
*   **Logic:**
    1.  Check `CacheService` for rate limiting key. If exists, return `429`.
    2.  Trigger the `AssetSeeder.seed_assets()` method synchronously.
    3.  Return `200 OK` with the summary of processed items.
    4.  Set rate limit key in cache with 5-minute expiry.
*   **Service Reuse:** Leverage the existing `backend/app/services/asset_seeder.py` which already handles the logic for downloading and parsing files from NSDL/BSE.

**Response Payload:**
```json
{
  "status": "success",
  "data": {
    "total_processed": 500,
    "newly_added": 12,
    "updated": 488,
    "timestamp": "2025-12-15T10:00:00Z"
  }
}
```

### 4.2. Frontend

*   **Location:** Add a new "System Maintenance" card or section in the existing Admin Dashboard (`frontend/src/pages/AdminPage.tsx` or similar).
*   **Component:**
    *   Button: "Update Asset Master Data".
    *   Description: "Downloads latest equity and bond lists from exchanges. This process runs in the background."
*   **Interaction:**
    *   On click, call the new API endpoint.
    *   Handle `200`: Show success toast with counts: "Sync Complete: 12 Added, 488 Updated."
    *   Handle `429`: Show warning toast "Please wait before syncing again."
    *   Handle `403`: Show error "Unauthorized."

## 5. Acceptance Criteria

*   **Scenario 1 (Success):** Admin clicks "Update Assets". API returns 200. UI shows success toast with counts.
*   **Scenario 2 (Rate Limit):** Admin clicks "Update Assets" twice in rapid succession. The second request returns 429, and the UI informs the user to wait.
*   **Scenario 3 (Security):** A non-admin user attempts to call the endpoint via curl/Postman and receives a 403 Forbidden response.
*   **Scenario 4 (Availability):** After the background task completes, a newly listed stock (not present before) is searchable in the "Add Transaction" modal.

## 6. UI/UX Flow

1.  **Navigation:** The Admin user logs in and navigates to the **Admin Dashboard** (or Settings page).
2.  **Discovery:** The user sees a new section titled **"System Maintenance"**.
3.  **Action:** Inside this section, there is a button labeled **"Update Asset Master Data"** with a description explaining that it downloads the latest market data.
4.  **Interaction:**
    *   **Click:** The user clicks the button.
    *   **Loading State:** The button immediately enters a disabled/loading state to prevent double-clicks.
5.  **Feedback:**
    *   **Success:** A toast notification appears: *"Asset update started in background."*
    *   **Conflict:** If a job is already running, a warning toast appears: *"Update already in progress."*
    *   **Error:** If the server fails to start the task, an error toast appears.
6.  **Completion:** Since this is a background task, there is no immediate "Finished" popup. The user can verify success by searching for a new asset in the "Add Transaction" modal later.

## 7. Testing Strategy

### 7.1. Backend Tests (`pytest`)
*   **Security (`test_admin.py`):**
    *   Attempt to call `POST /api/v1/admin/seed-assets` as a **normal user**. Assert `403 Forbidden`.
    *   Attempt to call it as an **admin**. Assert `202 Accepted`.
*   **Functionality:**
    *   Mock the `AssetSeeder.seed_assets` method. Call the endpoint and verify the mock was called as a `BackgroundTask`.
*   **Concurrency:**
    *   Mock the locking mechanism (if implemented). Simulate a running job and assert the endpoint returns `409 Conflict`.

### 7.2. Frontend Tests (`jest` / `React Testing Library`)
*   **Component Rendering:** Verify the "Update Asset Master Data" button renders correctly on the Admin page.
*   **Interaction:**
    *   Mock the API response to return `202`.
    *   Simulate a click.
    *   Assert the button becomes disabled.
    *   Assert the success toast is displayed.
*   **Error Handling:**
    *   Mock the API to return `409` or `500`.
    *   Simulate a click.
    *   Assert the appropriate error toast is displayed.

### 7.3. End-to-End Tests (`Playwright`)
*   **Happy Path:**
    1.  Log in as Admin.
    2.  Go to Admin Dashboard.
    3.  Click "Update Asset Master Data".
    4.  Wait for the "Update started" toast to appear.