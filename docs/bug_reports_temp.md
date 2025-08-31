**Bug ID:** 2025-08-30-02
**Title:** Backend test `test_read_transactions_with_filters_and_pagination` fails with 422 Unprocessable Entity.
**Module:** Test Suite (Backend)
**Reported By:** Gemini Code Assist via Test Log
**Date Reported:** 2025-08-30
**Classification:** Test Suite
**Severity:** High
**Description:**
The test for filtering transactions by date was failing because it sent a full `datetime` ISO string (e.g., `2025-08-15T10:00:00.123456`) to an API endpoint that was expecting a simple `date` string (e.g., `2025-08-15`). This caused a `422 Unprocessable Entity` validation error from FastAPI before the endpoint's logic was ever reached.
**Steps to Reproduce:**
1. Run the backend test suite: `./run_local_tests.sh backend`
2. Observe the failure in `test_transactions.py`.
**Expected Behavior:**
The test should pass by sending a correctly formatted date string to the API endpoint.
**Actual Behavior:**
The test failed with `AssertionError: assert 422 == 200`.
**Resolution:**
The test in `app/tests/api/v1/test_transactions.py` was updated to format the date correctly. The code was changed from `(datetime.utcnow() - timedelta(days=15)).isoformat()` to `(datetime.utcnow() - timedelta(days=15)).date().isoformat()`.

---