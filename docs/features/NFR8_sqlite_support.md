# Feature Plan: SQLite Database Support (NFR8)

## 1. Objective

To add support for SQLite as a database backend for ArthSaarthi. This is a critical non-functional requirement (NFR) that will significantly simplify deployment for native installations and single-file executables by removing the dependency on an external PostgreSQL server.

## 2. Functional Requirements

*   **NFR8: Portability:** The application must support SQLite as an alternative to PostgreSQL to facilitate simpler, single-file native deployments.

## 3. High-Level Technical Design

### 3.1. Backend Refactoring

The core of this feature involves making the backend database-agnostic.

*   **Configuration:**
    *   A new environment variable, `DATABASE_TYPE`, will be introduced. It will accept `postgres` (default) or `sqlite`.
    *   The `DATABASE_URL` will be constructed dynamically based on this type. For SQLite, it will point to a local file (e.g., `sqlite:///./arthsaarthi.db`).
*   **Database Engine:**
    *   The database session logic in `app/db/session.py` will be updated to create the correct SQLAlchemy engine (`create_engine`) based on the `DATABASE_TYPE`.
*   **Model Compatibility (Timezones):**
    *   SQLite does not have native support for timezone-aware timestamps (`TIMESTAMP(timezone=True)`).
    *   All SQLAlchemy models that use this type must be updated to use the generic `TIMESTAMP` type without timezone information.
    *   The application logic will operate under the assumption that all datetimes are stored in UTC.
*   **Database Migrations (Alembic):**
    *   The existing Alembic migration scripts are PostgreSQL-specific. They will continue to be used for PostgreSQL deployments.
    *   For SQLite deployments, migrations will not be used. Instead, the database schema will be created directly from the SQLAlchemy models on application startup using `Base.metadata.create_all()`. This is a common and practical approach for self-contained applications.

### 3.2. Deployment & Installation

*   **Docker:**
    *   A new `docker-compose.sqlite.yml` override file will be created. This file will remove the `db` (PostgreSQL) service and set `DATABASE_TYPE=sqlite` for the `backend` service. The SQLite database file will be persisted using a Docker volume.
*   **Native Installation:**
    *   The `docs/native_setup_guide.md` will be updated with a much simpler setup path for SQLite, removing the need to install and configure PostgreSQL.

## 4. Implementation Plan

1.  **Backend Core:** Update `config.py` and `session.py` to handle the `DATABASE_TYPE` variable and create the correct database engine.
2.  **Model Refactoring:** Update all SQLAlchemy models to remove `timezone=True` from `TIMESTAMP` columns.
3.  **New Migration:** Create a new Alembic migration to apply the timezone change to existing PostgreSQL databases.
4.  **Startup Logic:** Update the backend's `entrypoint.sh` or `main.py` to conditionally run `Base.metadata.create_all()` if the database type is SQLite.
5.  **Docker & Docs:** Create `docker-compose.sqlite.yml` and update all relevant documentation (`README.md`, `native_setup_guide.md`).

## 5. Testing Plan

*   The existing backend test suite already uses an in-memory SQLite database, which provides excellent coverage for the application logic against a SQLite backend.
*   The CI pipeline can be enhanced in the future to add a separate job that runs the test suite against a file-based SQLite database to validate the new configuration.

---

This plan ensures a robust and maintainable implementation that makes ArthSaarthi significantly more portable and easier for end-users to set up.
