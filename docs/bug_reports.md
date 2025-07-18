# Bug Reports

This document serves as the official bug log for the Personal Portfolio Management System. All issues discovered during testing must be documented here before work on a fix begins.

---

### Bug Report Template

Copy and paste the template below to file a new bug report.

```markdown
**Bug ID:** YYYYMMDD-NN (e.g.,  20250717-01)
**Title:**
**Reported By:**
**Date Reported:**
**Classification:** Implementation (Backend/Frontend) / Test Suite
**Severity:** Critical / High / Medium / Low
**Description:**
**Steps to Reproduce:**
1.
2.
**Expected Behavior:**
**Actual Behavior:**
**Resolution:** (To be filled in when fixed)
```

---

**Bug ID:** 20250717-01 
**Title:** Frontend tests fail due to missing @tanstack/react-query dependency. 
**Reported By:** QA Engineer 
**Date Reported:** 2025-07-17 
**Classification:** Implementation (Frontend) 
**Severity:** Critical 
**Description:** 
The test suites for UserManagementPage and UserFormModal fail to run because the @tanstack/react-query package, a core dependency for the useUsers custom hooks, is not installed in the project. 
Steps to Reproduce: 
1. Navigate to the project root.
2. Run the command docker-compose run --rm frontend npm test.
**Expected Behavior:** 
The Jest test suite should execute all tests for the User Management feature without module resolution errors. 
**Actual Behavior:**
The test run is interrupted, and two test suites fail with the error: Cannot find module '@tanstack/react-query'. 
**Resolution:** **Resolution:** Install the missing dependency by running `npm install @tanstack/react-query` in the `frontend` directory and then rebuilding the Docker image.
**Resolution:** Fixed

---

**Bug ID:**  20250717-02
**Title:** Frontend tests failing because custom hooks are not correctly mocked.
**Reported By:** QA Engineer
**Date Reported:**  2025-07-17
**Classification:** Test Suite
**Severity:** High
**Description:**
The test suites for `UserFormModal.test.tsx` and `UserManagementPage.test.tsx` fail to run with a `ReferenceError: useUsersHook is not defined`, indicating that the test files are not correctly mocking the custom hooks defined in `src/hooks/useUsers.ts`.
**Steps to Reproduce:**
1.  Navigate to the project root.
2.  Run the command `docker-compose run --rm frontend npm test`.
**Expected Behavior:**
The Jest test suite should execute all tests for the User Management feature without errors.
**Actual Behavior:**
The test run is interrupted, and two test suites fail with the error: `ReferenceError: useUsersHook is not defined`.
**Resolution:** The test setup must be corrected to use the directly imported hook functions (`useCreateUser`, `useUpdateUser`, `useUser`, and `useDeleteUser`) for mock casting, rather than the non-existent `useUsersHook` object. Additionally, a missing `mockUser` constant needs to be defined for the 'Edit Mode' tests.
**Resolution:** Fixed

---

**Bug ID:**  20250717-03
**Title:** `UserManagementPage` test suite crashes with TypeError due to incomplete hook mocking.
**Reported By:** QA Engineer
**Date Reported:**  2025-07-17
**Classification:** Test Suite
**Severity:** High
**Description:**
The test suite for `UserManagementPage.tsx` fails with a `TypeError: Cannot read properties of undefined (reading 'isPending')`. This occurs when a test simulates opening the `UserFormModal` for creating or editing a user. The `UserFormModal` internally uses the `useCreateUser` and `useUpdateUser` hooks, but these hooks are not mocked within the `UserManagementPage.test.tsx` file, causing the error.
**Steps to Reproduce:**
1. Fix the `ReferenceError` in `UserFormModal.test.tsx`.
2. Run the frontend test suite with `docker-compose run --rm frontend npm test`.
**Expected Behavior:**
The tests for opening the create/edit modals in `UserManagementPage.test.tsx` should run without crashing.
**Actual Behavior:**
The tests crash with a `TypeError`.
**Resolution:**
The test setup for `UserManagementPage.test.tsx` must be updated to provide mocks for `useCreateUser` and `useUpdateUser` in the test cases where the `UserFormModal` is rendered.
**Resolution:** Fixed

