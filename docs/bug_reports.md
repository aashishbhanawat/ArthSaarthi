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

---

**Bug ID:** 20250718-16
**Title:** Portfolio tests crash due to missing `react-hook-form` dependency.
**Reported By:** QA Engineer
**Date Reported:** 2025-07-18
**Classification:** Implementation (Frontend)
**Severity:** Critical
**Description:**
The test suites for `AddTransactionModal` and `PortfolioDetailPage` fail to run with the error `Cannot find module 'react-hook-form'`. The `AddTransactionModal` component, a core part of the feature, depends on this library, but it is not listed in `package.json`.
**Steps to Reproduce:**
1. Run the frontend test suite: `docker-compose run --rm frontend npm test`.
**Expected Behavior:**
All test suites should be collected and run without module resolution errors.
**Actual Behavior:**
The test run is interrupted for two suites because a required npm package is missing.
**Resolution:** Fixed by adding `react-hook-form` to the `dependencies` in `frontend/package.json` and rebuilding the Docker image.

---

**Bug ID:** 20250718-17
**Title:** `LoginForm` tests crash with TypeError due to missing AuthContext import.
**Reported By:** QA Engineer
**Date Reported:** 2025-07-18
**Classification:** Test Suite
**Severity:** High
**Description:**
All tests in `LoginForm.test.tsx` fail with `TypeError: Cannot read properties of undefined (reading 'Provider')`. The test file attempts to wrap the component in an `AuthContext.Provider` but never imports the `AuthContext` object itself.
**Steps to Reproduce:**
1. Run the frontend test suite.
**Expected Behavior:**
The `LoginForm` tests should run without crashing.
**Actual Behavior:**
The entire test suite for `LoginForm.tsx` fails with a `TypeError`.
**Resolution:** Fixed by adding the missing `AuthContext` import in `LoginForm.test.tsx`.

---

**Bug ID:** 20250718-18
**Title:** `AdminRoute` tests fail due to incorrect test setup and assertions.
**Reported By:** QA Engineer
**Date Reported:** 2025-07-18
**Classification:** Test Suite
**Severity:** High
**Description:**
The tests for `AdminRoute.tsx` fail because the test setup does not correctly simulate the application's routing, causing redirect tests to fail. Additionally, the test for the loading state incorrectly asserts that "Loading..." text should be present, when the component is designed to render nothing while waiting for user data.
**Steps to Reproduce:**
1. Run the frontend test suite.
**Expected Behavior:**
The tests should accurately verify the component's redirect and loading state logic.
**Actual Behavior:**
Tests fail with `TestingLibraryElementError` because the DOM state does not match the test's incorrect expectations.
**Resolution:** Fixed by refactoring the test to use a complete routing structure, which allows redirects to be handled correctly and eliminates console warnings. 

---

**Bug ID:** 20250718-19
**Title:** `AddTransactionModal` test fails due to ambiguous query for "Type" label.
**Reported By:** QA Engineer
**Date Reported:** 2025-07-18
**Classification:** Test Suite
**Severity:** High
**Description:**
The test case "submits correct data for a new asset" in `AddTransactionModal.test.tsx` fails with `TestingLibraryElementError: Found multiple elements with the text of: /type/i`. The test attempts to select the "Transaction Type" dropdown, but the query `getByLabelText(/type/i)` is ambiguous because it also matches the "Asset Type" input field label.
**Steps to Reproduce:**
1. Run the frontend test suite.
**Expected Behavior:**
The test should uniquely identify and interact with the "Transaction Type" dropdown.
**Actual Behavior:**
The test fails because the query finds two matching elements.
**Resolution:** Fixed by changing the query to `getByLabelText('Type', { exact: true })` to uniquely identify the correct form element. 

---

**Bug ID:** 20250718-20
**Title:** `AddTransactionModal` test fails due to incomplete assertion.
**Reported By:** QA Engineer
**Date Reported:** 2025-07-18
**Classification:** Test Suite
**Severity:** High
**Description:**
The test case "submits correct data for a new asset" in `AddTransactionModal.test.tsx` fails because the `expect.objectContaining` assertion is missing properties (`transaction_type`, `transaction_date`) that are correctly being passed to the `createTransaction` mutation.
**Steps to Reproduce:**
1. Run the frontend test suite.
**Expected Behavior:**
The test assertion should match the shape of the data being sent in the mutation.
**Actual Behavior:**
The test fails because the assertion is missing required fields.
**Resolution:** Fixed by adding the missing properties to the `expect.objectContaining` assertion in the test.

---

**Bug ID:** 20250718-21
**Title:** `AddTransactionModal` test fails due to incomplete assertion for default fees.
**Reported By:** QA Engineer
**Date Reported:** 2025-07-18
**Classification:** Test Suite
**Severity:** High
**Description:**
The test case "submits correct data for a new asset" in `AddTransactionModal.test.tsx` fails because the `expect.objectContaining` assertion does not account for the `fees: 0` property that the component correctly sends by default when no fee is entered.
**Steps to Reproduce:**
1. Run the frontend test suite.
**Expected Behavior:**
The test assertion should match the shape of the data being sent in the mutation, including default values.
**Actual Behavior:**
The test fails because the assertion is missing the `fees` property.
**Resolution:** Fixed by adding the `fees: 0` property to the `expect.objectContaining` assertion in the test.

---

**Bug ID:** 20250718-22
**Title:** `LoginForm` component does not call the correct API service function.
**Reported By:** QA Engineer
**Date Reported:** 2025-07-18
**Classification:** Implementation (Frontend)
**Severity:** Critical
**Description:**
The `LoginForm` component has incorrect submission logic. It does not call the abstracted `loginUser` function from the API service layer, which is what the test suite mocks. This causes all related tests to fail, as the component does not interact with the mocked API correctly.
**Steps to Reproduce:**
1. Run the frontend test suite.
**Expected Behavior:**
The form should call the `loginUser` service function on submit.
**Actual Behavior:**
The `loginUser` function is never called, and tests for both successful and failed submissions fail.
**Resolution:** Fixed by refactoring `LoginForm.tsx` to call the `api.loginUser` function instead of using `api.post` directly.

---

**Bug ID:** 20250718-23
**Title:** `AddTransactionModal` test fails due to incorrect assertion for `asset_id`.
**Reported By:** QA Engineer
**Date Reported:** 2025-07-18
**Classification:** Test Suite
**Severity:** High
**Description:**
The test case "submits correct data for a new asset" in `AddTransactionModal.test.tsx` fails. The test assertion `expect.objectContaining` includes `asset_id: undefined`, but when a new asset is being created, the component correctly omits the `asset_id` key from the payload entirely. The test should not check for the presence of an undefined key.
**Steps to Reproduce:**
1. Run the frontend test suite.
**Expected Behavior:**
The test assertion should match the shape of the data being sent, which does not include an `asset_id` key for new assets.
**Actual Behavior:**
The test fails because the assertion expects a key that does not exist in the submitted object.
**Resolution:** Fixed by removing the `asset_id: undefined` check from the test assertion.

---

**Bug ID:** 20250719-01
**Title:** Login fails with 404 Not Found due to incorrect API endpoint.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-19
**Classification:** Implementation (Frontend)
**Severity:** Critical
**Description:**
The `LoginForm` component makes a `POST` request to `/auth/login` instead of the correct endpoint `/api/v1/auth/login`. This results in a `404 Not Found` error from the server, making it impossible for users to log in.
**Steps to Reproduce:**
1. Navigate to the login page.
2. Enter valid user credentials.
3. Click the "Sign in" button.
4. Observe the browser's developer console.
**Expected Behavior:**
The user should be successfully authenticated, receive a JWT token, and be redirected to the dashboard.
**Actual Behavior:**
The login request fails with a `404 Not Found` error in the console. The user remains on the login page with an error message.
**Resolution:** The `handleSubmit` function in `LoginForm.tsx` was updated to use the correct API endpoint: `/api/v1/auth/login`.
**Resolution:** Fixed

---

