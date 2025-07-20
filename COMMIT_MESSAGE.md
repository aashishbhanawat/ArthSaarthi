fix(backend): Stabilize entire backend and complete dashboard MVP

This commit represents a major stabilization effort for the entire backend, resolving a deep cascade of bugs that prevented the test suite from running and broke core features. The MVP for the dashboard summary endpoint was also completed and tested as part of this process.

Key Changes:
*   **Database Models:** Corrected SQLAlchemy ORM mapping errors (e.g., missing `__tablename__`, columns).
*   **Pydantic Schemas:** Ensured consistency between schemas, models, and API responses.
*   **CRUD Layer:** Implemented missing modules (`crud_dashboard`) and fixed critical logic errors (e.g., missing `user_id` on transactions, `NameError` from missing imports).
*   **API Routing:** Correctly nested transaction routes under portfolios.
*   **Test Suite:** Fixed numerous incorrect assertions, data type mismatches, and unhandled exceptions in tests.
*   **Documentation:** Performed a major cleanup and consolidation of all bug reports in `docs/bug_reports.md` to ensure an accurate history.

Bug Fixes:
*   This commit resolves all backend bugs logged on 2025-07-20.

The result is a fully stable backend where all 36 tests pass, providing a solid foundation for future development.