---

**Bug ID:**  20250717-04
**Title:** Tests for UserManagementPage are failing with TypeError: Cannot read properties of undefined (reading 'isPending')
**Reported By:** QA Engineer
**Date Reported:**  2025-07-17
**Classification:** Test Suite
**Severity:** High
**Description:**
The test suite `UserManagementPage.test.tsx` fails to run because the mock for the `useCreateUser` and `useUpdateUser` React Query hooks are incomplete. The test expects these mocked hooks to have an `isPending` property, which is undefined in the current mock implementation.
**Steps to Reproduce:**
1.  Navigate to the project root.
2.  Run the command `docker-compose run --rm frontend npm test`.
**Expected Behavior:**
The Jest test suite should execute all tests for the `UserManagementPage` component without errors.
**Actual Behavior:**
The test run fails because the test expects `isPending` to be a property on the mocked React Query mutation results, but it is undefined.
**Resolution:** The mock for the `useCreateUser` and `useUpdateUser` hooks in `src/__tests__/pages/Admin/UserManagementPage.test.tsx` needs to be updated to include an `isPending` property.
**Resolution:** Fixed

---

**Bug ID:**  20250717-05
**Title:** UserManagementPage test suite crashes with TypeError due to incomplete hook mocking. 
**Reported By:** QA Engineer 
**Date Reported:**  2025-07-17 
**Classification:** Test Suite 
**Severity:** High 
**Description:** 
The test suite for UserManagementPage.tsx fails with a TypeError: Cannot read properties of undefined (reading 'isPending'). This occurs when a test simulates opening the UserFormModal for creating or editing a user. The UserFormModal internally uses the useCreateUser and useUpdateUser hooks, but these hooks are not mocked completely within the UserManagementPage.test.tsx file, causing the error. 
**Steps to Reproduce:**
1. Ensure that tests for UserFormModal.tsx have been fixed.
2. Run the frontend test suite with docker-compose run --rm frontend npm test. 
**Expected Behavior:** The tests for opening the create/edit modals in UserManagementPage.test.tsx should run without crashing. 
**Actual Behavior:** The tests crash with a TypeError. 
**Resolution:** The test setup for UserManagementPage.test.tsx must be updated to provide complete mocks for useCreateUser and useUpdateUser hooks, including the isPending property.
**Resolution:** Fixed

---

**Bug ID:**  20250717-06
**Title:** `UserManagementPage.test.tsx` test suite fails to run due to syntax error.
**Reported By:** QA Engineer
**Date Reported:**  2025-07-17
**Classification:** Test Suite
**Severity:** Critical
**Description:**
The test suite for `UserManagementPage` fails during the Jest collection phase with a `TS1005: ',' expected.` syntax error. This is caused by an invalid, duplicated `mockUseCreateUser.mockReturnValue` call that was nested inside another mock definition, breaking the JavaScript syntax.
**Steps to Reproduce:**
1.  Run the frontend test suite with `docker-compose run --rm frontend npm test`.
**Expected Behavior:**
The test suite for `UserManagementPage.test.tsx` should compile and run without errors.
**Actual Behavior:**
The test run for this file is aborted with a syntax error during compilation.
**Resolution:**
The duplicated, nested mock call must be removed from `UserManagementPage.test.tsx` to fix the syntax.
**Resolution:** Fixed

---