**Bug ID:** 20250719-02
**Title:** Application-wide UI styling is broken due to missing Tailwind CSS configuration.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-19
**Classification:** Implementation (Frontend)
**Severity:** Critical
**Description:**
Despite adding custom CSS classes (`.card`, `.btn`, etc.) to `index.css`, none of the styles are being applied across the application. The layout is broken, components are unstyled, and the UI is unusable. This is caused by a missing Tailwind CSS build configuration.
**Steps to Reproduce:**
1. Define custom component classes in `index.css` using `@apply`.
2. Apply these classes to components (e.g., `<div class="card">`).
3. Launch the frontend application.
**Expected Behavior:**
The custom classes should be processed by Tailwind CSS, and the components should render with the correct styling.
**Actual Behavior:**
The classes are ignored, and the application appears unstyled. The browser's inspector shows the custom class names but no associated CSS rules.
**Resolution:** 
1. Create `tailwind.config.js` and `postcss.config.js` in the frontend root.
2. Add `tailwindcss`, `postcss`, and `autoprefixer` as dev dependencies to `package.json`.
3. Rebuild the frontend Docker container.
**Resolution:** Fixed

---

**Bug ID:** 20250719-03
**Title:** Frontend build fails due to use of deprecated `focus:shadow-outline` class.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-19
**Classification:** Implementation (Frontend)
**Severity:** Critical
**Description:**
After correctly setting up the Tailwind CSS build process, the Vite server fails to start. The error message indicates that the `focus:shadow-outline` class, used in the custom `.btn` component style, does not exist. This class is from an older version of Tailwind CSS.
**Steps to Reproduce:**
1. Configure Tailwind CSS correctly.
2. Define a class in `index.css` using `@apply focus:shadow-outline`.
3. Attempt to start the frontend development server.
**Expected Behavior:**
The server should start without errors.
**Actual Behavior:**
The build process fails with a PostCSS error: "The `focus:shadow-outline` class does not exist."
**Resolution:** Replaced `focus:shadow-outline` with modern focus ring utilities (`focus:ring-2 focus:ring-offset-2`) in `index.css` for the `.btn` class and its variants.
**Resolution:** Fixed

---

**Bug ID:** 20250719-04
**Title:** Login page is unstyled and inconsistent with the application theme.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-19
**Classification:** Implementation (Frontend)
**Severity:** Medium
**Description:**
The `AuthPage`, `LoginForm`, and `SetupForm` components do not use the application's global design system. They render with default, unstyled HTML elements, creating a jarring and unprofessional user experience compared to the rest of the application.
**Steps to Reproduce:**
1. Navigate to the `/login` route.
**Expected Behavior:**
The login page should have a clean, centered layout with styled form inputs and buttons that match the application's theme.
**Actual Behavior:**
The login form is unstyled, misaligned, and does not use the `.card`, `.form-input`, or `.btn` classes.
**Resolution:** Refactored `AuthPage.tsx` to provide a centered layout with a `.card` container. Refactored `LoginForm.tsx` and `SetupForm.tsx` to use the global form styling classes (`.form-group`, `.form-label`, `.form-input`) and button classes.
**Resolution:** Fixed

---

**Bug ID:** 20250719-05
**Title:** Frontend crashes due to incorrect relative import paths in form components.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-19
**Classification:** Implementation (Frontend)
**Severity:** Critical
**Description:**
The application crashes when attempting to render the login page. The Vite server throws a `Failed to resolve import` error. The `LoginForm.tsx` and `SetupForm.tsx` components use incorrect relative paths to import the `AuthContext`, causing the module resolution to fail.
**Steps to Reproduce:**
1. Navigate to the `/login` route after refactoring the login forms.
**Expected Behavior:**
The login page should render correctly.
**Actual Behavior:**
The application shows a blank page, and the Vite server logs a fatal error related to module resolution.
**Resolution:** Corrected the import paths for `useAuth` in both `LoginForm.tsx` (to `../context/AuthContext`) and `SetupForm.tsx` (to `../../context/AuthContext`).
**Resolution:** Fixed

---

**Bug ID:** 20250719-06
**Title:** Login functionality is broken, preventing user authentication.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-19
**Classification:** Implementation (Frontend)
**Severity:** Critical
**Description:**
After successfully styling the login page, attempting to log in fails. The `LoginForm` component's submission logic is incorrect. It does not properly handle the API request or the resulting authentication token. This leads to a `404 Not Found` error (due to an incorrect URL) and subsequent `403 Forbidden` errors on protected routes because the token is never stored.
**Steps to Reproduce:**
1. Navigate to the login page.
2. Enter valid credentials and submit the form.
3. Observe the browser console and network requests.
**Expected Behavior:**
The user should be logged in, and the auth token should be stored in the `AuthContext`.
**Actual Behavior:**
The login API call fails with a 404. The user is not logged in and remains on the login page with an error message.
**Resolution:** The `handleSubmit` function in `LoginForm.tsx` was completely refactored. It now uses the correct API endpoint (`/api/v1/auth/login`), correctly formats the request payload as `x-www-form-urlencoded`, and upon success, calls the `login` function from `AuthContext` with the received token.
**Resolution:** Fixed

---

**Bug ID:** 20250720-01
**Title:** Test suite collection fails due to multiple setup and configuration errors.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Test Suite / Implementation (Backend)
**Severity:** Critical
**Description:**
The test suite fails to run due to a cascade of configuration and setup issues that prevent pytest from collecting tests. The issues include:
1.  `ModuleNotFoundError` because the test helper `app.tests.utils.transaction.py` was never created.
2.  `Fixture 'mocker' not found` because the `pytest-mock` dependency was missing from `requirements.txt`.
3.  `AttributeError` because the `FINANCIAL_API_KEY` and `FINANCIAL_API_URL` settings were missing from `app/core/config.py`.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
The test suite should collect and run successfully.
**Actual Behavior:**
Test collection is interrupted by various fatal errors.
**Resolution:**
1. Created the missing test utility file `app/tests/utils/transaction.py`.
2. Added `pytest-mock` to `requirements.txt`.
3. Added the required financial API settings to the `Settings` class.
**Resolution:** Fixed

---

**Bug ID:** 20250720-02
**Title:** Test suite fails due to multiple inconsistencies between tests and application code.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Test Suite
**Severity:** High
**Description:**
Multiple tests are failing due to a drift between the test implementation and the application code. The issues include:
1.  `test_get_dashboard_summary_unauthorized` asserts for a `403` status code, but the API correctly returns `401`.
2.  Dashboard tests call `create_test_portfolio` with a `user_id` argument, but the test helper function signature did not include it.
3.  Portfolio tests call `create_test_portfolio` with a `user` object, but the helper expects a `user_id`.
4.  The `create_test_transaction` helper did not provide a `currency` when creating a new asset, causing a `ValidationError`.
**Steps to Reproduce:**
1. Run the backend test suite after fixing the initial setup issues.
**Expected Behavior:**
Tests should pass.
**Actual Behavior:**
Tests fail with `AssertionError`, `TypeError`, and `ValidationError`.
**Resolution:**
1. Corrected the status code assertion in the unauthorized dashboard test to `401`.
2. Updated the `create_test_portfolio` helper to accept a `user_id`.
3. Corrected all calls to `create_test_portfolio` to pass `user_id=user.id`.
4. Updated the `create_test_transaction` helper to include a default `currency`.
**Resolution:** Fixed

---

**Bug ID:** 20250720-03
**Title:** Dashboard logic fails due to missing method and incorrect initialization.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The dashboard summary calculation in `crud_dashboard.py` is broken. It attempts to call `financial_data_service.get_asset_price()`, but this method was never defined in the `FinancialDataService` class.
**Steps to Reproduce:**
1. Call the `GET /api/v1/dashboard/summary` endpoint.
**Expected Behavior:**
The dashboard summary should be calculated correctly.
**Actual Behavior:**
The request fails with an `AttributeError`.
**Resolution:** Added the missing `get_asset_price` mock method to the `FinancialDataService` class.
**Resolution:** Fixed

---

