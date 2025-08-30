# Feature Plan: User Profile Management (FR1.5)

**Feature ID:** FR1.5
**Status:** ✅ Done
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
*   **`core/key_manager.py`:** During implementation, a critical bug was discovered and fixed in this module. The `change_password` method was incorrectly generating a new master key instead of re-wrapping the existing one, which would have led to data loss. The logic was refactored to ensure the same key is preserved.

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