**Bug ID:**  20250717-07
**Title:** `UserFormModal` tests fail because form labels are not associated with inputs.
**Reported By:** QA Engineer
**Date Reported:**  2025-07-17
**Classification:** Implementation (Frontend)
**Severity:** High
**Description:**
All tests for the `UserFormModal.tsx` component fail with a `TestingLibraryElementError`. The tests cannot find form controls using their labels because the `<label>` elements in the component are missing the `htmlFor` attribute to link them to their corresponding `<input>` elements, which also lack `id` attributes. This is an accessibility violation and prevents a primary method of testing forms.
**Steps to Reproduce:**
1.  Fix previous test suite errors.
2.  Run the frontend test suite with `docker-compose run --rm frontend npm test`.
**Expected Behavior:**
Tests should be able to find form inputs by their label text, and the form should be accessible.
**Actual Behavior:**
Tests fail with `TestingLibraryElementError: Found a label with the text of: ..., however no form control was found associated to that label.`
**Resolution:**
Update `UserFormModal.tsx` to add `htmlFor` and `id` attributes to all corresponding label/input pairs to make the form accessible and testable.
The duplicated, nested mock call must be removed from `UserManagementPage.test.tsx` to fix the syntax.
**Resolution:** Fixed

---

**Bug ID:** 20250717-08
**Title:** `UserFormModal` crashes with "Objects are not valid as a React child" error.
**Reported By:** QA Engineer
**Date Reported:** 2025-07-17
**Classification:** Implementation (Frontend)
**Severity:** High
**Description:**
When an API call fails during form submission, the `UserFormModal` component attempts to render the raw error object received from the API directly into the JSX. React does not permit rendering of plain JavaScript objects, which causes the component to crash and display a cryptic error message to the user.
**Steps to Reproduce:**
1.  Run the frontend test suite.
2.  Observe the failure in the test case "displays error messages from API on failed user creation" for `UserFormModal.test.tsx`.
**Expected Behavior:**
The component should parse the incoming error object, extract the user-friendly message string (e.g., "Email already exists"), and display only that string in the UI.
**Actual Behavior:**
The component crashes with the error: `Error: Objects are not valid as a React child (found: object with keys {loc, msg})`.
The error handling logic in the handleSubmit function of UserFormModal.tsx must be corrected to ensure that test don't hit errors that can impact the UX of the app.
**Resolution:**
 The duplicated, nested mock call must be removed from `UserManagementPage.test.tsx` to fix the syntax.
**Resolution:** Fixed

---

**Bug ID:** 20250717-09
**Title:** `UserFormModal` tests fail due to duplicate component rendering in 'Edit Mode' suite.
**Reported By:** QA Engineer
**Date Reported:** 2025-07-17
**Classification:** Test Suite
**Severity:** High
**Description:**
The test suite for `UserFormModal.tsx` fails when testing error states in 'Edit Mode' because the component is rendered twice. The `beforeEach` hook renders the modal, and the specific test case also renders it again. This results in `TestingLibraryElementError` because queries like `getByRole` find multiple matching elements.
**Steps to Reproduce:**
1.  Fix previous test suite errors.
2.  Run the frontend test suite with `docker-compose run --rm frontend npm test`.
**Expected Behavior:**
Each test should run against a single instance of the rendered component, allowing queries to resolve to a unique element.
**Actual Behavior:**
Tests fail with `TestingLibraryElementError: Found multiple elements with the role "button" and name "Save Changes"`.
**Resolution:**
The test suite structure must be refactored to ensure the component is rendered only once per test. The rendering call in the `beforeEach` block should be removed, and each test case should be responsible for its own rendering.
**Resolution:** Fixed

---

**Bug ID:** 20250717-10
**Title:** `UserManagementPage` delete confirmation test fails with an ambiguous query.
**Reported By:** QA Engineer
**Date Reported:** 2025-07-17
**Classification:** Test Suite
**Severity:** Medium
**Description:**
The test case "opens delete confirmation modal when 'Delete' is clicked" fails because it uses a `screen.getByText` query for a user's name. When the modal opens, this name is present in both the background table and the modal itself, leading to a `TestingLibraryElementError` for finding multiple elements.
**Steps to Reproduce:**
1.  Fix previous test suite errors.
2.  Run the frontend test suite with `docker-compose run --rm frontend npm test`.
**Expected Behavior:**
The test should uniquely identify elements within the modal to verify its content, even if the same text exists elsewhere on the page.
**Actual Behavior:**
The test fails with `TestingLibraryElementError: Found multiple elements with the text: Test User`.
**Resolution:**
The test query must be scoped to search only within the modal dialog. This can be achieved by first finding the modal element (e.g., by its role of `dialog`) and then using the `within` utility from React Testing Library to perform subsequent queries inside it.
**Resolution:** Fixed

