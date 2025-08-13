# Feature Plan: Core User Authentication for ArthSaarthi

This document outlines the development plan for the Core User Authentication feature.

**Related Requirements:** FR1, NFR1

## 1. Backend Development Plan

This plan was created by the **Backend Developer** and **Database Administrator**.

### 1.1. Authentication Strategy

We will use **JWT (JSON Web Tokens)** as specified in NFR1. Its stateless nature is ideal for our client-server architecture. We will implement short-lived access tokens for security.

### 1.2. Database Schema (PostgreSQL)

A new table named `users` will be created.

| Column Name       | Data Type           | Constraints                               | Description                               |
| ----------------- | ------------------- | ----------------------------------------- | ----------------------------------------- |
| `id`              | `Integer`           | `PRIMARY KEY`, `INDEX`                    | Unique identifier for the user.           |
| `full_name`       | `String`            | `NOT NULL`                                | The user's full name.                     |
| `email`           | `String`            | `UNIQUE`, `NOT NULL`, `INDEX`             | The user's email, used for login.         |
| `hashed_password` | `String`            | `NOT NULL`                                | The user's securely hashed password.      |
| `is_admin`        | `Boolean`           | `DEFAULT FALSE`, `NOT NULL`               | Flag to identify administrator users.     |
| `is_active`       | `Boolean`           | `DEFAULT TRUE`                            | For soft-deleting or deactivating users.  |
| `created_at`      | `TIMESTAMP(timezone)` | `NOT NULL`, `SERVER_DEFAULT(now())`       | Timestamp of user creation.               |
| `updated_at`      | `TIMESTAMP(timezone)` | `NOT NULL`, `SERVER_DEFAULT(now())`, `ON UPDATE` | Timestamp of the last update.             |

### 1.3. API Endpoints (FastAPI)

**Endpoint 1: Initial Admin Setup**
*   **URL:** `POST /api/v1/auth/setup`
*   **Description:** Creates the first administrator account. This endpoint will only succeed if there are no other users in the database.
*   **Request Body (`UserCreate` schema):** `{ "email": "...", "password": "...", "full_name": "..." }`
*   **Success Response (201 Created):** The new user object (without password).
*   **Error Response (409 Conflict):** If a user account already exists.

**Endpoint 2: User Login**
*   **URL:** `POST /api/v1/auth/login`
*   **Description:** Authenticates any active user and returns a JWT.
*   **Request Body (OAuth2PasswordRequestForm):** Form data with `username` (email) and `password`.
*   **Success Response (200 OK):** `{ "access_token": "...", "token_type": "bearer" }`
*   **Error Response (401 Unauthorized):** If credentials are incorrect or the user is inactive.

**Endpoint 3: Get Current User**
*   **URL:** `GET /api/v1/users/me`
*   **Description:** A protected endpoint to fetch the profile of the currently authenticated user.
*   **Authorization:** Requires a valid JWT in the `Authorization: Bearer <token>` header.
*   **Success Response (200 OK):** The current user object (without password).

### 1.4. Backend Logic Overview

*   **Password Policy:** A strict password policy will be enforced on user creation (`/setup` and future admin user creation endpoints) via a Pydantic validator. The password must contain:
    *   At least 8 characters
    *   At least one uppercase letter
    *   At least one lowercase letter
    *   At least one number
    *   At least one special character

*   **Initial Setup (`/setup`):**
    1.  Check if any records exist in the `users` table. If yes, raise an HTTP 409 Conflict error.
    2.  Hash the provided password using `bcrypt`.
    3.  Create a new user record with `is_admin` set to `True`.
    4.  Return the newly created user object.
*   **Login (`/login`):**
    1.  Retrieve the user from the database by email.
    2.  Verify the provided password against the stored hash.
    3.  If passwords match, generate a JWT access token.
    4.  Return the access token.

### 1.5. Proposed Backend File Structure

*   `app/models/user.py`: SQLAlchemy `User` model.
*   `app/schemas/user.py`: Pydantic schemas (`User`, `UserCreate`, `Token`).
*   `app/crud/crud_user.py`: Reusable database functions for the `User` model.
*   `app/core/security.py`: Password hashing and JWT helper functions.
*   `app/api/v1/endpoints/auth.py`: Router for `/setup` and `/login` endpoints.
*   `app/api/v1/endpoints/users.py`: Router for `/users/me` endpoint.
*   `app/core/dependencies.py`: Dependency injection functions (e.g., `get_current_user`).

---