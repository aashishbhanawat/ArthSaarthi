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
**Resolution:** Fixed
**Resolution:** Fixed
**Resolution:** Fixed
**Resolution:** Fixed
**Resolution:** Fixed
**Resolution:** Fixed
**Resolution:** Fixed
**Resolution:** Fixed