---

**Bug ID:** 20250717-11
**Title:**  `UserFormModal` component crashes when displaying API error.
**Reported By:** QA Engineer
**Date Reported:** 2025-07-17
**Classification:** Implementation (Frontend)
**Severity:** High
**Description:**
The tests confirm that when submitting the user management form a React error is thrown. `Objects are not valid as a React child (found: object with keys {loc, msg}).`
This error occurs when the UserFormModal attempts to render the raw API error as output in the jsx.
**Steps to Reproduce:**
1.  Run the frontend tests.
2. Trigger a failed submission on the UserFormModal
**Expected Behavior:**
UserFormModal must display error in a user-friendly format.
**Actual Behavior:**
Tests crash with React error message Objects are not valid as a React child (found: object with keys {loc, msg}).
The error handling logic in the handleSubmit function of UserFormModal.tsx must be corrected to ensure that test don't hit errors that can impact the UX of the app.
The test query must be scoped to search only within the modal dialog. This can be achieved by first finding the modal element (e.g., by its role of `dialog`) and then using the `within` utility from React Testing Library to perform subsequent queries inside it.
The test suite structure must be refactored to ensure the component is rendered only once per test. The rendering call in the `beforeEach` block should be removed, and each test case should be responsible for its own rendering.
The error handling logic in the `handleSubmit` function of `UserFormModal.tsx` must be corrected to ensure only a string is set in the `error` state.
Update `UserFormModal.tsx` to add `htmlFor` and `id` attributes to all corresponding label/input pairs to make the form accessible and testable.
The duplicated, nested mock call must be removed from `UserManagementPage.test.tsx` to fix the syntax.

**Resolution:**
The test query must be scoped to search only within the modal dialog. This can be achieved by first finding the modal element (e.g., by its role of `dialog`) and then using the `within` utility from React Testing Library to perform subsequent queries inside it.
The error handling logic in the handleSubmit function of UserFormModal.tsx must be corrected to ensure that test don't hit errors that can impact the UX of the app.
**Resolution:** Fixed

---

**Bug ID:** 20250717-12
**Title:** Syntax error in `UserFormModal.tsx` breaks multiple test suites.
**Reported By:** QA Engineer
**Date Reported:** 2025-07-17
**Classification:** Implementation (Frontend)
**Severity:** Critical
**Description:**
The test suites for `UserManagementPage` and `UserFormModal` both fail during the Jest collection phase with a `TS1005: '}' expected.` syntax error. The error originates in the `UserFormModal.tsx` component file, which has a missing closing curly brace. This invalid syntax prevents any component or test that imports it from compiling.
**Steps to Reproduce:**
1.  Run the frontend test suite with `docker-compose run --rm frontend npm test`.
**Expected Behavior:**
The test suites should compile and run without errors.
**Actual Behavior:**
The test run is aborted with a syntax error during compilation, originating from `UserFormModal.tsx`.
**Resolution:**
The missing `}` must be added to the `handleSubmit` function in `UserFormModal.tsx` to fix the syntax.
**Resolution:** Fixed

---

