# Task: Implement User Profile Management (FR1.5) - Rework

**AI Assistant:** Jules
**Role:** Full-Stack Developer

---

## 1. Overview

Your task is to implement the **User Profile Management (FR1.5)** feature from scratch. The previous implementation had significant UI and quality issues, so we are discarding it.

This feature will provide users with a dedicated page (`/profile`) to update their personal information (full name) and securely change their password.

Please adhere strictly to the feature plan and the quality requirements outlined below.

---

## 2. Feature Plan

This is the official plan for the feature. Please follow it precisely.

```markdown
# Feature Plan: User Profile Management (FR1.5)

**Feature ID:** FR1.5
**Status:** 📝 Planned
**Title:** User Profile Management
**User Story:** As a logged-in user, I want a dedicated profile/settings page where I can update my personal information and change my password, so that I can manage my own account details securely.

---

## 1. Objective

This document outlines the full-stack implementation plan for the "User Profile" feature. The goal is to provide a clean, intuitive, and secure interface for users to manage their own account details, specifically updating their name and changing their password. This plan replaces a previous, lower-quality implementation.

---

## 2. UI/UX Design

The User Profile page will be located at `/profile`. The design will be clean and consistent with the existing application aesthetic, using cards to separate distinct functions.

**Mockup:**
```
+--------------------------------------------------------------------+
| NavBar | Top Bar: Search [_________] [User Menu ▼]                 |
|--------|-----------------------------------------------------------|
| ...    |  User Profile                                             |
| Profile|                                                           |
| ...    |  +------------------------------------------------------+ |
|        |  | Update Profile Information                           | |
|        |  |------------------------------------------------------| |
|        |  | Full Name: [ Admin User          ]                   | |
|        |  | Email:     [ admin@example.com  ] (Read-only)       | |
|        |  |                                      [Save Changes]  | |
|        |  +------------------------------------------------------+ |
|        |                                                           |
|        |  +------------------------------------------------------+ |
|        |  | Change Password                                      | |
|        |  |------------------------------------------------------| |
|        |  | Current Password: [ ************ ]                   | |
|        |  | New Password:     [ ************ ]                   | |
|        |  | Confirm Password: [ ************ ]                   | |
|        |  |                                   [Update Password]  | |
|        |  +------------------------------------------------------+ |
+--------------------------------------------------------------------+
```

---

## 3. Backend Implementation Plan

### 3.1. Database Schema
*   **No changes are required.** The existing `users` table is sufficient.

### 3.2. API Endpoints
New endpoints will be added to handle profile updates. They will be protected by the `get_current_active_user` dependency.

*   **Update Profile Info:**
    *   **URL:** `PUT /api/v1/users/me`
    *   **Description:** Updates the current user's non-sensitive information (e.g., `full_name`).
    *   **Request Body:** `UserUpdateMe` schema.
    *   **Success Response (200 OK):** `User` schema.
*   **Change Password:**
    *   **URL:** `POST /api/v1/auth/me/change-password`
    *   **Description:** Changes the current user's password after verifying the old one. This endpoint also handles re-wrapping the master encryption key in desktop mode.
    *   **Request Body:** `UserPasswordChange` schema.
    *   **Success Response (200 OK):** `Msg` schema (`{"msg": "Password updated successfully"}`).

### 3.3. Pydantic Schemas (`app/schemas/user.py`)
*   `UserUpdateMe(BaseModel)`: Contains `full_name: Optional[str] = None`.
*   `UserPasswordChange(BaseModel)`: Contains `old_password: str` and `new_password: str`.

### 3.4. Business Logic
*   **`crud_user.py`:** A new `update_me` method will be added to handle partial updates of user data.
*   **`endpoints/auth.py`:** The `change-password` endpoint will contain the core logic:
    1.  Verify the user's `old_password`.
    2.  If in `desktop` mode, call the `key_manager` to re-encrypt the master key with the new password.
    3.  Hash the `new_password` and update the `hashed_password` in the database.

---

## 4. Frontend Implementation Plan

### 4.1. Routing & Navigation
*   **Route:** Add a new protected route for `/profile` in `frontend/src/App.tsx`.
*   **Navigation:** Add a "Profile" link to the user dropdown menu in `frontend/src/components/NavBar.tsx`.

### 4.2. New Files to Create
*   **Page:** `frontend/src/pages/ProfilePage.tsx`
*   **Components:**
    *   `frontend/src/components/Profile/UpdateProfileForm.tsx`
    *   `frontend/src/components/Profile/ChangePasswordForm.tsx`
*   **Data Layer:**
    *   `frontend/src/hooks/useProfile.ts` (or update `useUsers.ts`)
    *   `frontend/src/services/userApi.ts` (update)
*   **Tests:** Corresponding test files in `frontend/src/__tests__/`.

### 4.3. State Management (React Query)
*   Create a `useUpdateProfile` mutation hook. On success, it must update the user data in the `AuthContext` to ensure the UI (e.g., the name in the `NavBar`) updates immediately.
*   Create a `useChangePassword` mutation hook. On success, it should display a success notification.

---
## 5. Testing Plan

*   **Backend:**
    *   Add tests for `PUT /users/me` to verify successful name changes.
    *   Add tests for `POST /auth/me/change-password` covering success, incorrect old password, and password policy validation.
*   **Frontend:**
    *   Add unit tests for `UpdateProfileForm.tsx` and `ChangePasswordForm.tsx` to verify form validation and submission logic.
*   **E2E:**
    *   Create a new E2E test file `e2e/tests/profile-management.spec.ts`.
    *   The test will log in, navigate to the profile page, update the user's name, and verify the change is reflected in the `NavBar`.
    *   It will then change the user's password, log out, and verify that the user can log in with the new password.
```

