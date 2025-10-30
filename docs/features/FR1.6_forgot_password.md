# Feature Plan: Forgotten Password Reset (FR1.6)

**Feature ID:** FR1.6
**Status:** 📝 Planned
**Title:** Forgotten Password Reset
**User Story:** As a user who has forgotten my password, I want to be able to securely reset it via my registered email address, so that I can regain access to my account.

---

## 1. Objective

This document outlines the full-stack implementation plan for a secure "Forgotten Password" feature. The flow will involve the user requesting a reset, receiving a time-sensitive token via email, and using that token to set a new password.

---

## 2. Deployment Mode Considerations

This feature's implementation differs significantly between the multi-user **Server Mode** and the single-user **Desktop Mode**.

*   **Server Mode (Production):** This is the primary target for this feature. The **application administrator** (the person self-hosting the application) is responsible for configuring the SMTP server details in the `.env.prod` file. **End-users do not need to configure anything;** they simply use the feature.
*   **Server Mode (Development):** The email service will be a mock that prints the reset link to the console logs, allowing developers to test the full flow without a real email server.
*   **Desktop Mode:** A traditional email-based password reset is **not feasible** as it would require every user to configure their own SMTP server, which is unreasonable. For the desktop application, password recovery is **out of scope**. If a user forgets their password, their encrypted data will be inaccessible. This is a known trade-off for the enhanced privacy and self-contained nature of the desktop app. A clear warning about this should be displayed during the initial setup.

---

## 3. High-Level User Flow (Server Mode)

1.  User clicks the "Forgot Password?" link on the login page.
2.  User is taken to a page where they enter their registered email address.
3.  The system generates a secure, single-use, time-limited reset token, stores its hash in the database, and sends an email to the user containing a link with the token (e.g., `/reset-password?token=...`).
4.  User clicks the link in the email.
5.  User is taken to a page where they can enter and confirm their new password.
6.  On submission, the system validates the token, updates the user's password, and invalidates the token.
7.  User is redirected to the login page to sign in with their new password.

---

## 4. Backend Implementation Plan (Server Mode)

### 3.1. Database Schema (`models/password_reset_token.py`)

A new table is required to securely store password reset tokens.

| Column Name      | Data Type | Constraints                               | Description                                      |
| ---------------- | --------- | ----------------------------------------- | ------------------------------------------------ |
| `id`             | `UUID`    | `PRIMARY KEY`                             | Unique identifier for the token record.          |
| `user_id`        | `UUID`    | `FOREIGN KEY (users.id)`, `NOT NULL`      | The user who requested the reset.                |
| `token_hash`     | `String`  | `NOT NULL`, `UNIQUE`, `INDEXED`           | The securely hashed reset token.                 |
| `expires_at`     | `TIMESTAMP` | `NOT NULL`                                | The timestamp when the token becomes invalid.    |
| `created_at`     | `TIMESTAMP` | `NOT NULL`, `SERVER_DEFAULT(now())`       | Timestamp of when the token was created.         |
| `is_used`        | `Boolean` | `NOT NULL`, `DEFAULT(False)`              | Flag to indicate if the token has been used.     |

### 3.2. API Endpoints

*   **Request Password Reset:**
    *   **URL:** `POST /api/v1/auth/password-recovery/{email}`
    *   **Description:** Initiates the password recovery process for a user.
    *   **Request Body:** None.
    *   **Success Response (200 OK):** `Msg` schema (`{"msg": "Password recovery email sent"}`).
    *   **Logic:**
        1.  Find the user by email. If not found, return success to prevent user enumeration.
        2.  Generate a secure token.
        3.  Hash the token and store the hash, `user_id`, and expiry date (e.g., 1 hour from now) in the `password_reset_tokens` table.
        4.  Call the email service to send the reset link to the user's email address.

*   **Reset Password:**
    *   **URL:** `POST /api/v1/auth/reset-password/`
    *   **Description:** Sets a new password for a user using a valid reset token.
    *   **Request Body:** `ResetPassword` schema (`token: str`, `new_password: str`).
    *   **Success Response (200 OK):** `Msg` schema (`{"msg": "Password updated successfully"}`).
    *   **Logic:**
        1.  Hash the incoming `token`.
        2.  Find the corresponding record in the `password_reset_tokens` table.
        3.  Validate that the token exists, has not expired, and has not been used.
        4.  If valid, hash the `new_password` and update the user's record.
        5.  Mark the token as used (`is_used = True`).
        6.  If in `desktop` mode, re-wrap the master encryption key with the new password.

### 3.3. Pydantic Schemas
*   `ResetPassword(BaseModel)`: Contains `token: str` and `new_password: str`.

### 3.4. Email Service Integration

A new email service will be created to handle sending the password reset link.

*   **New File:** `backend/app/core/email.py`
*   **Development/Test Mode:**
    *   If `ENVIRONMENT` is `test` or `development`, the email service will be a **mock**.
    *   It will not send a real email. Instead, it will print the email content (recipient, subject, and body with the reset link) to the console log. This allows for easy testing without a mail server.
*   **Production Mode:**
    *   If `ENVIRONMENT` is `production`, the service will connect to a real SMTP server.
    *   This will require new environment variables in `.env.prod`:
        *   `SMTP_HOST`: The SMTP server hostname.
        *   `SMTP_PORT`: The SMTP server port.
        *   `SMTP_USER`: The username for authentication.
        *   `SMTP_PASSWORD`: The password for authentication.
        *   `EMAILS_FROM_EMAIL`: The "From" address for outgoing emails.
        *   `EMAILS_FROM_NAME`: The "From" name for outgoing emails.

---

## 5. Frontend Implementation Plan (Server Mode)

### 4.1. New Files to Create
*   **Pages:** `frontend/src/pages/ForgotPasswordPage.tsx`, `frontend/src/pages/ResetPasswordPage.tsx`
*   **Data Layer:**
    *   Update `frontend/src/services/authApi.ts` with `requestPasswordReset` and `resetPassword` functions.
    *   Update `frontend/src/hooks/useAuth.ts` with `useRequestPasswordReset` and `useResetPassword` mutation hooks.

### 4.2. UI Components & Flow
1.  **Login Page:** Add a "Forgot Password?" link below the sign-in button.
2.  **`ForgotPasswordPage.tsx`:** A simple page with a single email input field and a "Send Reset Link" button. On success, it should show a confirmation message.
3.  **`ResetPasswordPage.tsx`:** A page with "New Password" and "Confirm New Password" fields. It will get the `token` from the URL query parameters. On success, it should show a success message and a link to the login page.

---

## 6. Testing Plan

*   **Backend:**
    *   Unit tests for token generation and hashing.
    *   Integration tests for the `/password-recovery` and `/reset-password` endpoints, covering success cases, invalid/expired tokens, and attempting to reuse a token.
*   **Frontend:**
    *   Unit tests for the new pages to verify form validation and submission logic.
*   **E2E:**
    *   Create a new test file `e2e/tests/forgot-password.spec.ts`.
    *   The test will:
        1.  Create a user via API.
        2.  Navigate to the "Forgot Password" page and submit the user's email.
        3.  **Challenge:** Fetch the reset token (e.g., from a new testing-only backend endpoint or by parsing backend logs).
        4.  Navigate to the reset page with the token.
        5.  Submit a new password.
        6.  Verify that login fails with the old password and succeeds with the new password.