**Bug ID:** 20250718-01
**Title:** Admin-only "User Management" link is not displayed on the dashboard.
**Reported By:** Developer via Manual E2E Test
**Date Reported:** 2025-07-18
**Classification:** Implementation (Frontend)
**Severity:** High
**Description:**
After an administrator successfully logs in, the dashboard page only displays a generic welcome message. It does not provide a navigation link to the User Management page, making the feature inaccessible through the UI. The `DashboardPage.tsx` component fails to check the logged-in user's `is_admin` status to conditionally render the required navigation.
**Steps to Reproduce:**
1. Log in to the application as a user with administrator privileges.
2. Observe the dashboard page.
**Expected Behavior:**
The dashboard should display a "User Management" link that navigates to `/admin/users`.
**Actual Behavior:**
No "User Management" link is visible.
**Resolution:** The logic was refactored to place the conditional link in the `NavBar` component and fetch user data centrally in the `AuthContext`. **Resolution:** Fixed

---

**Bug ID:** 20250718-02
**Title:** Navigating to `/admin/users` results in a "No routes matched location" error.
**Reported By:** Developer via Manual E2E Test
**Date Reported:** 2025-07-18
**Classification:** Implementation (Frontend)
**Severity:** Critical
**Description:**
After programmatically adding the link to the User Management page, clicking it results in a blank page and a `No routes matched location "/admin/users"` error in the console. The main application router in `App.tsx` has not been configured to handle this path.
**Steps to Reproduce:**
1. Apply the fix for Bug ID 20250718-01.
2. Log in as an admin.
3. Click the "User Management" link.
**Expected Behavior:**
The application should navigate to the User Management page and render its content.
**Actual Behavior:**
The application renders a blank page, and the routing fails.
**Resolution:** Create a new `AdminRoute.tsx` protected route component. Update the main router in `App.tsx` to define a nested route for `/admin/users` that is protected by both the standard `ProtectedRoute` and the new `AdminRoute`. **Resolution:** Fixed

---

**Bug ID:** 20250718-03
**Title:** User Management page crashes with "No QueryClient set" error.
**Reported By:** Developer via Manual E2E Test
**Date Reported:** 2025-07-18
**Classification:** Implementation (Frontend)
**Severity:** Critical
**Description:**
After fixing the routing, the `UserManagementPage` immediately crashes upon loading. The browser console shows the error `Uncaught Error: No QueryClient set, use QueryClientProvider to set one`. The page and its children use React Query hooks, but the root `App.tsx` component is not wrapped in the required `<QueryClientProvider>`.
**Steps to Reproduce:**
1. Apply fixes for the previous two bugs.
2. Log in as an admin and navigate to the User Management page.
**Expected Behavior:**
The User Management page should load correctly and begin fetching user data.
**Actual Behavior:**
The page crashes, and the application becomes unresponsive.
**Resolution:** In `App.tsx`, instantiate a new `QueryClient` and wrap the entire `<Router>` component with a `<QueryClientProvider client={queryClient}>`. **Resolution:** Fixed

---

**Bug ID:** 20250718-04
**Title:** SQLAlchemy ORM mapping fails due to missing relationship back-references in User model.
**Reported By:** QA Engineer
**Date Reported:** 2025-07-18
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
After adding `Portfolio`, `Asset`, and `Transaction` models with relationships pointing to the `User` model, the `User` model itself was not updated with the corresponding `back_populates` relationships. This causes SQLAlchemy's mapper configuration to fail whenever any part of the application attempts to query a user, leading to a cascade of `FAILED` tests across the entire test suite.
**Steps to Reproduce:**
1. Implement the new models for portfolio management.
2. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
The SQLAlchemy ORM should initialize correctly, and tests should run without mapping errors.
**Actual Behavior:**
Tests fail with `sqlalchemy.exc.InvalidRequestError: Mapper 'Mapper[User(users)]' has no property 'portfolios'`.
**Resolution:** Fixed

---

