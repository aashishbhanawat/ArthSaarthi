# Feature Plan: User Management

**Related Requirements:** FR1.2 (Admin User Management)

This document outlines the development plan for the User Management feature, which allows administrators to perform CRUD (Create, Read, Update, Delete) operations on all users in the system.

---

## 1. Backend Development Plan

This plan was created by the **Backend Developer** and **Database Administrator**.

### 1.1. Database Schema Review

**No changes** to the `users` table are necessary. The existing schema, with `is_admin` and `is_active` flags, is sufficient for the planned operations.

### 1.2. Authorization: Admin-Only Access

A new reusable dependency, `get_current_admin_user`, will be created in `app/core/dependencies.py`. This function will:
1.  Depend on `get_current_user` to retrieve the authenticated user.
2.  Check if `current_user.is_admin` is `True`.
3.  If the user is not an admin, it will raise an `HTTPException` with status `403 Forbidden`.

### 1.3. API Endpoints (FastAPI)

All endpoints will be located in `app/api/v1/endpoints/users.py` and will be protected by `Depends(get_current_admin_user)`.

*   **List Users:**
    *   **URL:** `GET /api/v1/users/`
    *   **Description:** Retrieves a paginated list of all users.
    *   **Success Response (200 OK):** `List[User]`
*   **Create User:**
    *   **URL:** `POST /api/v1/users/`
    *   **Description:** Creates a new user. Password strength will be validated by the `UserCreate` schema.
    *   **Request Body:** `UserCreate` schema.
    *   **Success Response (201 Created):** `User`
*   **Get User by ID:**
    *   **URL:** `GET /api/v1/users/{user_id}`
    *   **Description:** Retrieves a single user by their ID.
    *   **Success Response (200 OK):** `User`
    *   **Error Response (404 Not Found):** If user does not exist.
*   **Update User:**
    *   **URL:** `PUT /api/v1/users/{user_id}`
    *   **Description:** Updates an existing user's details.
    *   **Request Body:** `UserUpdate` schema.
    *   **Success Response (200 OK):** `User`
*   **Delete User:**
    *   **URL:** `DELETE /api/v1/users/{user_id}`
    *   **Description:** Deletes a user from the database.
    *   **Success Response (200 OK):** `{ "message": "User deleted successfully" }`

### 1.4. Pydantic Schemas

A new `UserUpdate` schema will be added to `app/schemas/user.py`. It will allow for partial updates by making all fields optional.

### 1.5. Proposed Backend File Changes

| File                                         | Purpose                                                      |
| :------------------------------------------- | :----------------------------------------------------------- |
| `backend/app/api/v1/endpoints/users.py`      | Add the new admin-only CRUD endpoints.                       |
| `backend/app/crud/crud_user.py`              | Add `get_by_id`, `get_multi`, `update`, and `remove` functions. |
| `backend/app/schemas/user.py`                | Add the new `UserUpdate` Pydantic schema.                    |
| `backend/app/core/dependencies.py`           | Add the `get_current_admin_user` dependency.                 |
| `backend/app/tests/api/v1/test_users_admin.py` | New test file for the admin-only user management endpoints.  |

---

## 2. Frontend Development Plan

This plan was created by the **Frontend Developer** and **UI/UX Designer**.

### 2.1. UI/UX Design & Mockup

The User Management page will be accessible to administrators at the `/admin/users` route. It will feature a table of all users with actions to "Edit" and "Delete", and a button to "Create New User". Both creating and editing will use a modal dialog.

**Mockup:**
```
+----------------------------------------------------------------------+
| PMS Navigation Bar (Logout)                       [User Management]  |
+----------------------------------------------------------------------+
|                                                                      |
|  User Management                                [Create New User]    |
|  ==================================================================  |
|  | Full Name     | Email                | Active | Admin | Actions | |
|  |---------------|----------------------|--------|-------|---------| |
|  | Admin User    | admin@example.com    |  Yes   |  Yes  | [Edit]  | |
|  | Test User 1   | test1@example.com    |  Yes   |  No   | [Edit]  | |
|                                                                      |
+----------------------------------------------------------------------+
```

### 2.2. Routing & Authorization

*   The "User Management" link in the navigation will be conditionally rendered if `auth.user.is_admin` is true.
*   A new route `/admin/users` will be protected by a wrapper component that redirects non-admins.

### 2.3. State Management & API Integration

*   **State Management:** We will use **React Query** for server state management to handle fetching, caching, and optimistic updates for the user list.
*   **API Integration:** A new service file, `frontend/src/services/adminApi.ts`, will be created to interact with the new backend endpoints.

### 2.4. Proposed Frontend File Structure

*   `frontend/src/pages/Admin/UserManagementPage.tsx`: Main page component; uses React Query to fetch users.
*   `frontend/src/components/Admin/UsersTable.tsx`: Displays the list of users and their details.
*   `frontend/src/components/Admin/UserFormModal.tsx`: Modal form for creating and editing users.
*   `frontend/src/components/Admin/DeleteConfirmationModal.tsx`: Confirmation dialog for deleting a user.
*   `frontend/src/services/adminApi.ts`: Contains API call functions (`getUsers`, `createUser`, `updateUser`, `deleteUser`).