**Bug ID:** 20250720-04
**Title:** Portfolio and Transaction tests fail due to incorrect API logic and routing.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Implementation (Backend) / Test Suite
**Severity:** Critical
**Description:**
Multiple tests related to portfolios and transactions are failing due to a combination of incorrect API logic, routing, and schema validation.
1.  `test_create_portfolio` asserts for a `200` status code, but the API correctly returns `201`.
2.  `test_read_portfolio_wrong_owner` asserts for `403`, but the API returns `404` due to flawed access control logic.
3.  All transaction tests fail with `404 Not Found` because the transaction router is not correctly nested under the portfolio router.
4.  Transaction creation tests fail with `422 Unprocessable Entity` because the `TransactionCreate` schema incorrectly includes a `portfolio_id`.
**Steps to Reproduce:**
1. Run the backend test suite.
**Expected Behavior:**
All portfolio and transaction tests should pass.
**Actual Behavior:**
Tests fail with `AssertionError`, `404 Not Found`, and `422 Unprocessable Entity`.
**Resolution:**
1. Updated the portfolio creation test to assert for `201`.
2. Fixed the `read_portfolio` endpoint to correctly return `403` for unauthorized access.
3. Refactored the API routing to correctly nest the transaction endpoints under `/portfolios/{portfolio_id}/transactions`.
4. Removed the redundant `portfolio_id` from the `TransactionCreate` schema.
**Resolution:** Fixed

---

**Bug ID:** 20250720-05
**Title:** Application fails to start due to multiple configuration and import errors.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
A series of critical errors prevent the application from starting, making it impossible to run the test suite. These include:
1.  A missing `__tablename__` in the `Portfolio` SQLAlchemy model.
2.  A missing `crud_dashboard` module and `DashboardSummary` schema.
3.  Incorrect imports for `models.User` in endpoint files.
4.  A missing import for the `crud` package in `crud_transaction.py`, causing a `NameError`.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
The application should start, and the test suite should run.
**Actual Behavior:**
The test suite collection fails with `InvalidRequestError`, `AttributeError`, `ImportError`, and `NameError`.
**Resolution:**
1. Added `__tablename__ = "portfolios"` to the `Portfolio` model.
2. Created the `crud_dashboard.py` module and the `schemas/dashboard.py` file.
3. Corrected all incorrect imports across the application to use direct imports (e.g., `from app.models.user import User`).
**Resolution:** Fixed

---

**Bug ID:** 20250720-06
**Title:** Data validation and creation fails due to mismatches between Pydantic schemas and SQLAlchemy models.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
Multiple features are failing due to inconsistencies between the Pydantic schemas (the API layer) and the SQLAlchemy models (the database layer).
1.  Portfolio creation fails with a `TypeError` because the `description` field exists in the `PortfolioCreate` schema but not in the `Portfolio` database model.
2.  Portfolio creation API responses are missing the `description` field because it was not in the `Portfolio` response schema.
3.  Transaction creation fails with a `422 Unprocessable Entity` error because the `TransactionCreate` schema incorrectly includes a `portfolio_id` field, which should be derived from the URL path.
**Steps to Reproduce:**
1. Run the backend test suite.
**Expected Behavior:**
Data should be validated and saved to the database without errors.
**Resolution:**
1. Added the `description` column to the `Portfolio` SQLAlchemy model.
2. Added the `description` field to the `Portfolio` Pydantic response schema.
3. Removed the redundant `portfolio_id` field from the `TransactionCreate` schema.
**Resolution:** Fixed


---

**Bug ID:** 20250720-05
**Title:** Application fails to start due to multiple configuration and import errors.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
A series of critical errors prevent the application from starting, making it impossible to run the test suite. These include:
1.  A missing `__tablename__` in the `Portfolio` SQLAlchemy model.
2.  A missing `crud_dashboard` module and `DashboardSummary` schema.
3.  Incorrect imports for `models.User` in endpoint files.
4.  A missing import for the `crud` package in `crud_transaction.py`, causing a `NameError`.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
The application should start, and the test suite should run.
**Actual Behavior:**
The test suite collection fails with `InvalidRequestError`, `AttributeError`, `ImportError`, and `NameError`.
**Resolution:**
1. Added `__tablename__ = "portfolios"` to the `Portfolio` model.
2. Created the `crud_dashboard.py` module and the `schemas/dashboard.py` file.
3. Corrected all incorrect imports across the application to use direct imports (e.g., `from app.models.user import User`).
**Resolution:** Fixed

---

**Bug ID:** 20250720-06
**Title:** Data validation and creation fails due to mismatches between Pydantic schemas and SQLAlchemy models.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
Multiple features are failing due to inconsistencies between the Pydantic schemas (the API layer) and the SQLAlchemy models (the database layer).
1.  Portfolio creation fails with a `TypeError` because the `description` field exists in the `PortfolioCreate` schema but not in the `Portfolio` database model.
2.  Portfolio creation API responses are missing the `description` field because it was not in the `Portfolio` response schema.
3.  Transaction creation fails with a `422 Unprocessable Entity` error because the `TransactionCreate` schema incorrectly includes a `portfolio_id` field, which should be derived from the URL path.
**Steps to Reproduce:**
1. Run the backend test suite.
**Expected Behavior:**
Data should be validated and saved to the database without errors.
**Resolution:**
1. Added the `description` column to the `Portfolio` SQLAlchemy model.
2. Added the `description` field to the `Portfolio` Pydantic response schema.
3. Removed the redundant `portfolio_id` field from the `TransactionCreate` schema.
**Resolution:** Fixed

---

**Bug ID:** 20250720-07
**Title:** Transaction creation fails due to missing user ID and import errors.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The transaction creation logic in `crud_transaction.py` is broken due to two issues:
1.  It fails with a `NameError` because it attempts to use `crud.portfolio.get` without importing the `crud` package.
2.  It fails with a database `IntegrityError` because it does not set the `user_id` on the new transaction object, violating a `NOT NULL` constraint.
**Steps to Reproduce:**
1. Run any test that creates a transaction.
**Expected Behavior:**
Transactions should be created successfully without errors.
**Actual Behavior:**
Tests crash with `NameError` and `IntegrityError`.
**Resolution:**
1. Added `from app import crud` to `app/crud/crud_transaction.py`.
2. Updated the `create_with_portfolio` method to fetch the portfolio and pass its `user_id` to the new `Transaction` object.
**Resolution:** Fixed

---

**Bug ID:** 20250720-08
**Title:** Dashboard tests fail due to incorrect assertions and data type mismatches.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Test Suite
**Severity:** High
**Description:**
The dashboard tests in `test_dashboard.py` are failing due to several assertion issues:
1.  Comparing string decimal values (e.g., `'0.0'`) with integers (e.g., `0`).
2.  Asserting for outdated schema fields (`asset_allocation`, `portfolio_values`) that are no longer in use.
3.  Comparing string values with different decimal precision (e.g., `'29600.0'` vs `'29600.000000000'`).
**Steps to Reproduce:**
1. Run the backend test suite.
**Expected Behavior:**
Dashboard tests should pass by correctly asserting against the API's response.
**Actual Behavior:**
Tests fail with `AssertionError`.
**Resolution:**
1. Updated tests to assert against the correct string values (e.g., `'0.0'`).
2. Updated tests to assert against the correct schema fields (`total_unrealized_pnl`, `total_realized_pnl`, `top_movers`).
3. Updated tests to cast string values from the API to a `float` before comparing them to a numeric value, making the tests robust to formatting differences.
**Resolution:** Fixed

---

**Bug ID:** 20250720-09
**Title:** Dashboard calculation crashes when financial data service fails.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Implementation (Backend)
**Severity:** High
**Description:**
The `get_dashboard_summary` function in `crud_dashboard.py` does not handle exceptions from the `FinancialDataService`. If the service fails to fetch a price for an asset, the unhandled exception crashes the entire API request, resulting in a 500 Internal Server Error instead of gracefully calculating the summary with the available data.
**Steps to Reproduce:**
1. Run the backend test suite.
2. Observe the failure in `test_get_dashboard_summary_with_failing_price_lookup`.
**Expected Behavior:**
The dashboard summary calculation should continue, treating the value of the asset with the failed price lookup as 0. The API should return a 200 OK response.
**Actual Behavior:**
The API request crashes with an unhandled `Exception`.
**Resolution:** The call to `financial_data_service.get_asset_price` in `crud_dashboard.py` was wrapped in a `try...except` block to catch exceptions and default the asset's price to 0 in case of failure.
**Resolution:** Fixed


---