**Bug ID:** 20250718-05
**Title:** Portfolio & Transaction test suite fails due to use of non-existent 'normal_user_token_headers' fixture.
**Reported By:** QA Engineer
**Date Reported:** 2025-07-18
**Classification:** Test Suite
**Severity:** Critical
**Description:**
The entire test suite for the new portfolio and transaction endpoints (`test_portfolios_transactions.py`) fails during test collection because it attempts to use a pytest fixture named `normal_user_token_headers`. This fixture is not defined in the project's `conftest.py`, causing every test in the file to `ERROR` out.
**Steps to Reproduce:**
1. Implement the new portfolio/transaction endpoints and their corresponding tests.
2. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
The tests in `test_portfolios_transactions.py` should be collected and should run.
**Actual Behavior:**
All tests in the file fail with the error: `fixture 'normal_user_token_headers' not found`.
**Resolution:** Fixed

---

**Bug ID:** 20250718-06
**Title:** Portfolio & Transaction test suite fails due to incorrect usage of `get_auth_headers` fixture.
**Reported By:** QA Engineer
**Date Reported:** 2025-07-18
**Classification:** Test Suite
**Severity:** Critical
**Description:**
All tests in `test_portfolios_transactions.py` fail with a `TypeError` because the `get_auth_headers` fixture is called with only the user's email. The fixture requires both the email and the password to function correctly. The `create_random_user` utility returns the plain-text password, but it is not being captured and passed to the fixture.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
The tests in `test_portfolios_transactions.py` should run successfully.
**Actual Behavior:**
All tests in the file fail with `TypeError: get_auth_headers.<locals>._get_auth_headers() missing 1 required positional argument: 'password'`.
**Resolution:** Fixed

---

**Bug ID:** 20250718-07
**Title:** Tests fail due to missing `API_V1_STR` in application settings.
**Reported By:** QA Engineer
**Date Reported:** 2025-07-18
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
Multiple tests in `test_portfolios_transactions.py` fail with `AttributeError: 'Settings' object has no attribute 'API_V1_STR'`. The tests rely on this configuration variable to construct the API endpoint URLs, but it is not defined in the `Settings` class in `app/core/config.py`.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
Tests should be able to access the API version string from the global settings.
**Actual Behavior:**
Tests crash with an `AttributeError`.
**Resolution:** Fixed

---

**Bug ID:** 20250718-08
**Title:** Test helpers fail due to unexposed Pydantic schemas.
**Reported By:** QA Engineer
**Date Reported:** 2025-07-18
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
Test utility functions like `create_test_portfolio` fail with `AttributeError: module 'app.schemas' has no attribute 'PortfolioCreate'`. The new Pydantic schemas for Portfolio, Asset, and Transaction were created in their own files but were not imported into the main `app/schemas/__init__.py` file, making them inaccessible to the rest of the application.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
All Pydantic schemas should be importable from the `app.schemas` package.
**Actual Behavior:**
Tests crash with an `AttributeError` when trying to access the new schemas.
**Resolution:** Fixed

---

**Bug ID:** 20250718-09
**Title:** Test suite collection fails with ImportError for non-existent 'UserInDB' schema.
**Reported By:** QA Engineer
**Date Reported:** 2025-07-18
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The entire test suite fails to run because of an `ImportError` during the test collection phase. The `app/schemas/__init__.py` file attempts to import a Pydantic schema named `UserInDB` from `app/schemas/user.py`, but this schema is not defined in that file. This breaks the application's startup and prevents any tests from running.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
The test suite should collect and run successfully.
**Actual Behavior:**
Test collection is interrupted with `ImportError: cannot import name 'UserInDB' from 'app.schemas.user'`.
**Resolution:** Fixed

---

**Bug ID:** 20250718-10
**Title:** Test suite collection fails with ModuleNotFoundError for 'app.schemas.msg'.
**Reported By:** QA Engineer
**Date Reported:** 2025-07-18
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The test suite fails to run because of a `ModuleNotFoundError`. The `app/schemas/__init__.py` file attempts to import the `Msg` schema from `app.schemas.msg`, but the `msg.py` file does not exist in the `app/schemas/` directory. This breaks the application's startup and prevents any tests from running.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
The test suite should collect and run successfully.
**Actual Behavior:**
Test collection is interrupted with `ModuleNotFoundError: No module named 'app.schemas.msg'`.
**Resolution:** Fixed 

