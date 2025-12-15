# Feature Plan: Manual Asset Seeding Trigger

**Status:** 🚧 Proposed
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

*   **New Endpoint:** `POST /api/v1/admin/seed-assets`
*   **Permissions:** Restricted to Superusers (`deps.get_current_active_superuser`).
*   **Logic:**
    1.  Check if a seeding job is currently in progress (using a Redis lock or application state).
    2.  If free, trigger the `AssetSeeder.seed_assets()` method using FastAPI's `BackgroundTasks`.
    3.  Return `202 Accepted` immediately with a message "Asset seeding started."
    4.  If locked/busy, return `409 Conflict` with "Seeding already in progress."
*   **Service Reuse:** Leverage the existing `backend/app/services/asset_seeder.py` which already handles the logic for downloading and parsing files from NSDL/BSE.

### 4.2. Frontend

*   **Location:** Add a new "System Maintenance" card or section in the existing Admin Dashboard (`frontend/src/pages/AdminPage.tsx` or similar).
*   **Component:**
    *   Button: "Update Asset Master Data".
    *   Description: "Downloads latest equity and bond lists from exchanges. This process runs in the background."
*   **Interaction:**
    *   On click, call the new API endpoint.
    *   Handle `202`: Show success toast "Update started. Check logs for progress."
    *   Handle `409`: Show warning toast "Update already in progress."
    *   Handle `403`: Show error "Unauthorized."

## 5. Acceptance Criteria

*   **Scenario 1 (Success):** Admin clicks "Update Assets". API returns 202. UI shows success toast. Server logs indicate that `AssetSeeder` has started downloading files.
*   **Scenario 2 (Concurrency):** Admin clicks "Update Assets" twice in rapid succession. The second request returns 409 (or is gracefully ignored), and the UI informs the user that a job is already running.
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