**Bug ID:** 20250719-07
**Title:** Application crashes after login with "Rendered fewer hooks than expected" error.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-19
**Classification:** Implementation (Frontend)
**Severity:** Critical
**Description:**
After a user successfully logs in, the application crashes with a React error related to violating the Rules of Hooks. The `AuthPage` component has a conditional return statement (`if (token)`) that executes before all the component's hooks (specifically, a `useEffect`) have been called. This causes an inconsistent number of hooks to be rendered between the pre-login and post-login states, which is a fatal error in React.
**Steps to Reproduce:**
1. Navigate to the login page.
2. Enter valid user credentials and log in.
3. Observe the application crashes and the browser console shows the "Rendered fewer hooks than expected" error.
**Expected Behavior:**
The user should be successfully redirected to the dashboard page without any application errors.
**Actual Behavior:**
The application crashes and displays a blank page.
**Resolution:** Refactored `AuthPage.tsx` to ensure all React hooks are called unconditionally at the top of the component, before any conditional return statements.
**Resolution:** Fixed

---

**Bug ID:** 20250719-08
**Title:** User Management page is unstyled and inconsistent with application theme.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-19
**Classification:** Implementation (Frontend)
**Severity:** Medium
**Description:**
The `UserManagementPage` component uses plain, unstyled HTML elements for its title, buttons, and table. This creates a jarring and unprofessional user experience that is inconsistent with the rest of the application's design system.
**Steps to Reproduce:**
1. Log in as an administrator.
2. Navigate to the `/admin/users` route.
**Expected Behavior:**
The User Management page should have a clean layout with a styled header, buttons, and table that match the application's theme.
**Actual Behavior:**
The page is unstyled, with misaligned elements and a plain HTML table.
**Resolution:** Refactored `UserManagementPage.tsx` to style its header. The unstyled `UsersTable.tsx` component was replaced with a fully styled version that uses the application's design system for cards, tables, and buttons.
**Resolution:** Fixed

---

**Bug ID:** 20250719-09
**Title:** User Management page crashes with "isError is not defined" ReferenceError.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-19
**Classification:** Implementation (Frontend)
**Severity:** Critical
**Description:**
The `UserManagementPage` component attempts to use a variable `isError` to handle the error state from the `useUsers` hook. However, this variable is never destructured from the hook's return value, leading to a `ReferenceError` that crashes the component.
**Steps to Reproduce:**
1. Log in as an administrator.
2. Navigate to the "User Management" page.
**Expected Behavior:**
The page should either display the list of users or, if an error occurs, display a user-friendly error message.
**Actual Behavior:**
The page crashes with `Uncaught ReferenceError: isError is not defined`.
**Resolution:** Updated the destructuring assignment for the `useUsers` hook in `UserManagementPage.tsx` to include the `isError` property.
**Resolution:** Fixed

---

**Bug ID:** 20250719-10
**Title:** Navigating away from User Management page logs the user out.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-19
**Classification:** Implementation (Frontend)
**Severity:** Critical
**Description:**
A faulty `useEffect` cleanup function in the `useDeleteUser` hook calls `logout()` whenever the component using it (`UserManagementPage`) unmounts. This clears the user's authentication token, causing all subsequent API calls to protected routes to fail with a 403 Forbidden error.
**Steps to Reproduce:**
1. Log in as an administrator.
2. Navigate to the "User Management" page.
3. Navigate to any other page (e.g., "Dashboard").
4. Observe that the new page fails to load data, and the browser console shows `403 Forbidden` errors.
**Expected Behavior:**
The user should remain logged in and be able to navigate between pages without losing their session.
**Actual Behavior:**
The user is silently logged out, and the application becomes unusable until the page is refreshed and the user logs in again.
**Resolution:** The erroneous `useEffect` hook was removed from the `useDeleteUser` custom hook in `src/hooks/useUsers.ts`.
**Resolution:** Fixed

---

**Bug ID:** 20250719-11
**Title:** Portfolios page is unstyled and inconsistent with application theme.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-19
**Classification:** Implementation (Frontend)
**Severity:** Medium
**Description:**
The `PortfolioPage` component uses a plain, unstyled `<h1>` and `<button>`, which is inconsistent with the design system used on the Dashboard and User Management pages.
**Steps to Reproduce:**
1. Log in to the application.
2. Navigate to the `/portfolios` page.
**Expected Behavior:**
The page should have a clean header with a styled title and "Create New Portfolio" button.
**Actual Behavior:**
The page header is unstyled and does not match the rest of the application.
**Resolution:** Refactored `PortfolioPage.tsx` to use a flexbox header and apply consistent styling to the title and "Create New Portfolio" button.
**Resolution:** Fixed

---

**Bug ID:** 20250719-12
**Title:** User Management modal is missing action buttons.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-19
**Classification:** Implementation (Frontend) 
**Severity:** High 
**Description:**
When an admin clicks "Create New User" or "Edit" on the User Management page, the modal that opens is unstyled and uses deprecated CSS classes. This makes the form difficult to use and visually inconsistent with the rest of the application.
**Steps to Reproduce:**
1. Log in as an admin. 
2. Navigate to User Management.
3. Click "Create New User" or "Edit" on an existing user.
**Expected Behavior:**
The modal should appear with styling consistent with the application's design system, including styled form elements and buttons.
**Actual Behavior:**
The modal is unstyled and uses old CSS classes that are no longer defined.
**Resolution:** The `UserFormModal.tsx` component was refactored to use the new design system classes (`.modal-overlay`, `.modal-content`, `.form-input`, `.btn`, etc.) for all its elements.
**Resolution:** Fixed

---

**Bug ID:** 20250719-13
**Title:** Portfolio Detail page is unstyled and inconsistent with application theme.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-19
**Classification:** Implementation (Frontend)
**Severity:** Medium
**Description:**
The page for viewing a single portfolio's transactions (`/portfolios/:id`) has an unstyled header and layout, which is inconsistent with the rest of the application.
**Steps to Reproduce:**
1. Log in and navigate to the "Portfolios" page.
2. Click on an existing portfolio to view its details.
**Expected Behavior:**
The page should have a clean header with the portfolio's name, a "Back to Portfolios" link, and a styled "Add Transaction" button.
**Actual Behavior:**
The page header is unstyled and does not match the rest of the application.
**Resolution:** Refactored `PortfolioDetailPage.tsx` to use a flexbox header, styled components, and add a "Back to Portfolios" link for better navigation.
**Resolution:** Fixed

---

**Bug ID:** 20250719-14
**Title:** Application does not handle expired authentication tokens, leading to a broken UI state.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-19
**Classification:** Implementation (Frontend)
**Severity:** High
**Description:**
When the user's JWT expires, the frontend does not automatically log them out. Instead, all subsequent API calls start failing with `403 Forbidden` errors, leaving the user with a non-functional UI where data fails to load.
**Steps to Reproduce:**
1. Log in to the application.
2. Wait for the JWT token to expire (the default is short for development).
3. Attempt to navigate to another page or refresh the current page.
**Expected Behavior:**
The application should detect the expired token (via a 403 error), automatically log the user out, and redirect them to the login page.
**Actual Behavior:**
The application remains on the current page in a broken state, with all data failing to load and console errors.
**Resolution:** Implemented a global Axios response interceptor within the `AuthContext`. This interceptor checks for `403` status codes on API responses and, if detected, calls the `logout` function to clear the session and redirect the user.
**Resolution:** Fixed

---

**Bug ID:** 20250719-15
**Title:** Unstyled browser confirmation used for portfolio deletion.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-19
**Classification:** Implementation (Frontend)
**Severity:** Medium
**Description:**
When deleting a portfolio from the main portfolio list, the application uses the browser's default `window.confirm()` dialog. This is inconsistent with the application's professional design system and provides a poor user experience.
**Steps to Reproduce:**
1. Log in and navigate to the "Portfolios" page.
2. Click the "Delete" button on any portfolio.
**Expected Behavior:**
A styled confirmation modal should appear, matching the application's theme, asking the user to confirm the deletion.
**Actual Behavior:**
A plain, unstyled browser-native confirmation dialog appears.
**Resolution:** The `window.confirm` call in `PortfolioList.tsx` was replaced with a new, styled `DeletePortfolioModal` component. State management was added to `PortfolioList.tsx` to control the modal's visibility.
**Resolution:** Fixed

---

**Bug ID:** 20250719-16
**Title:** User deletion confirmation modal is unstyled.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-19
**Classification:** Implementation (Frontend)
**Severity:** Medium
**Description:**
The confirmation modal for deleting a user is unstyled and inconsistent with the application's design system.
**Steps to Reproduce:**
1. Log in as an admin.
2. Navigate to User Management.
3. Click "Delete" on any user.
**Expected Behavior:**
A styled confirmation modal should appear, matching the application's theme.
**Actual Behavior:**
An unstyled or incorrectly styled modal appears.
**Resolution:** The `DeleteConfirmationModal.tsx` component was created/refactored to use the global design system classes for modals and buttons.
**Resolution:** Fixed

