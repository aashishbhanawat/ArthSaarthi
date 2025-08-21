## Bug Reports

### Bug 1: TypeError in test_goals.py

- **ID:** BUG-001
- **Summary:** `TypeError: create_test_portfolio() missing 1 required keyword-only argument: 'name'`
- **Description:** The `create_test_portfolio` test utility function requires a `name` argument, but it was being called without one in `test_create_goal_link_portfolio` and `test_delete_goal_link` in `app/tests/api/v1/test_goals.py`.
- **Status:** Fixed.

---

### Bug 2: 422 Unprocessable Entity when creating a goal link

- **ID:** BUG-002
- **Summary:** The API endpoint `/api/v1/goals/{goal_id}/links` returns a 422 Unprocessable Entity error when trying to create a goal link.
- **Description:** The `GoalLinkCreate` Pydantic schema was incorrectly defined, and the `create_goal_link` endpoint was not correctly handling the `goal_id` from the path. This caused a validation error.
- **Status:** Fixed.