---

## 3. Quality & Process Requirements

Adherence to these requirements is mandatory for task completion.

*   **UI/UX Consistency:** The new profile page **must** be visually consistent with the existing application. Use the **Dashboard, Portfolios, and Goals pages** as a reference for styling, layout, and component usage (e.g., cards, buttons, forms). The UI must be clean and professional.

*   **UI Verification via E2E Screenshots:** To help you review the final look and feel, you can add screenshot assertions to the E2E test. For example: `await expect(page).toHaveScreenshot('profile-page.png');`.

*   **Mandatory Testing:** All automated tests **must pass** before you submit your work. This includes backend, frontend, and E2E tests. Our CI/CD pipeline will block any merge requests with failing tests. You are responsible for running the tests locally to verify your changes.

*   **Documentation Updates:** As per our project standards, you must update all relevant documentation before finalizing the task. This includes updating the feature plan status, adding a `workflow_history.md` entry, and creating bug reports for any issues you fix. Use the `COMMIT_TEMPLATE.md` as a guide.

*   **Definition of Done:** This task will not be considered complete until all automated tests pass **AND** a manual E2E smoke test of the feature has been successfully performed.

---

## 4. Developer Notes & Resources

Please use these notes to help you during development and testing.

### 4.1. How to Run Tests Locally

**To avoid disk space issues, please use the local test runner script instead of Docker.**

*   **Run the entire suite:** `./run_local_tests.sh all`
*   **Run only linters:** `./run_local_tests.sh lint`
*   **Run only backend tests:** `./run_local_tests.sh backend`
*   **Run only frontend tests:** `./run_local_tests.sh frontend`
*   **Run only E2E tests:** `./run_local_tests.sh e2e`
*   **Run only migration tests:** `./run_local_tests.sh migrations`
*   **Use a PostgreSQL database:** `./run_local_tests.sh backend --db postgres`
*   **See all options:** `./run_local_tests.sh --help`

### 4.2. How to Debug E2E Tests

If you encounter failures in the E2E tests, use these Playwright debugging tools:

**Using the `playwright` object in the Console (Debug Mode):**
When Playwright is launched in debug mode (e.g., by setting `PWDEBUG=1`), a special `playwright` object becomes available in the browser's console. This object provides utilities for interacting with and inspecting elements:

*   `playwright.$(selector)`: Highlights the first occurrence of the element matching the provided selector.
*   `playwright.$$(selector)`: Highlights all occurrences of elements matching the provided selector.
*   `playwright.inspect(selector)`: Inspects the element matching the selector in the Elements panel of the DevTools.
*   `playwright.locator(selector)`: Highlights the first occurrence of the element located by the Playwright locator.
*   `playwright.clear()`: Clears any existing highlights applied by the `playwright` object.
*   `playwright.selector(element)`: Generates a Playwright selector for a given DOM element.

**Viewing Console Output from Playwright Tests:**

*   **Trace Viewer:** Playwright's Trace Viewer provides a comprehensive view of test execution, including console output, network requests, and DOM snapshots. This is particularly useful for debugging headless tests or reviewing detailed execution traces.
*   **Terminal Output:** Console logs (e.g., `console.log()`) from your Playwright tests will also appear in the terminal where you are running your tests.