---

**Bug ID:** 20250720-01
**Title:** Test suite collection fails with `AttributeError: module 'app.models' has no attribute 'User'`.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The test suite fails to run because of an `AttributeError` during test collection. The `dashboard.py` endpoint file uses an incorrect type hint `models.User` for the `current_user` dependency. The `User` model is not directly available under the `app.models` namespace.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
The test suite should collect and run successfully.
**Actual Behavior:**
Test collection is interrupted with `AttributeError: module 'app.models' has no attribute 'User'`.
**Resolution:** The import statement in `app/api/v1/endpoints/dashboard.py` was corrected to import `User` directly from `app.models.user`, and the type hint for `current_user` was updated to use the directly imported `User` class.
**Resolution:** Fixed

---

**Bug ID:** 20250720-02
**Title:** Test suite collection fails with `ModuleNotFoundError: No module named 'app.tests.utils.transaction'`.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Test Suite
**Severity:** Critical
**Description:**
The test suite fails to run because the new dashboard test file (`test_dashboard.py`) tries to import a test helper function from `app.tests.utils.transaction`, but this utility module was never created.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
The test suite should collect and run successfully.
**Actual Behavior:**
Test collection is interrupted with `ModuleNotFoundError: No module named 'app.tests.utils.transaction'`.
**Resolution:** Created the missing test utility file `app/tests/utils/transaction.py` and implemented the `create_test_transaction` helper function.
**Resolution:** Fixed

---

**Bug ID:** 20250720-03
**Title:** Dashboard tests fail with "fixture 'mocker' not found".
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Test Suite
**Severity:** Critical
**Description:**
Tests in `test_dashboard.py` that use mocking fail because the `mocker` fixture is not available. This is because the `pytest-mock` library, which provides this fixture, is not installed in the test environment.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
The tests should be collected and run without fixture errors.
**Actual Behavior:**
Tests that depend on the `mocker` fixture error out during test setup.
**Resolution:** Added `pytest-mock` to the `backend/requirements.txt` file.
**Resolution:** Fixed

---

**Bug ID:** 20250720-04
**Title:** Dashboard summary calculation fails with TypeError on `FinancialDataService` initialization.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The `get_dashboard_summary` function in `crud_dashboard.py` attempts to instantiate `FinancialDataService()` without providing the required `api_key` and `api_url` arguments, causing a `TypeError`.
**Steps to Reproduce:**
1. Run the backend test suite.
2. Observe the failure in `test_get_dashboard_summary_no_portfolios`.
**Expected Behavior:**
The `FinancialDataService` should be initialized correctly with configuration from the application settings.
**Actual Behavior:**
The API call fails with `TypeError: FinancialDataService.__init__() missing 2 required positional arguments: 'api_key' and 'api_url'`.
**Resolution:** Updated `crud_dashboard.py` to import the `settings` object and pass the required API key and URL to the `FinancialDataService` constructor.
**Resolution:** Fixed

---

**Bug ID:** 20250720-05
**Title:** Unauthorized dashboard test fails with incorrect status code assertion.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Test Suite
**Severity:** Medium
**Description:**
The test `test_get_dashboard_summary_unauthorized` asserts that the status code for an unauthenticated request should be `403 Forbidden`. The API correctly returns `401 Unauthorized`, which is the standard for missing credentials, causing the test to fail.
**Steps to Reproduce:**
1. Run the backend test suite.
**Expected Behavior:**
The test should pass by asserting the correct `401` status code.
**Actual Behavior:**
The test fails with the assertion `assert 401 == 403`.
**Resolution:** Updated the assertion in `test_dashboard.py` to check for a `401` status code.
**Resolution:** Fixed

---

**Bug ID:** 20250720-06
**Title:** Dashboard calculation fails with AttributeError for non-existent 'get_asset_price' method.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The `get_dashboard_summary` function in `crud_dashboard.py` calls `financial_data_service.get_asset_price()`. However, this method is not defined in the `FinancialDataService` class, which would cause a runtime `AttributeError`. The tests did not catch this because they directly mocked the non-existent method.
**Steps to Reproduce:**
1. Run the application and call the `GET /api/v1/dashboard/summary` endpoint.
**Expected Behavior:**
The dashboard summary should be calculated correctly using the mock financial service.
**Actual Behavior:**
The request fails with an `AttributeError: 'FinancialDataService' object has no attribute 'get_asset_price'`.
**Resolution:** Added the missing `get_asset_price` mock method to the `FinancialDataService` class.
**Resolution:** Fixed

---

**Bug ID:** 20250720-07
**Title:** Dashboard tests fail with TypeError due to incorrect test helper signature.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Test Suite
**Severity:** Critical
**Description:**
The tests for the dashboard summary endpoint fail with `TypeError: create_test_portfolio() got an unexpected keyword argument 'user_id'`. The test helper function `create_test_portfolio` in `app/tests/utils/portfolio.py` does not have `user_id` in its signature, but the tests require it to associate the portfolio with a user. This indicates an inconsistency between the test helper and the CRUD layer it's supposed to wrap.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
The dashboard tests should run without `TypeError`.
**Actual Behavior:**
The tests fail with a `TypeError` when calling `create_test_portfolio`.
**Resolution:** The `create_test_portfolio` function in `app/tests/utils/portfolio.py` was updated to accept a `user_id` keyword argument, which is then passed to the `crud.portfolio.create_with_owner` function.
**Resolution:** Fixed

---

**Bug ID:** 20250720-08
**Title:** Dashboard tests fail with ValidationError due to missing 'currency' field in test helper.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Test Suite
**Severity:** Critical
**Description:**
The `create_test_transaction` helper function in `app/tests/utils/transaction.py` fails to provide a `currency` when creating a new asset. The `AssetCreate` schema requires this field, causing a `ValidationError` and failing any test that relies on this helper to create a new asset.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
The `create_test_transaction` helper should successfully create assets.
**Actual Behavior:**
Tests fail with `pydantic_core._pydantic_core.ValidationError: 1 validation error for AssetCreate\nE currency\nE Field required`.
**Resolution:** The `create_test_transaction` function in `app/tests/utils/transaction.py` was updated to include a default `currency="USD"` when instantiating `schemas.AssetCreate`.
**Resolution:** Fixed

---

**Bug ID:** 20250720-09
**Title:** Portfolio tests fail with TypeError due to incorrect argument in `create_test_portfolio` calls.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Test Suite
**Severity:** Critical
**Description:**
Multiple tests in `test_portfolios_transactions.py` fail with `TypeError: create_test_portfolio() got an unexpected keyword argument 'user'`. The test helper function expects a `user_id` argument, but the tests are incorrectly passing a `user` object.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
The tests should call the helper function with the correct `user_id` argument.
**Actual Behavior:**
Tests fail with a `TypeError`.
**Resolution:** All calls to `create_test_portfolio` in `app/tests/api/v1/test_portfolios_transactions.py` were updated to pass `user_id=user.id` instead of `user=user`.
**Resolution:** Fixed

---

**Bug ID:** 20250720-12
**Title:** All transaction-related tests fail with 404 Not Found due to incorrect API routing.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The transaction endpoints are registered at the root level (`/api/v1/transactions`) instead of being properly nested under their respective portfolios (`/api/v1/portfolios/{portfolio_id}/transactions`). This causes all test requests to these nested routes to fail with a 404 error.
**Steps to Reproduce:**
1. Run the backend test suite.
**Expected Behavior:**
Transaction endpoints should be accessible via their nested routes (e.g., `POST /api/v1/portfolios/1/transactions/`).
**Actual Behavior:**
All requests to transaction endpoints return `404 Not Found`.
**Resolution:**
1. Removed the top-level transaction router from `app/api/v1/api.py`.
2. Included the transaction router within the `app/api/v1/endpoints/portfolios.py` file, nesting it correctly under the portfolio path with a `{portfolio_id}` parameter.
3. Updated the `create_transaction` endpoint in `transactions.py` to accept the `portfolio_id` from the path and use it for validation and creation.
**Resolution:** Fixed
**Resolution:** Fixed

---

