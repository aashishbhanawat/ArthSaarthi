## 2026-04-29 - Prevent information leakage in log retrieval
**Vulnerability:** The `get_logs` system endpoint leaked internal system information by returning the exact exception string (`str(e)`) to the client if log file reading failed.
**Learning:** In Python, catching a generic `Exception` and stringifying it can inadvertently expose sensitive file paths or environment constraints to unauthorized clients.
**Prevention:** API responses should always return safe, generic error messages (e.g., 'Error reading log file. Please check server logs.'), while the actual error details must be securely logged internally using `logger.error(..., exc_info=True)`.
