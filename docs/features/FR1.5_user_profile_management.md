# Feature Plan: User Profile Management (FR1.5)

**Feature ID:** FR1.5
**Title:** User Profile Management
**User Story:** As a logged-in user, I want a dedicated profile/settings page where I can update my personal information and change my password, so that I can manage my own account details securely.

---

## 1. Objective

This document outlines the implementation plan for creating a full-stack "User Profile" feature. This will involve creating a new page on the frontend and corresponding new endpoints on the backend. The feature will be developed in two phases to manage complexity.

---

## 2. Technical Design & Architecture

This feature will add a new user-facing page and protected backend endpoints.

### 2.1. Backend

*   **API Endpoints:** New `PUT` endpoints will be added to the existing `users.py` router. These endpoints will be protected by the `get_current_user` dependency to ensure users can only modify their own data.
*   **Pydantic Schemas:** New schemas will be created in `app/schemas/user.py` to handle the specific data required for profile updates and password changes.
*   **CRUD Logic:** New methods will be added to `app/crud/crud_user.py` to handle the business logic of updating user information and verifying/updating passwords.

### 2.2. Frontend

*   **Routing:** A new route `/profile` will be added to `App.tsx` and protected by the `ProtectedRoute`.
*   **Navigation:** A link to the new `/profile` page will be added to the user dropdown menu in the `NavBar.tsx` component.
*   **Page:** A new `ProfilePage.tsx` will be created to serve as the main container for this feature.
*   **Components:** The page will contain two primary form components: `UpdateProfileForm.tsx` and `ChangePasswordForm.tsx`.
*   **Data Layer:** The existing `useUsers.ts` hook file will be updated with new React Query mutations (`useUpdateMe`, `useUpdatePassword`) to interact with the new backend endpoints. The `userApi.ts` service will be updated accordingly.

---

## 3. Implementation Plan

### Phase 1: Update Profile Information (FR1.5.1)

**Objective:** Allow a user to update their `full_name`.

#### 3.1. Backend Steps

1.  **Schema:** In `app/schemas/user.py`, create a `UserUpdateMe` schema with a single optional field: `full_name: Optional[str] = None`.
2.  **CRUD:** In `app/crud/crud_user.py`, add a new method `update_me` to the `CRUDUser` class. This method will take a `User` object and the `UserUpdateMe` payload, update the user's `full_name`, and commit the change.
3.  **API Endpoint:** In `app/api/v1/endpoints/users.py`, add a new endpoint:
   `PUT /users/me`
   -   It will be protected by `deps.get_current_user`.
   -   It will accept a `UserUpdateMe` payload.
   -   It will call `crud.user.update_me` and return the updated `schemas.User` object.

#### 3.2. Frontend Steps

1.  **Page:** Create `frontend/src/pages/ProfilePage.tsx`. This page will render the two form components in separate cards.
2.  **Component:** Create `frontend/src/components/Profile/UpdateProfileForm.tsx`. This form will have a single input for "Full Name" and a "Save" button. It will be pre-populated with the user's current full name from the `AuthContext`.
3.  **API Service:** In `frontend/src/services/userApi.ts`, add a new `updateMe` function that sends a `PUT` request to `/api/v1/users/me`.
4.  **Hook:** In `frontend/src/hooks/useUsers.ts`, create a `useUpdateMe` mutation hook that uses the `updateMe` service function. On success, it should update the user data in the `AuthContext`.
5.  **Navigation:** Add a "Profile" link to the user dropdown menu in `NavBar.tsx`.
6.  **Routing:** Add the route for `/profile` in `App.tsx`, protected by `ProtectedRoute`.

---

### Phase 2: Change Password (FR1.5.2)

**Objective:** Allow a user to change their password.

#### 3.3. Backend Steps

1.  **Schema:** In `app/schemas/user.py`, create a `UserUpdatePassword` schema with two fields: `current_password: str` and `new_password: str`.
2.  **API Endpoint:** The existing endpoint `POST /api/v1/auth/me/change-password` in `app/api/v1/endpoints/auth.py` will be used. Its logic must be enhanced to handle key re-wrapping.
    -   It will be protected by `deps.get_current_active_user`.
    -   It will accept a `UserPasswordChange` payload containing `old_password` and `new_password`.
    -   **Step 1: Verify Old Password.** The endpoint first verifies that the provided `old_password` is correct for the current user.
    -   **Step 2: Handle Desktop Mode Encryption.**
        -   If `settings.DEPLOYMENT_MODE == "desktop"`, the endpoint will call `key_manager.change_password(old_password, new_password)`.
        -   This `key_manager` method uses the old password to decrypt the master key, then re-encrypts it with a key derived from the new password.
        -   If this process fails, an HTTP 400 error is returned.
    -   **Step 3: Update Password Hash.** The endpoint will hash the `new_password` and update the `hashed_password` field for the user in the database.
    -   **Step 4: Commit & Respond.** The transaction is committed, and a success message is returned.

#### 3.4. Frontend Steps

1.  **Component:** Create `frontend/src/components/Profile/ChangePasswordForm.tsx`. This form will have inputs for "Current Password", "New Password", and "Confirm New Password", along with a "Change Password" button.
2.  **API Service:** In `frontend/src/services/userApi.ts`, add a new `updatePassword` function that sends a `POST` request to `/api/v1/auth/me/change-password`.
3.  **Hook:** In `frontend/src/hooks/useUsers.ts`, create a `useUpdatePassword` mutation hook that uses the `updatePassword` service function.

---

## 4. Testing Plan

*   **Backend:**
    *   Add new tests to `app/tests/api/v1/test_users.py` to cover the new `PUT /users/me` and `PUT /users/me/password` endpoints.
    *   Tests should cover success cases, unauthorized access (401), and incorrect current password (400).
*   **Frontend:**
    *   Add new test suites for `ProfilePage.tsx`, `UpdateProfileForm.tsx`, and `ChangePasswordForm.tsx`.
    *   Tests should verify correct form rendering, submission, and handling of success and error states from the mocked API hooks.
*   **E2E:**
    *   Create a new E2E test file `e2e/tests/profile-management.spec.ts`.
    *   The test will log in, navigate to the profile page, update the user's name, and verify the change is reflected in the `NavBar`.
    *   It will then change the user's password, log out, and verify that the user can log in with the new password.