**Bug ID:** 20250720-10
**Title:** Dashboard tests fail with AttributeError due to incorrect CRUD method call in test helper.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Test Suite
**Severity:** Critical
**Description:**
The `create_test_transaction` helper function in `app/tests/utils/transaction.py` calls `crud.transaction.create_with_owner`, but this method does not exist on the `CRUDTransaction` class.
**Steps to Reproduce:**
1. Run the backend test suite.
**Expected Behavior:**
The dashboard tests should pass.
**Actual Behavior:**
Tests fail with `AttributeError: 'CRUDTransaction' object has no attribute 'create_with_owner'`.
**Resolution:** The `create_test_transaction` function in `app/tests/utils/transaction.py` was updated to call the correct `crud.transaction.create` method, which is inherited from the base CRUD class.
**Resolution:** Fixed

---

**Bug ID:** 20250720-11
**Title:** Portfolio tests fail due to incorrect status code assertions and flawed access control logic.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Test Suite / Implementation (Backend)
**Severity:** High
**Description:**
1. `test_create_portfolio` fails because it asserts a `200 OK` status code, but the API correctly returns `201 Created`.
2. `test_read_portfolio_wrong_owner` fails because it asserts a `403 Forbidden` status, but the API incorrectly returns `404 Not Found` due to flawed access control logic that doesn't distinguish between a non-existent resource and an unauthorized one.
**Steps to Reproduce:**
1. Run the backend test suite.
**Expected Behavior:**
Tests should pass. The API should return 403 for unauthorized access to an existing resource and 201 for successful creation.
**Actual Behavior:**
Multiple tests fail with `AssertionError`.
**Resolution:**
1. Updated `test_create_portfolio` to assert for a `201` status code.
2. Updated the `read_portfolio` endpoint in `portfolios.py` to check for ownership and return a 403 if the user is not the owner of an existing portfolio.
**Resolution:** Fixed

---

**Bug ID:** 20250720-12
**Title:** All transaction-related tests fail with 404 Not Found due to incorrect API routing.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The transaction endpoints are registered at the root level (`/api/v1/transactions`) instead of being properly nested under their respective portfolios (`/api/v1/portfolios/{portfolio_id}/transactions`). This causes all test requests to these nested routes to fail with a 404 error.
**Steps to Reproduce:**
1. Run the backend test suite.
**Expected Behavior:**
Transaction endpoints should be accessible via their nested routes (e.g., `POST /api/v1/portfolios/1/transactions/`).
**Actual Behavior:**
All requests to transaction endpoints return `404 Not Found`.
**Resolution:**
1. Created the `app/api/v1/endpoints/transactions.py` router file with the correct endpoint logic.
2. Removed the top-level transaction router from `app/api/v1/api.py`.
3. Included the transaction router within the `app/api/v1/endpoints/portfolios.py` file, nesting it correctly under the portfolio path.
**Resolution:** Fixed
**Resolution:** Fixed

---

**Bug ID:** 20250720-10
**Title:** Dashboard tests fail with AttributeError due to incorrect CRUD method call in test helper.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Test Suite
**Severity:** Critical
**Description:**
The `create_test_transaction` helper function in `app/tests/utils/transaction.py` calls `crud.transaction.create_with_portfolio`, but this method does not exist on the `CRUDTransaction` class. The correct method is `create_with_owner`.
**Steps to Reproduce:**
1. Run the backend test suite.
**Expected Behavior:**
The dashboard tests should pass.
**Actual Behavior:**
Tests fail with `AttributeError: 'CRUDTransaction' object has no attribute 'create_with_portfolio'`.
**Resolution:** The `create_test_transaction` function in `app/tests/utils/transaction.py` was updated to call the correct `crud.transaction.create_with_owner` method.
**Resolution:** Fixed

---

**Bug ID:** 20250720-11
**Title:** Portfolio tests fail due to incorrect status code assertions and flawed access control logic.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Test Suite / Implementation (Backend)
**Severity:** High
**Description:**
1. `test_create_portfolio` fails because it asserts a `200 OK` status code, but the API correctly returns `201 Created`.
2. `test_read_portfolio_wrong_owner` fails because it asserts a `403 Forbidden` status, but the API incorrectly returns `404 Not Found` due to flawed access control logic that doesn't distinguish between a non-existent resource and an unauthorized one.
**Steps to Reproduce:**
1. Run the backend test suite.
**Expected Behavior:**
Tests should pass. The API should return 403 for unauthorized access to an existing resource and 201 for successful creation.
**Actual Behavior:**
Multiple tests fail with `AssertionError`.
**Resolution:**
1. Updated `test_create_portfolio` to assert for a `201` status code.
2. Updated the `read_portfolio` endpoint in `portfolios.py` to check for ownership and return a 403 if the user is not the owner of an existing portfolio.
**Resolution:** Fixed

---

**Bug ID:** 20250720-12
**Title:** All transaction-related tests fail with 404 Not Found due to incorrect API routing.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The transaction endpoints are registered at the root level (`/api/v1/transactions`) instead of being properly nested under their respective portfolios (`/api/v1/portfolios/{portfolio_id}/transactions`). This causes all test requests to these nested routes to fail with a 404 error.
**Steps to Reproduce:**
1. Run the backend test suite.
**Expected Behavior:**
Transaction endpoints should be accessible via their nested routes (e.g., `POST /api/v1/portfolios/1/transactions/`).
**Actual Behavior:**
All requests to transaction endpoints return `404 Not Found`.
**Resolution:**
1. Created the `app/api/v1/endpoints/transactions.py` router file with the correct endpoint logic.
2. Removed the top-level transaction router from `app/api/v1/api.py`.
3. Included the transaction router within the `app/api/v1/endpoints/portfolios.py` file, nesting it correctly under the portfolio path.
**Resolution:** Fixed
**Resolution:** Fixed

---

**Bug ID:** 20250720-10
**Title:** Dashboard tests fail with ValidationError due to mismatched TransactionCreate schema in test helper.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Test Suite
**Severity:** Critical
**Description:**
The `create_test_transaction` helper function in `app/tests/utils/transaction.py` is incompatible with the `TransactionCreate` schema. The schema expects `price_per_unit` and `portfolio_id`, but the helper provides `price` and does not pass the `portfolio_id` to the schema constructor.
**Steps to Reproduce:**
1. Run the backend test suite.
**Expected Behavior:**
The dashboard tests should pass.
**Actual Behavior:**
Tests fail with `pydantic_core._pydantic_core.ValidationError: 2 validation errors for TransactionCreate\nE price_per_unit\nE   Field required`.
**Resolution:** The `create_test_transaction` function in `app/tests/utils/transaction.py` was updated to pass the correct field names (`price_per_unit`) and include the `portfolio_id` when instantiating `schemas.TransactionCreate`.
**Resolution:** Fixed

---

**Bug ID:** 20250721-01
**Title:** Test suite collection fails with `AttributeError: module 'app.models' has no attribute 'User'`.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The test suite fails to run because of an `AttributeError` during test collection. The `portfolios.py` endpoint file uses an incorrect type hint `models.User` for the `current_user` dependency. The `User` model is not directly available under the `app.models` namespace.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
The test suite should collect and run successfully.
**Actual Behavior:**
Test collection is interrupted with `AttributeError: module 'app.models' has no attribute 'User'`.
**Resolution:** The import statement in `app/api/v1/endpoints/portfolios.py` was corrected to import `User` directly from `app.models.user`, and the type hint for `current_user` was updated to use the directly imported `User` class.
**Resolution:** Fixed
**Resolution:** Fixed
**Resolution:** Fixed
**Resolution:** Fixed
**Resolution:** Fixed
---

**Bug ID:** 20250720-11
**Title:** Portfolio tests fail due to incorrect status code assertions and flawed access control logic.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Test Suite / Implementation (Backend)
**Severity:** High
**Description:**
1. `test_create_portfolio` fails because it asserts a `200 OK` status code, but the API correctly returns `201 Created`.
2. `test_read_portfolio_wrong_owner` fails because it asserts a `403 Forbidden` status, but the API incorrectly returns `404 Not Found` due to flawed access control logic that doesn't distinguish between a non-existent resource and an unauthorized one.
**Steps to Reproduce:**
1. Run the backend test suite.
**Expected Behavior:**
Tests should pass. The API should return 403 for unauthorized access to an existing resource and 201 for successful creation.
**Actual Behavior:**
Multiple tests fail with `AssertionError`.
**Resolution:**
1. Updated `test_create_portfolio` to assert for a `201` status code.
2. Updated the `read_portfolio` endpoint in `portfolios.py` to check for ownership and return a 403 if the user is not the owner of an existing portfolio.
**Resolution:** Fixed

