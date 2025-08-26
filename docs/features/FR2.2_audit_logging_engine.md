# Feature Plan: Audit Logging Engine (FR2.2)

**Feature ID:** FR2.2
**Title:** Audit Logging Engine
**User Story:** As an administrator, I need a secure and detailed audit trail of all security-sensitive events, so that I can monitor for suspicious activity, troubleshoot issues, and ensure compliance.

---

## 1. Objective

To design and implement a robust, backend-only audit logging system. This system will record key events to a persistent database table. This feature is foundational for future enhancements like an admin-facing log viewer (FR2.3).

---

## 2. Technical Design & Architecture

The audit logging engine will be a self-contained service that can be called from anywhere in the backend.

### 2.1. Database Schema

A new table, `audit_logs`, will be created to store all audit trail records.

| Column Name   | Data Type         | Constraints                               | Description                                                                    |
| :------------ | :---------------- | :---------------------------------------- | :----------------------------------------------------------------------------- |
| `id`          | `UUID`            | `PRIMARY KEY`                             | Unique identifier for the log entry.                                           |
| `user_id`     | `UUID`            | `FOREIGN KEY (users.id)`, `NULLABLE`      | The user who performed the action. Null for system events or failed logins.    |
| `event_type`  | `String`          | `NOT NULL`                                | A machine-readable event type (e.g., 'USER_LOGIN_SUCCESS').                    |
| `details`     | `JSONB`           | `NULLABLE`                                | A JSON object for storing contextual data (e.g., target user ID, session ID).  |
| `ip_address`  | `String`          | `NULLABLE`                                | The IP address of the client that initiated the event.                         |
| `timestamp`   | `TIMESTAMP(timezone=True)` | `NOT NULL`, `SERVER_DEFAULT(now())`       | The exact time the event occurred.                                             |

### 2.2. Service Layer

A new service will be created to abstract the logging logic.

*   **Module:** `backend/app/services/audit_logger.py`
*   **Core Function:** `log_event(db: Session, event_type: str, ...)`
*   **Responsibility:** This function will be the single point of entry for creating audit logs. It will construct an `AuditLog` object and save it to the database using a dedicated CRUD module.

### 2.3. Integration Strategy

The `log_event` function will be called from the API endpoint layer at the point where an auditable event occurs.

*   **Example (Login):** In `endpoints/auth.py`, after a login attempt, `log_event` will be called with the event type `'USER_LOGIN_SUCCESS'` or `'USER_LOGIN_FAILURE'`.
*   **IP Address:** The client's IP address will be retrieved from the FastAPI `Request` object and passed to the `log_event` function.

---

## 3. Implementation Plan

### Phase 1: Backend Foundation

1.  **Model:** Create `backend/app/models/audit_log.py` with the `AuditLog` SQLAlchemy model.
2.  **Schema:** Create `backend/app/schemas/audit_log.py` with the necessary Pydantic schemas for creating and reading log entries.
3.  **CRUD:** Create `backend/app/crud/crud_audit_log.py` with a `create` method.
4.  **Migration:** Generate a new Alembic migration script to create the `audit_logs` table in the database.

### Phase 2: Service & Integration

1.  **Service:** Implement the `log_event` function in `backend/app/services/audit_logger.py`.
2.  **Login Events:**
    *   Modify `backend/app/api/v1/endpoints/auth.py`.
    *   Inject the `Request` object into the `/login` endpoint.
    *   Call `log_event` after successful and failed login attempts, passing the user's email and IP address.
3.  **User Management Events:**
    *   Modify `backend/app/api/v1/endpoints/users.py`.
    *   Call `log_event` in the `create_user` and `delete_user` endpoints, logging the acting admin and the target user.

---

## 4. Testing Plan

*   **Unit Tests:**
    *   Add a test for the `log_event` service to ensure it correctly calls the CRUD `create` method with the right data.
*   **Integration Tests:**
    *   **`test_auth.py`:**
        *   After a successful login test, add an assertion to query the `audit_logs` table and verify that a `USER_LOGIN_SUCCESS` log was created with the correct `user_id` and `ip_address`.
        *   After a failed login test, verify a `USER_LOGIN_FAILURE` log was created.
    *   **`test_users_admin.py`:**
        *   After the test for creating a user, verify a `USER_CREATED` log exists.
        *   After the test for deleting a user, verify a `USER_DELETED` log exists.

---

This plan provides a clear, backend-focused path to implement a critical security feature with no impact on other ongoing development work.