---

**Bug ID:** 20250718-11
**Title:** New portfolio and asset endpoints are not registered, causing 404 errors.
**Reported By:** QA Engineer
**Date Reported:** 2025-07-18
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
Tests for new endpoints like `POST /api/v1/portfolios/` and `GET /api/v1/assets/lookup/{ticker}` are failing with a `404 Not Found` status code. The FastAPI routers for the portfolio, asset, and transaction features were created but were never included in the main API router in `app/api/v1/api.py`, so the application is unaware of these routes.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
Requests to the new endpoints should be routed correctly.
**Actual Behavior:**
Requests to any new portfolio, asset, or transaction endpoint result in a 404 error.
**Resolution:** Fixed by including the new routers in `app/api/v1/api.py`.

---

**Bug ID:** 20250718-12
**Title:** Test helpers fail due to unexposed CRUD modules.
**Reported By:** QA Engineer
**Date Reported:** 2025-07-18
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
Multiple tests in `test_portfolios_transactions.py` fail with `AttributeError: module 'app.crud' has no attribute 'portfolio'`. The new CRUD modules (`crud_portfolio.py`, `crud_asset.py`, `crud_transaction.py`) were created, but their singleton instances were not imported into the main `app/crud/__init__.py` file. This makes them inaccessible to the rest of the application, particularly the test utility functions that rely on them.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
CRUD modules should be importable from the `app.crud` package.
**Actual Behavior:**
Tests crash with an `AttributeError` when trying to access any of the new CRUD modules.
**Resolution:** Fixed by importing the new CRUD singletons into `app/crud/__init__.py`.

---

**Bug ID:** 20250718-13
**Title:** Test suite collection fails with ModuleNotFoundError for 'app.crud.base'.
**Reported By:** QA Engineer
**Date Reported:** 2025-07-18
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The test suite fails to run because of a `ModuleNotFoundError`. The `app/crud/__init__.py` file attempts to import `CRUDBase` from `app.crud.base`, but the `base.py` file containing this essential class does not exist in the `app/crud/` directory. This breaks the application's startup and prevents any tests from running.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
The test suite should collect and run successfully.
**Actual Behavior:**
Test collection is interrupted with `ModuleNotFoundError: No module named 'app.crud.base'`.
**Resolution:** Fixed by creating the `app/crud/base.py` file.

---

**Bug ID:** 20250718-14
**Title:** Test suite collection fails with ImportError for 'user' from 'crud_user'.
**Reported By:** QA Engineer
**Date Reported:** 2025-07-18
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The test suite fails to run because of an `ImportError`. The `app/crud/__init__.py` file attempts to import the `user` singleton from `app.crud.crud_user`, but this object is never instantiated within the `crud_user.py` file. The file is a collection of disorganized functions instead of following the established class-based `CRUDBase` pattern.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
The test suite should collect and run successfully.
**Actual Behavior:**
Test collection is interrupted with `ImportError: cannot import name 'user' from 'app.crud.crud_user'`.
**Resolution:** Fixed by reverting `crud_user.py` to a functional approach and commenting out the problematic import in `crud/__init__.py`.

---

**Bug ID:** 20250718-15
**Title:** Asset lookup tests fail due to missing financial API configuration.
**Reported By:** QA Engineer
**Date Reported:** 2025-07-18
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The tests for the asset lookup endpoint (`/api/v1/assets/lookup/{ticker_symbol}`) are failing with `AttributeError: 'Settings' object has no attribute 'FINANCIAL_API_KEY'`. The `FinancialDataService` requires an API key and URL, but these configuration variables are not defined in the `Settings` class in `app/core/config.py`.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
The asset lookup tests should run successfully.
**Actual Behavior:**
The tests fail with an `AttributeError` when trying to initialize the `FinancialDataService`.
**Resolution:** Fixed by adding the required `FINANCIAL_API_KEY` and `FINANCIAL_API_URL` to the `Settings` class.