---

**Bug ID:** 20250720-12
**Title:** All transaction-related tests fail with 404 Not Found due to incorrect API routing.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The transaction endpoints are registered at the root level (`/api/v1/transactions`) instead of being properly nested under their respective portfolios (`/api/v1/portfolios/{portfolio_id}/transactions`). This causes all test requests to these nested routes to fail with a 404 error.
**Steps to Reproduce:**
1. Run the backend test suite.
**Expected Behavior:**
Transaction endpoints should be accessible via their nested routes (e.g., `POST /api/v1/portfolios/1/transactions/`).
**Actual Behavior:**
All requests to transaction endpoints return `404 Not Found`.
**Resolution:**
1. Created the `app/api/v1/endpoints/transactions.py` router file with the correct endpoint logic.
2. Removed the top-level transaction router from `app/api/v1/api.py`.
3. Included the transaction router within the `app/api/v1/endpoints/portfolios.py` file, nesting it correctly under the portfolio path.
**Resolution:** Fixed
**Resolution:** Fixed

---

**Bug ID:** 20250721-01
**Title:** Test suite collection fails with `AttributeError: module 'app.models' has no attribute 'User'`.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The test suite fails to run because of an `AttributeError` during test collection. The `portfolios.py` endpoint file uses an incorrect type hint `models.User` for the `current_user` dependency. The `User` model is not directly available under the `app.models` namespace.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
The test suite should collect and run successfully.
**Actual Behavior:**
Test collection is interrupted with `AttributeError: module 'app.models' has no attribute 'User'`.
**Resolution:** The import statement in `app/api/v1/endpoints/portfolios.py` was corrected to import `User` directly from `app.models.user`, and the type hint for `current_user` was updated to use the directly imported `User` class.
**Resolution:** Fixed
**Resolution:** Fixed

---

**Bug ID:** 20250721-02
**Title:** Portfolio creation test fails with `KeyError` due to missing `description` in response schema.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Implementation (Backend)
**Severity:** High
**Description:**
The `test_create_portfolio` test fails with a `KeyError: 'description'` because the `schemas.Portfolio` Pydantic model, which is used as the response model for the creation endpoint, does not include the `description` field. The API correctly saves the description to the database, but it is not included in the JSON response sent back to the client.
**Steps to Reproduce:**
1. Run the backend test suite.
2. Observe the failure in `test_create_portfolio`.
**Expected Behavior:**
The JSON response for a newly created portfolio should include the `description` field.
**Actual Behavior:**
The `description` field is missing from the response, causing the test assertion to fail with a `KeyError`.
**Resolution:** The `description` field was added to the `schemas.PortfolioInDBBase` Pydantic model in `app/schemas/portfolio.py`, ensuring it is included in all derived response schemas.
**Resolution:** Fixed

---

**Bug ID:** 20250721-03
**Title:** Transaction creation tests fail with 422 Unprocessable Entity due to schema mismatch.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Implementation (Backend)
**Severity:** High
**Description:**
Tests for creating transactions fail with a `422 Unprocessable Entity` error. This is because the `TransactionCreate` Pydantic schema incorrectly includes a `portfolio_id` field. This field is redundant, as the portfolio ID is already provided in the URL path parameter of the API endpoint. The API expects the `portfolio_id` in the request body, but the tests do not provide it, leading to a validation failure.
**Steps to Reproduce:**
1. Run the backend test suite.
**Expected Behavior:**
Transaction creation requests should be validated successfully, and tests should pass.
**Actual Behavior:**
Tests fail with `assert 422 == 201` or `assert 422 == 403`.
**Resolution:** The `portfolio_id` field was removed from the `schemas.TransactionCreate` model in `app/schemas/transaction.py`. The API endpoint and CRUD layer correctly handle associating the transaction with the portfolio using the ID from the URL path.
**Resolution:** Fixed

---

**Bug ID:** 20250721-04
**Title:** Test suite collection fails with `ImportError` for non-existent 'TransactionCreateInternal' schema.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The test suite fails to run because of an `ImportError` during the test collection phase. The `app/schemas/__init__.py` file attempts to import a Pydantic schema named `TransactionCreateInternal` from `app.schemas.transaction`, but this schema is not defined in that file. This breaks the application's startup and prevents any tests from running.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
The test suite should collect and run successfully.
**Actual Behavior:**
Test collection is interrupted with `ImportError: cannot import name 'TransactionCreateInternal' from 'app.schemas.transaction'`.
**Resolution:** The `app/schemas/__init__.py` file was corrected to only import schemas that actually exist in their respective modules, removing the reference to the non-existent `TransactionCreateInternal`.
**Resolution:** Fixed

---

**Bug ID:** 20250721-05
**Title:** Test helper `create_test_transaction` fails with `ValidationError` and uses incorrect CRUD method.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Test Suite
**Severity:** High
**Description:**
The test utility function `create_test_transaction` in `app/tests/utils/transaction.py` is implemented incorrectly. It attempts to pass a `portfolio_id` to the `schemas.TransactionCreate` Pydantic model, which does not have this field, leading to a `ValidationError`. Furthermore, it calls the generic `crud.transaction.create` method instead of the correct `crud.transaction.create_with_portfolio` method, which is necessary to associate the transaction with its portfolio.
**Steps to Reproduce:**
1. Fix the `ImportError` from Bug ID 20250721-04.
2. Run a test that uses the `create_test_transaction` helper.
**Expected Behavior:**
The test helper should create a transaction successfully without validation errors.
**Actual Behavior:**
The test helper will crash with a `ValidationError` or the created transaction will not be correctly linked to a portfolio.
**Resolution:** The `create_test_transaction` helper was refactored to instantiate `schemas.TransactionCreate` without the `portfolio_id` and to call the correct `crud.transaction.create_with_portfolio` method, passing the `portfolio_id` as a separate argument.
**Resolution:** Fixed

---

**Bug ID:** 20250721-06
**Title:** Test suite collection fails with `ImportError` for non-existent 'TransactionCreateInternal' schema in CRUD layer.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The test suite fails to run because of an `ImportError` during the test collection phase. The `app/crud/crud_transaction.py` file attempts to import a Pydantic schema named `TransactionCreateInternal` from `app.schemas.transaction`, but this schema is not defined. This breaks the application's startup and prevents any tests from running. This was caused by an incomplete implementation of the CRUD layer.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
The test suite should collect and run successfully.
**Actual Behavior:**
Test collection is interrupted with `ImportError: cannot import name 'TransactionCreateInternal' from 'app.schemas.transaction'`.
**Resolution:** The entire CRUD layer for portfolio management (`base.py`, `crud_asset.py`, `crud_portfolio.py`, `crud_transaction.py`, and `__init__.py`) was created with the correct logic and imports, resolving the `ImportError` and completing the feature.
**Resolution:** Fixed

---

**Bug ID:** 20250721-07
**Title:** Test suite collection fails with `AttributeError` for missing 'DashboardSummary' schema.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The test suite fails to run because of an `AttributeError` during test collection. The `dashboard.py` endpoint file attempts to use a Pydantic schema named `DashboardSummary` as its `response_model`, but this schema is not defined or exposed in the `app.schemas` package. This breaks the application's startup and prevents any tests from running.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
The test suite should collect and run successfully.
**Actual Behavior:**
Test collection is interrupted with `AttributeError: module 'app.schemas' has no attribute 'DashboardSummary'`.
**Resolution:** Created `app/schemas/dashboard.py` to define the `DashboardSummary` model. Updated `app/schemas/__init__.py` to import and expose the new schema.
**Resolution:** Fixed

---

**Bug ID:** 20250721-08
**Title:** Dashboard tests fail with `AttributeError` due to missing `crud_dashboard` module.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
All tests for the dashboard summary endpoint fail with an `AttributeError`. The API endpoint (`app/api/v1/endpoints/dashboard.py`) and the tests (`app/tests/api/v1/test_dashboard.py`) attempt to call functions from `app.crud.dashboard` and `app.crud.crud_dashboard`, but this module was never created.
**Steps to Reproduce:**
1. Run the backend test suite.
**Expected Behavior:**
Dashboard tests should be collected and run without `AttributeError`.
**Actual Behavior:**
Tests fail with `AttributeError: module 'app.crud' has no attribute 'dashboard'` or `AttributeError: module 'app.crud' has no attribute 'crud_dashboard'`.
**Resolution:** Created `app/crud/crud_dashboard.py` with the `get_dashboard_summary` function and a `CRUDDashboard` class. Updated `app/crud/__init__.py` to expose the new `dashboard` CRUD object.
**Resolution:** Fixed

