**Bug ID:** 2025-09-22-01
**Title:** `TypeError` in `test_bond_crud.py` due to incorrect test utility usage.
**Module:** Test Suite (Backend)
**Reported By:** Gemini Code Assist via Test Log
**Date Reported:** 2025-09-22
**Classification:** Test Suite
**Severity:** High
**Description:**
The new CRUD tests for the Bond feature were failing with `TypeError: create_test_asset() got an unexpected keyword argument 'asset_type'`. This was because the tests were using the simple `create_test_asset` helper, which does not support creating specific asset types like "BOND". This blocked all unit testing for the new CRUD layer.
**Steps to Reproduce:**
1. Run the backend test suite after adding the `test_bond_crud.py` file.
2. Observe the `TypeError`.
**Expected Behavior:**
The tests should correctly create a "BOND" type asset as a prerequisite for testing the bond CRUD logic.
**Actual Behavior:**
The test setup crashed with a `TypeError`.
**Resolution:**
Refactored the tests in `test_bond_crud.py` to use the correct pattern for creating test assets (`crud.asset.create` with a full `schemas.AssetCreate` object and a randomized ticker). This approach is consistent with other working tests in the project, such as `test_bonds.py`, and ensures that tests are robust and do not rely on overly simplistic test helpers.

---