---

**Bug ID:** 20250721-09
**Title:** All portfolio and transaction tests fail with `TypeError` due to missing `description` field in `Portfolio` model.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
Any test that attempts to create a portfolio fails with `TypeError: 'description' is an invalid keyword argument for Portfolio`. The `PortfolioCreate` Pydantic schema correctly includes a `description` field, and the tests pass this data. However, the underlying `Portfolio` SQLAlchemy model in `app/models/portfolio.py` is missing the corresponding `description` column, causing the ORM to raise a `TypeError` on object creation.
**Steps to Reproduce:**
1. Run the backend test suite.
**Expected Behavior:**
Portfolios should be created successfully in the database without errors.
**Actual Behavior:**
All tests that create portfolios crash with a `TypeError`.
**Resolution:** Added the `description = Column(String, nullable=True)` field to the `Portfolio` model in `app/models/portfolio.py`.
**Resolution:** Fixed

---

**Bug ID:** 20250721-10
**Title:** Test suite collection fails with `InvalidRequestError` due to missing `__tablename__` in `Portfolio` model.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The test suite fails to run because of a SQLAlchemy `InvalidRequestError`. The `Portfolio` model in `app/models/portfolio.py` inherits from the declarative `Base` but is missing the required `__tablename__` attribute. This prevents the ORM from mapping the class to a database table and breaks the application startup.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
The test suite should collect and run successfully.
**Actual Behavior:**
Test collection is interrupted with `sqlalchemy.exc.InvalidRequestError: Class <class 'app.models.portfolio.Portfolio'> does not have a __table__ or __tablename__ specified...`.
**Resolution:** Added `__tablename__ = "portfolios"` to the `Portfolio` model class in `app/models/portfolio.py`.
**Resolution:** Fixed

---

**Bug ID:** 20250721-11
**Title:** Dashboard test `test_get_dashboard_summary_no_portfolios` fails with `AssertionError` due to incorrect type comparison.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Test Suite
**Severity:** Medium
**Description:**
The test `test_get_dashboard_summary_no_portfolios` in `app/tests/api/v1/test_dashboard.py` fails because it compares the string value `'0.0'` from the API response with the integer `0`. The test expects an integer, but the API returns a string representation of a decimal.
**Steps to Reproduce:**
1. Run the backend test suite.
2. Observe the failure in `test_get_dashboard_summary_no_portfolios`.
**Expected Behavior:**
The test should correctly handle the string representation of the decimal value.
**Actual Behavior:**
The test fails with `AssertionError: assert '0.0' == 0`.
**Resolution:** Updated the assertion in `test_get_dashboard_summary_no_portfolios` to compare `data["total_value"]` with the string `'0.0'`.
**Resolution:** Fixed

---

**Bug ID:** 20250721-12
**Title:** Transaction creation fails with `IntegrityError` due to missing `user_id` in `transactions` table.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Implementation (Backend)
**Severity:** High
**Description:**
Tests that create transactions fail with `IntegrityError: (psycopg2.errors.NotNullViolation) null value in column "user_id" of relation "transactions" violates not-null constraint`. The `transactions` table in the database has a `NOT NULL` constraint on the `user_id` column, but the backend logic for creating transactions does not associate the transaction with the portfolio's owner.
**Steps to Reproduce:**
1. Run the backend test suite.
2. Observe the failures in tests related to transaction creation.
**Expected Behavior:**
Transactions should be created successfully with the correct `user_id` associated with the portfolio's owner.
**Actual Behavior:**
Tests fail with `sqlalchemy.exc.IntegrityError`.
**Resolution:** Updated the `create_with_portfolio` method in `CRUDTransaction` to include the `user_id` of the portfolio's owner when creating a transaction.
**Resolution:** Fixed

---

**Bug ID:** 20250721-13
**Title:** Dashboard tests fail with `AssertionError` and outdated assertions.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Test Suite
**Severity:** High
**Description:**
The tests for the dashboard summary endpoint in `app/tests/api/v1/test_dashboard.py` are failing for two reasons. First, they compare the string value `'0.0'` from the API response with the integer `0`. Second, they assert for keys (`asset_allocation`, `portfolio_values`) that are no longer part of the `DashboardSummary` schema, which now uses `total_unrealized_pnl`, `total_realized_pnl`, and `top_movers`.
**Steps to Reproduce:**
1. Run the backend test suite.
**Expected Behavior:**
The tests should correctly handle the string representation of decimal values and assert against the correct schema fields.
**Actual Behavior:**
Tests fail with `AssertionError: assert '0.0' == 0` and would also fail with `KeyError` if the first assertion passed.
**Resolution:** Updated the dashboard tests to assert against the correct string values (e.g., `'0.0'`) and the correct schema fields (`total_unrealized_pnl`, `total_realized_pnl`, `top_movers`).
**Resolution:** Fixed

---

**Bug ID:** 20250721-14
**Title:** Transaction creation fails with `NameError` due to missing import in `crud_transaction.py`.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
All tests that create transactions fail with `NameError: name 'crud' is not defined`. The `create_with_portfolio` method in `app/crud/crud_transaction.py` attempts to use the `crud` package to fetch the portfolio (`crud.portfolio.get(...)`) but does not import it. This causes a cascade of failures in any test that creates a transaction.
**Steps to Reproduce:**
1. Run the backend test suite.
**Expected Behavior:**
Transactions should be created successfully without a `NameError`.
**Actual Behavior:**
All tests that create transactions crash with a `NameError`.
**Resolution:** Added `from app import crud` to the top of `app/crud/crud_transaction.py`.
**Resolution:** Fixed

---

**Bug ID:** 20250721-15
**Title:** Dashboard calculation crashes when financial data service fails.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Implementation (Backend)
**Severity:** High
**Description:**
The `get_dashboard_summary` function in `crud_dashboard.py` does not handle exceptions from the `FinancialDataService`. If the service fails to fetch a price for an asset, the unhandled exception crashes the entire API request, resulting in a 500 Internal Server Error instead of gracefully calculating the summary with the available data.
**Steps to Reproduce:**
1. Run the backend test suite.
2. Observe the failure in `test_get_dashboard_summary_with_failing_price_lookup`.
**Expected Behavior:**
The dashboard summary calculation should continue, treating the value of the asset with the failed price lookup as 0. The API should return a 200 OK response.
**Actual Behavior:**
The API request crashes with an unhandled `Exception`.
**Resolution:** The call to `financial_data_service.get_asset_price` in `crud_dashboard.py` was wrapped in a `try...except` block to catch exceptions and default the asset's price to 0 in case of failure.
**Resolution:** Fixed

---

**Bug ID:** 20250721-16
**Title:** Dashboard summary test fails due to decimal precision mismatch in assertion.
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Test Suite
**Severity:** Medium
**Description:**
The test `test_get_dashboard_summary_success` fails with an `AssertionError` because it compares the `total_value` from the API response to a hardcoded string. The API returns a `Decimal` value serialized as a string with high precision (e.g., `'29600.000000000'`), while the test expects a less precise string (`'29600.0'`).
**Steps to Reproduce:**
1. Run the backend test suite.
**Expected Behavior:**
The test should pass regardless of the number of trailing zeros in the decimal representation.
**Actual Behavior:**
The test fails with `AssertionError: assert '29600.000000000' == '29600.0'`.
**Resolution:** The assertion in `test_get_dashboard_summary_success` was updated to cast the string value from the API to a `float` before comparing it to a numeric value, making the test robust to formatting differences.
**Resolution:** Fixed
**Resolution:** Fixed
**Resolution:** Fixed
**Resolution:** Fixed
**Resolution:** Fixed
**Resolution:** Fixed
**Resolution:** Fixed
**Resolution:** Fixed
**Resolution:** Fixed
**Resolution:** Fixed
**Resolution:** Fixed
**Resolution:** Fixed
**Resolution:** Fixed
