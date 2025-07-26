# Bug Reports

This document serves as the official bug log for the Personal Portfolio Management System. All issues discovered during testing must be documented here before work on a fix begins.

---

### Bug Report Template

Copy and paste the template below to file a new bug report.

```markdown
**Bug ID:** YYYY-MM-DD-NN (e.g., 2025-07-17-01)
**Title:**
**Module:** (e.g., User Management, Authentication, Core Backend, UI/Styling)
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

---

**Bug ID:** 2025-07-17-01 
**Title:** Frontend tests fail due to missing @tanstack/react-query dependency. 
**Module:** Core Frontend, Dependencies 
**Reported By:** QA Engineer 
**Date Reported:** 2025-07-17 
**Classification:** Implementation (Frontend) 
**Severity:** Critical 
**Description:** The test suites for UserManagementPage and UserFormModal fail to run because the @tanstack/react-query package, a core dependency for the useUsers custom hooks, is not installed in the project. 
**Steps to Reproduce:**
Navigate to the project root.
Run the command docker-compose run --rm frontend npm test. 
**Expected Behavior:** The Jest test suite should execute all tests for the User Management feature without module resolution errors. Actual Behavior: The test run is interrupted, and two test suites fail with the error: Cannot find module '@tanstack/react-query'. 
**Resolution:** Install the missing dependency by running npm install @tanstack/react-query in the frontend directory and then rebuilding the Docker image.


**Bug ID:** 2025-07-17-02 
**Title:** Frontend tests failing because custom hooks are not correctly mocked. 
**Module:** User Management (Test Suite) 
**Reported By:** QA Engineer 
**Date Reported:** 2025-07-17 
**Classification:** Test Suite 
**Severity:** High 
**Description:** The test suites for UserFormModal.test.tsx and UserManagementPage.test.tsx fail to run with a ReferenceError: useUsersHook is not defined, indicating that the test files are not correctly mocking the custom hooks defined in src/hooks/useUsers.ts. 
**Steps to Reproduce:**
Navigate to the project root.
Run the command docker-compose run --rm frontend npm test. 
**Expected Behavior:** The Jest test suite should execute all tests for the User Management feature without errors. 
**Actual Behavior:** The test run is interrupted, and two test suites fail with the error: ReferenceError: useUsersHook is not defined. 
**Resolution:** The test setup must be corrected to use the directly imported hook functions (useCreateUser, useUpdateUser, useUser, and useDeleteUser) for mock casting, rather than the non-existent useUsersHook object. Additionally, a missing mockUser constant needs to be defined for the 'Edit Mode' tests.

---

**Bug ID:** 2025-07-17-03
**Title:** `UserManagementPage` test suite crashes with TypeError due to incomplete hook mocking.
**Module:** User Management (Test Suite)
**Reported By:** QA Engineer
**Date Reported:** 2025-07-17
**Classification:** Test Suite
**Severity:** High
**Description:**
The test suite for `UserManagementPage.tsx` fails with a `TypeError: Cannot read properties of undefined (reading 'isPending')`. This occurs when a test simulates opening the `UserFormModal`, which internally uses the `useCreateUser` and `useUpdateUser` hooks. These hooks were not mocked completely within the `UserManagementPage.test.tsx` file, causing the error.
**Steps to Reproduce:**
1. Fix previous `ReferenceError`s in the test suite.
2. Run the frontend test suite with `docker-compose run --rm frontend npm test`.
**Expected Behavior:**
The tests for opening the create/edit modals in `UserManagementPage.test.tsx` should run without crashing.
**Actual Behavior:**
The tests crash with a `TypeError`.
**Resolution:**
The test setup for `UserManagementPage.test.tsx` must be updated to provide complete mocks for the `useCreateUser` and `useUpdateUser` hooks, ensuring the returned object includes the `isPending` property.

---

**Bug ID:** 2025-07-17-06
**Title:** `UserManagementPage.test.tsx` test suite fails to run due to syntax error.
**Module:** User Management (Test Suite)
**Reported By:** QA Engineer
**Date Reported:** 2025-07-17
**Classification:** Test Suite
**Severity:** Critical
**Description:**
The test suite for `UserManagementPage` fails during the Jest collection phase with a `TS1005: ',' expected.` syntax error. This is caused by an invalid, duplicated `mockUseCreateUser.mockReturnValue` call that was nested inside another mock definition, breaking the JavaScript syntax.
**Steps to Reproduce:**
1. Run the frontend test suite with `docker-compose run --rm frontend npm test`.
**Expected Behavior:**
The test suite for `UserManagementPage.test.tsx` should compile and run without errors.
**Actual Behavior:**
The test run for this file is aborted with a syntax error during compilation.
**Resolution:**
The duplicated, nested mock call must be removed from `UserManagementPage.test.tsx` to fix the syntax.

---

**Bug ID:** 2025-07-17-07
**Title:** `UserFormModal` tests fail because form labels are not associated with inputs.
**Module:** User Management (Frontend), Accessibility
**Reported By:** QA Engineer
**Date Reported:** 2025-07-17
**Classification:** Implementation (Frontend)
**Severity:** High
**Description:**
All tests for the `UserFormModal.tsx` component fail with a `TestingLibraryElementError`. The tests cannot find form controls using their labels because the `<label>` elements in the component are missing the `htmlFor` attribute to link them to their corresponding `<input>` elements, which also lack `id` attributes. This is an accessibility violation and prevents a primary method of testing forms.
**Steps to Reproduce:**
1. Fix previous test suite errors.
2. Run the frontend test suite with `docker-compose run --rm frontend npm test`.
**Expected Behavior:**
Tests should be able to find form inputs by their label text, and the form should be accessible.
**Actual Behavior:**
Tests fail with `TestingLibraryElementError: Found a label with the text of: ..., however no form control was found associated to that label.`
**Resolution:**
Update `UserFormModal.tsx` to add `htmlFor` and `id` attributes to all corresponding label/input pairs to make the form accessible and testable.

---

**Bug ID:** 2025-07-17-08
**Title:** `UserFormModal` crashes with "Objects are not valid as a React child" error.
**Module:** User Management (Frontend)
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
**Resolution:**
The error handling logic in the `handleSubmit` function of `UserFormModal.tsx` must be corrected to ensure only a string is set in the `error` state.

---

**Bug ID:** 2025-07-17-09
**Title:** `UserFormModal` tests fail due to duplicate component rendering in 'Edit Mode' suite.
**Module:** User Management (Test Suite)
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

---

**Bug ID:** 2025-07-17-10
**Title:** `UserManagementPage` delete confirmation test fails with an ambiguous query.
**Module:** User Management (Test Suite)
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

---

**Bug ID:** 2025-07-17-12
**Title:** Syntax error in `UserFormModal.tsx` breaks multiple test suites.
**Module:** User Management (Frontend)
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

---

**Bug ID:** 2025-07-18-01
**Title:** Admin-only "User Management" link is not displayed on the dashboard.
**Module:** Navigation, Authentication (Frontend)
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
**Resolution:**
The logic was refactored to place the conditional link in the `NavBar` component and fetch user data centrally in the `AuthContext`.

---

**Bug ID:** 2025-07-18-02
**Title:** Navigating to `/admin/users` results in a "No routes matched location" error.
**Module:** Routing (Frontend)
**Reported By:** Developer via Manual E2E Test
**Date Reported:** 2025-07-18
**Classification:** Implementation (Frontend)
**Severity:** Critical
**Description:**
After programmatically adding the link to the User Management page, clicking it results in a blank page and a `No routes matched location "/admin/users"` error in the console. The main application router in `App.tsx` has not been configured to handle this path.
**Steps to Reproduce:**
1. Apply the fix for Bug ID 2025-07-18-01.
2. Log in as an admin.
3. Click the "User Management" link.
**Expected Behavior:**
The application should navigate to the User Management page and render its content.
**Actual Behavior:**
The application renders a blank page, and the routing fails.
**Resolution:**
Create a new `AdminRoute.tsx` protected route component. Update the main router in `App.tsx` to define a nested route for `/admin/users` that is protected by both the standard `ProtectedRoute` and the new `AdminRoute`.

---

**Bug ID:** 2025-07-18-03
**Title:** User Management page crashes with "No QueryClient set" error.
**Module:** Core Frontend, Dependencies
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
**Resolution:**
In `App.tsx`, instantiate a new `QueryClient` and wrap the entire `<Router>` component with a `<QueryClientProvider client={queryClient}>`.

---

**Bug ID:** 2025-07-18-04
**Title:** SQLAlchemy ORM mapping fails due to missing relationship back-references in User model.
**Module:** Core Backend, Database
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
**Resolution:**
Updated the `User` model in `app/models/user.py` to include the `portfolios` and `transactions` relationships with the correct `back_populates` attributes.

---

**Bug ID:** 2025-07-18-05
**Title:** Portfolio & Transaction test suite fails due to use of non-existent 'normal_user_token_headers' fixture.
**Module:** Portfolio Management (Test Suite)
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
**Resolution:**
Created the missing `normal_user_token_headers` fixture in `backend/app/tests/conftest.py`.

---

**Bug ID:** 2025-07-18-03
**Title:** User Management page crashes with "No QueryClient set" error.
**Module:** Core Frontend, Dependencies
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
**Resolution:**
In `App.tsx`, instantiate a new `QueryClient` and wrap the entire `<Router>` component with a `<QueryClientProvider client={queryClient}>`.

---

**Bug ID:** 2025-07-18-04
**Title:** SQLAlchemy ORM mapping fails due to missing relationship back-references in User model.
**Module:** Core Backend, Database
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
**Resolution:**
Updated the `User` model in `app/models/user.py` to include the `portfolios` and `transactions` relationships with the correct `back_populates` attributes.

---

**Bug ID:** 2025-07-18-05
**Title:** Portfolio & Transaction test suite fails due to use of non-existent 'normal_user_token_headers' fixture.
**Module:** Portfolio Management (Test Suite)
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
**Resolution:**
Created the missing `normal_user_token_headers` fixture in `backend/app/tests/conftest.py`.

---

**Bug ID:** 2025-07-18-06
**Title:** Portfolio & Transaction test suite fails due to incorrect usage of `get_auth_headers` fixture.
**Module:** Portfolio Management (Test Suite)
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
**Resolution:**
Updated all calls to `create_random_user` in the test suite to capture the returned password and pass it to the `get_auth_headers` fixture.

---

**Bug ID:** 2025-07-18-07
**Title:** Tests fail due to missing `API_V1_STR` in application settings.
**Module:** Core Backend, Configuration
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
**Resolution:**
Added `API_V1_STR: str = "/api/v1"` to the `Settings` class in `app/core/config.py`.

---

**Bug ID:** 2025-07-18-08
**Title:** Test helpers fail due to unexposed Pydantic schemas.
**Module:** Core Backend, Schemas
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
**Resolution:**
Updated `app/schemas/__init__.py` to import and expose all the new schemas (`Portfolio`, `PortfolioCreate`, `Asset`, `AssetCreate`, `Transaction`, `TransactionCreate`).

---

**Bug ID:** 2025-07-18-09
**Title:** Test suite collection fails with ImportError for non-existent 'UserInDB' schema.
**Module:** Core Backend, Schemas
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
**Resolution:**
Removed the incorrect import of `UserInDB` from `app/schemas/__init__.py`.

---

**Bug ID:** 2025-07-18-10
**Title:** Test suite collection fails with ModuleNotFoundError for 'app.schemas.msg'.
**Module:** Core Backend, Schemas
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
**Resolution:**
Created the missing `app/schemas/msg.py` file with the `Msg` schema.

---

**Bug ID:** 2025-07-18-11
**Title:** New portfolio and asset endpoints are not registered, causing 404 errors.
**Module:** Routing (Backend)
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
**Resolution:**
Fixed by including the new routers in `app/api/v1/api.py`.

---

**Bug ID:** 2025-07-18-12
**Title:** Test helpers fail due to unexposed CRUD modules.
**Module:** Core Backend, CRUD
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
**Resolution:**
Fixed by importing the new CRUD singletons into `app/crud/__init__.py`.

---

**Bug ID:** 2025-07-18-13
**Title:** Test suite collection fails with ModuleNotFoundError for 'app.crud.base'.
**Module:** Core Backend, CRUD
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
**Resolution:**
Fixed by creating the `app/crud/base.py` file.

---

**Bug ID:** 2025-07-18-14
**Title:** Test suite collection fails with ImportError for 'user' from 'crud_user'.
**Module:** Core Backend, CRUD
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
**Resolution:**
Fixed by reverting `crud_user.py` to a functional approach and commenting out the problematic import in `crud/__init__.py`.

---

**Bug ID:** 2025-07-18-15
**Title:** Asset lookup tests fail due to missing financial API configuration.
**Module:** Portfolio Management (Backend), Configuration
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
**Resolution:**
Fixed by adding the required `FINANCIAL_API_KEY` and `FINANCIAL_API_URL` to the `Settings` class.

---

**Bug ID:** 2025-07-18-16
**Title:** Portfolio tests crash due to missing `react-hook-form` dependency.
**Module:** Portfolio Management (Frontend), Dependencies
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
**Resolution:**
Fixed by adding `react-hook-form` to the `dependencies` in `frontend/package.json` and rebuilding the Docker image.

---

**Bug ID:** 2025-07-18-17
**Title:** `LoginForm` tests crash with TypeError due to missing AuthContext import.
**Module:** Authentication (Test Suite)
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
**Resolution:**
Fixed by adding the missing `AuthContext` import in `LoginForm.test.tsx`.

---

**Bug ID:** 2025-07-18-18
**Title:** `AdminRoute` tests fail due to incorrect test setup and assertions.
**Module:** Authentication (Test Suite), Routing (Test Suite)
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
**Resolution:**
Fixed by refactoring the test to use a complete routing structure, which allows redirects to be handled correctly and eliminates console warnings.

---

**Bug ID:** 2025-07-18-19
**Title:** `AddTransactionModal` test fails due to ambiguous query for "Type" label.
**Module:** Portfolio Management (Test Suite)
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
**Resolution:**
Fixed by changing the query to `getByLabelText('Type', { exact: true })` to uniquely identify the correct form element.

---

**Bug ID:** 2025-07-18-20
**Title:** `AddTransactionModal` test fails due to incomplete assertion.
**Module:** Portfolio Management (Test Suite)
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
**Resolution:**
Fixed by adding the missing properties to the `expect.objectContaining` assertion in the test.

---

**Bug ID:** 2025-07-18-21
**Title:** `AddTransactionModal` test fails due to incomplete assertion for default fees.
**Module:** Portfolio Management (Test Suite)
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
**Resolution:**
Fixed by adding the `fees: 0` property to the `expect.objectContaining` assertion in the test.

---

**Bug ID:** 2025-07-18-22
**Title:** `LoginForm` component does not call the correct API service function.
**Module:** Authentication (Frontend)
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
**Resolution:**
Fixed by refactoring `LoginForm.tsx` to call the `api.loginUser` function instead of using `api.post` directly.

---

**Bug ID:** 2025-07-18-23
**Title:** `AddTransactionModal` test fails due to incorrect assertion for `asset_id`.
**Module:** Portfolio Management (Test Suite)
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
**Resolution:**
Fixed by removing the `asset_id: undefined` check from the test assertion.

---

**Bug ID:** 2025-07-19-01
**Title:** Login fails with 404 Not Found due to incorrect API endpoint.
**Module:** Authentication (Frontend), API Integration
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
**Resolution:**
The `handleSubmit` function in `LoginForm.tsx` was updated to use the correct API endpoint: `/api/v1/auth/login`.

---

**Bug ID:** 2025-07-19-02
**Title:** Application-wide UI styling is broken due to missing Tailwind CSS configuration.
**Module:** UI/Styling, Core Frontend
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

---

**Bug ID:** 2025-07-19-03
**Title:** Frontend build fails due to use of deprecated `focus:shadow-outline` class.
**Module:** UI/Styling, Core Frontend
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
**Resolution:**
Replaced `focus:shadow-outline` with modern focus ring utilities (`focus:ring-2 focus:ring-offset-2`) in `index.css` for the `.btn` class and its variants.

---

**Bug ID:** 2025-07-19-04
**Title:** Login page is unstyled and inconsistent with the application theme.
**Module:** UI/Styling, Authentication (Frontend)
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
**Resolution:**
Refactored `AuthPage.tsx` to provide a centered layout with a `.card` container. Refactored `LoginForm.tsx` and `SetupForm.tsx` to use the global form styling classes (`.form-group`, `.form-label`, `.form-input`) and button classes.

---

**Bug ID:** 2025-07-19-05
**Title:** Frontend crashes due to incorrect relative import paths in form components.
**Module:** Core Frontend, Authentication (Frontend)
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
**Resolution:**
Corrected the import paths for `useAuth` in both `LoginForm.tsx` (to `../context/AuthContext`) and `SetupForm.tsx` (to `../../context/AuthContext`).

---

**Bug ID:** 2025-07-19-06
**Title:** Login functionality is broken, preventing user authentication.
**Module:** Authentication (Frontend), API Integration
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
**Resolution:**
The `handleSubmit` function in `LoginForm.tsx` was completely refactored. It now uses the correct API endpoint (`/api/v1/auth/login`), correctly formats the request payload as `x-www-form-urlencoded`, and upon success, calls the `login` function from `AuthContext` with the received token.

---

**Bug ID:** 2025-07-19-07
**Title:** Application crashes after login with "Rendered fewer hooks than expected" error.
**Module:** Core Frontend, Authentication
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
**Resolution:**
Refactored `AuthPage.tsx` to ensure all React hooks are called unconditionally at the top of the component, before any conditional return statements.

---

**Bug ID:** 2025-07-19-08
**Title:** User Management page is unstyled and inconsistent with application theme.
**Module:** UI/Styling, User Management (Frontend)
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
**Resolution:**
Refactored `UserManagementPage.tsx` to style its header. The unstyled `UsersTable.tsx` component was replaced with a fully styled version that uses the application's design system for cards, tables, and buttons.

---

**Bug ID:** 2025-07-19-09
**Title:** User Management page crashes with "isError is not defined" ReferenceError.
**Module:** User Management (Frontend)
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
**Resolution:**
Updated the destructuring assignment for the `useUsers` hook in `UserManagementPage.tsx` to include the `isError` property.

---

**Bug ID:** 2025-07-19-10
**Title:** Navigating away from User Management page logs the user out.
**Module:** User Management (Frontend), Authentication
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
**Resolution:**
The erroneous `useEffect` hook was removed from the `useDeleteUser` custom hook in `src/hooks/useUsers.ts`.

---

**Bug ID:** 2025-07-19-11
**Title:** Portfolios page is unstyled and inconsistent with application theme.
**Module:** UI/Styling, Portfolio Management (Frontend)
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
**Resolution:**
Refactored `PortfolioPage.tsx` to use a flexbox header and apply consistent styling to the title and "Create New Portfolio" button.

---

**Bug ID:** 2025-07-19-12
**Title:** User Management modal is unstyled and uses deprecated classes.
**Module:** UI/Styling, User Management (Frontend)
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
**Resolution:**
The `UserFormModal.tsx` component was refactored to use the new design system classes (`.modal-overlay`, `.modal-content`, `.form-input`, `.btn`, etc.) for all its elements.

---

**Bug ID:** 2025-07-19-13
**Title:** Portfolio Detail page is unstyled and inconsistent with application theme.
**Module:** UI/Styling, Portfolio Management (Frontend)
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
**Resolution:**
Refactored `PortfolioDetailPage.tsx` to use a flexbox header, styled components, and add a "Back to Portfolios" link for better navigation.

---

**Bug ID:** 2025-07-19-14
**Title:** Application does not handle expired authentication tokens, leading to a broken UI state.
**Module:** Authentication, Core Frontend
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
**Resolution:**
Implemented a global Axios response interceptor within the `AuthContext`. This interceptor checks for `403` status codes on API responses and, if detected, calls the `logout` function to clear the session and redirect the user.

---

**Bug ID:** 2025-07-19-15
**Title:** Unstyled browser confirmation used for portfolio deletion.
**Module:** UI/Styling, Portfolio Management (Frontend)
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
**Resolution:**
The `window.confirm` call in `PortfolioList.tsx` was replaced with a new, styled `DeletePortfolioModal` component. State management was added to `PortfolioList.tsx` to control the modal's visibility.

---

**Bug ID:** 2025-07-19-16
**Title:** User deletion confirmation modal is unstyled.
**Module:** UI/Styling, User Management (Frontend)
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
**Resolution:**
The `DeleteConfirmationModal.tsx` component was created/refactored to use the global design system classes for modals and buttons.

---

**Bug ID:** 2025-07-20-01
**Title:** Test suite collection fails due to multiple setup and configuration errors.
**Module:** Core Backend, Configuration, Test Suite
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

---

**Bug ID:** 2025-07-20-02
**Title:** Test suite fails due to multiple inconsistencies between tests and application code.
**Module:** Dashboard (Test Suite), Portfolio Management (Test Suite)
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

---

**Bug ID:** 2025-07-20-03
**Title:** Dashboard logic fails due to missing method and incorrect initialization.
**Module:** Dashboard (Backend)
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
**Resolution:**
Added the missing `get_asset_price` mock method to the `FinancialDataService` class.

---

**Bug ID:** 2025-07-20-04
**Title:** Portfolio and Transaction tests fail due to incorrect API logic and routing.
**Module:** Portfolio Management (Backend), Routing (Backend), Test Suite
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

---

**Bug ID:** 2025-07-20-05
**Title:** Application fails to start due to multiple configuration and import errors.
**Module:** Core Backend, Database, CRUD
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

---

**Bug ID:** 2025-07-20-06
**Title:** Data validation and creation fails due to mismatches between Pydantic schemas and SQLAlchemy models.
**Module:** Core Backend, Schemas, Database
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
**Actual Behavior:**
Tests fail with `TypeError` and `422 Unprocessable Entity` errors.
**Resolution:**
1. Added the `description` column to the `Portfolio` SQLAlchemy model.
2. Added the `description` field to the `Portfolio` Pydantic response schema.
3. Removed the redundant `portfolio_id` field from the `TransactionCreate` schema.

---

**Bug ID:** 2025-07-20-07
**Title:** Transaction creation fails due to missing user ID and import errors.
**Module:** Portfolio Management (Backend), CRUD
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

---

**Bug ID:** 2025-07-20-08
**Title:** Dashboard tests fail due to incorrect assertions and data type mismatches.
**Module:** Dashboard (Test Suite)
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

---

**Bug ID:** 2025-07-20-09
**Title:** Dashboard calculation crashes when financial data service fails.
**Module:** Dashboard (Backend), Error Handling
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
**Resolution:**
The call to `financial_data_service.get_asset_price` in `crud_dashboard.py` was wrapped in a `try...except` block to catch exceptions and default the asset's price to 0 in case of failure.

---

**Bug ID:** 2025-07-20-10
**Title:** Dashboard tests fail with AttributeError due to incorrect CRUD method call in test helper.
**Module:** Dashboard (Test Suite), CRUD
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
**Resolution:**
The `create_test_transaction` function in `app/tests/utils/transaction.py` was updated to call the correct `crud.transaction.create` method, which is inherited from the base CRUD class.

---

**Bug ID:** 2025-07-20-11
**Title:** Portfolio tests fail due to incorrect status code assertions and flawed access control logic.
**Module:** Portfolio Management (Backend), Test Suite
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Test Suite / Implementation (Backend)
**Severity:** High
**Description:**
1.  `test_create_portfolio` fails because it asserts a `200 OK` status code, but the API correctly returns `201 Created`.
2.  `test_read_portfolio_wrong_owner` fails because it asserts a `403 Forbidden` status, but the API incorrectly returns `404 Not Found` due to flawed access control logic that doesn't distinguish between a non-existent resource and an unauthorized one.
**Steps to Reproduce:**
1. Run the backend test suite.
**Expected Behavior:**
Tests should pass. The API should return 403 for unauthorized access to an existing resource and 201 for successful creation.
**Actual Behavior:**
Multiple tests fail with `AssertionError`.
**Resolution:**
1. Updated `test_create_portfolio` to assert for a `201` status code.
2. Updated the `read_portfolio` endpoint in `portfolios.py` to check for ownership and return a 403 if the user is not the owner of an existing portfolio.

---

**Bug ID:** 2025-07-20-12
**Title:** All transaction-related tests fail with 404 Not Found due to incorrect API routing.
**Module:** Routing (Backend), Portfolio Management (Backend)
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

---

**Bug ID:** 2025-07-20-13
**Title:** Test suite collection fails with `AttributeError: module 'app.models' has no attribute 'User'`.
**Module:** Core Backend, API Integration
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
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
**Resolution:**
The import statement in `app/api/v1/endpoints/portfolios.py` was corrected to import `User` directly from `app.models.user`, and the type hint for `current_user` was updated to use the directly imported `User` class.

---

**Bug ID:** 2025-07-20-14
**Title:** Portfolio creation test fails with `KeyError` due to missing `description` in response schema.
**Module:** Portfolio Management (Backend), Schemas
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
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
**Resolution:**
The `description` field was added to the `schemas.PortfolioInDBBase` Pydantic model in `app/schemas/portfolio.py`, ensuring it is included in all derived response schemas.

---

**Bug ID:** 2025-07-20-15
**Title:** Transaction creation tests fail with 422 Unprocessable Entity due to schema mismatch.
**Module:** Portfolio Management (Backend), Schemas
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
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
**Resolution:**
The `portfolio_id` field was removed from the `schemas.TransactionCreate` model in `app/schemas/transaction.py`. The API endpoint and CRUD layer correctly handle associating the transaction with the portfolio using the ID from the URL path.

---

**Bug ID:** 2025-07-20-16
**Title:** Test suite collection fails with `ImportError` for non-existent 'TransactionCreateInternal' schema.
**Module:** Core Backend, Schemas
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
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
**Resolution:**
The `app/schemas/__init__.py` file was corrected to only import schemas that actually exist in their respective modules, removing the reference to the non-existent `TransactionCreateInternal`.

---

**Bug ID:** 2025-07-20-17
**Title:** Test helper `create_test_transaction` fails with `ValidationError` and uses incorrect CRUD method.
**Module:** Portfolio Management (Test Suite)
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Test Suite
**Severity:** High
**Description:**
The test utility function `create_test_transaction` in `app/tests/utils/transaction.py` is implemented incorrectly. It attempts to pass a `portfolio_id` to the `schemas.TransactionCreate` Pydantic model, which does not have this field, leading to a `ValidationError`. Furthermore, it calls the generic `crud.transaction.create` method instead of the correct `crud.transaction.create_with_portfolio` method, which is necessary to associate the transaction with its portfolio.
**Steps to Reproduce:**
1. Fix the `ImportError` from Bug ID 2025-07-20-16.
2. Run a test that uses the `create_test_transaction` helper.
**Expected Behavior:**
The test helper should create a transaction successfully without validation errors.
**Actual Behavior:**
The test helper will crash with a `ValidationError` or the created transaction will not be correctly linked to a portfolio.
**Resolution:**
The `create_test_transaction` helper was refactored to instantiate `schemas.TransactionCreate` without the `portfolio_id` and to call the correct `crud.transaction.create_with_portfolio` method, passing the `portfolio_id` as a separate argument.

---

**Bug ID:** 2025-07-20-18
**Title:** Test suite collection fails with `ImportError` for non-existent 'TransactionCreateInternal' schema in CRUD layer.
**Module:** Core Backend, CRUD
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The test suite fails to run because of an `ImportError` during the test collection phase. The `app/crud/crud_transaction.py` file attempts to import a Pydantic schema named `TransactionCreateInternal` from `app.schemas.transaction`, but this schema is not defined. This was caused by an incomplete implementation of the CRUD layer.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
The test suite should collect and run successfully.
**Actual Behavior:**
Test collection is interrupted with `ImportError: cannot import name 'TransactionCreateInternal' from 'app.schemas.transaction'`.
**Resolution:**
The entire CRUD layer for portfolio management (`base.py`, `crud_asset.py`, `crud_portfolio.py`, `crud_transaction.py`, and `__init__.py`) was created with the correct logic and imports, resolving the `ImportError` and completing the feature.

---

**Bug ID:** 2025-07-20-19
**Title:** Test suite collection fails with `AttributeError` for missing 'DashboardSummary' schema.
**Module:** Dashboard (Backend), Schemas
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
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
**Resolution:**
Created `app/schemas/dashboard.py` to define the `DashboardSummary` model. Updated `app/schemas/__init__.py` to import and expose the new schema.

---

**Bug ID:** 2025-07-20-20
**Title:** Dashboard tests fail with `AttributeError` due to missing `crud_dashboard` module.
**Module:** Dashboard (Backend), CRUD
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-20
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
**Resolution:**
Created `app/crud/crud_dashboard.py` with the `get_dashboard_summary` function and a `CRUDDashboard` class. Updated `app/crud/__init__.py` to expose the new `dashboard` CRUD object.

---

**Bug ID:** 2025-07-21-01
**Title:** `UserManagementPage` error state test fails due to incomplete mock.
**Module:** User Management (Test Suite)
**Reported By:** QA Engineer
**Date Reported:** 2025-07-21
**Classification:** Test Suite
**Severity:** Medium
**Description:**
The test for the error state in `UserManagementPage.test.tsx` is failing. The test correctly mocks the `useUsers` hook to return an error object, but it omits the `isError: true` boolean flag. The component relies on this flag to render the error UI, so the test fails to find the expected error message.
**Steps to Reproduce:**
1. Run the frontend test suite.
**Expected Behavior:**
The test should correctly mock the `isError` state, and the component should render the error message.
**Actual Behavior:**
The test fails with `TestingLibraryElementError: Unable to find an element with the text: An error occurred: Failed to fetch users`.
**Resolution:**
Updated the mock return value in `src/__tests__/pages/Admin/UserManagementPage.test.tsx` to include `isError: true`.

---

**Bug ID:** 2025-07-21-02
**Title:** `UserFormModal` creation test fails due to incorrect payload assertion.
**Module:** User Management (Test Suite)
**Reported By:** QA Engineer
**Date Reported:** 2025-07-21
**Classification:** Test Suite
**Severity:** Medium
**Description:**
The test for creating a new user in `UserFormModal.test.tsx` fails its `toHaveBeenCalledWith` assertion. The component correctly sends `{ "is_admin": false }` in the payload by default, but the test assertion does not expect this property.
**Steps to Reproduce:**
1. Run the frontend test suite.
**Expected Behavior:**
The test assertion should match the actual payload sent by the component.
**Actual Behavior:**
The test fails because the expected object is missing the `is_admin` property.
**Resolution:**
Added `is_admin: false` to the expected payload object in the test assertion in `src/__tests__/components/Admin/UserFormModal.test.tsx`.

---

**Bug ID:** 2025-07-21-04
**Title:** `UsersTable` test fails due to outdated assertions.
**Module:** User Management (Test Suite)
**Reported By:** QA Engineer
**Date Reported:** 2025-07-21
**Classification:** Test Suite
**Severity:** High
**Description:**
The test for `UsersTable.tsx` is failing because its assertions no longer match the rendered component. The component was updated to remove the "Full Name" column and display user roles as badges ("Admin", "User") instead of "Yes/No". The test was not updated to reflect these changes.
**Steps to Reproduce:**
1. Run the frontend test suite.
**Expected Behavior:**
The test should assert for the correct columns and text that are present in the DOM.
**Actual Behavior:**
The test fails with `TestingLibraryElementError: Unable to find an element with the text: Full Name`.
**Resolution:**
Corrected all the failing assertions in `src/__tests__/components/Admin/UsersTable.test.tsx` to match the current component output.

---

**Bug ID:** 2025-07-21-03
**Title:** All `LoginForm` tests crash due to missing `AuthContext` import.
**Module:** Authentication (Test Suite)
**Reported By:** QA Engineer
**Date Reported:** 2025-07-21
**Classification:** Test Suite
**Severity:** Critical
**Description:**
The entire test suite for `LoginForm.tsx` crashes with `TypeError: Cannot read properties of undefined (reading 'Provider')`. The test file's helper function `renderWithContext` attempts to use `<AuthContext.Provider ...>` but never imports `AuthContext` from the context file.
**Steps to Reproduce:**
1. Run the frontend test suite.
**Expected Behavior:**
The `LoginForm` tests should run without crashing.
**Actual Behavior:**
The test suite fails to run and throws a `TypeError`.
**Resolution:**
Added the correct `AuthContext` import to the `LoginForm` test file.

---

**Bug ID:** 2025-07-21-05
**Title:** `DeleteConfirmationModal` tests fail due to outdated text assertions.
**Module:** User Management (Test Suite)
**Reported By:** QA Engineer
**Date Reported:** 2025-07-21
**Classification:** Test Suite
**Severity:** High
**Description:**
The tests for `DeleteConfirmationModal.tsx` are failing because the component's text has been updated. The tests assert for a heading "Confirm Deletion", a button "Delete", and a user's full name. The actual component now renders a heading "Delete User", a button "Confirm Delete", and the user's email.
**Steps to Reproduce:**
1. Run the frontend test suite.
**Expected Behavior:**
Tests should assert for the correct text that is present in the DOM.
**Actual Behavior:**
Tests fail with `TestingLibraryElementError: Unable to find an accessible element...`.
**Resolution:**
Corrected all the failing assertions in `src/__tests__/components/Admin/DeleteConfirmationModal.test.tsx` to match the current component output.

---

**Bug ID:** 2025-07-21-06
**Title:** `UserManagementPage` error state test fails due to incorrect text assertion.
**Module:** User Management (Test Suite)
**Reported By:** QA Engineer
**Date Reported:** 2025-07-21
**Classification:** Test Suite
**Severity:** Medium
**Description:**
The test for the error state in `UserManagementPage.test.tsx` is failing. The component renders the error message as "Error: {message}", but the test is asserting for the text "An error occurred: {message}".
**Steps to Reproduce:**
1. Run the frontend test suite.
**Expected Behavior:**
The test assertion should match the text rendered by the component.
**Actual Behavior:**
The test fails with `TestingLibraryElementError: Unable to find an element with the text: An error occurred: Failed to fetch users`.
**Resolution:**
Updated the assertion in `src/__tests__/pages/Admin/UserManagementPage.test.tsx` to check for `Error: Failed to fetch users`.

---

**Bug ID:** 2025-07-21-18
**Title:** `LoginForm` tests fail due to incorrect button text assertion.
**Module:** Authentication (Test Suite)
**Reported By:** QA Engineer
**Date Reported:** 2025-07-21
**Classification:** Test Suite
**Severity:** Medium
**Description:**
All tests in `LoginForm.test.tsx` fail with `TestingLibraryElementError`. The tests are querying for a button with the accessible name `/login/i`, but the component actually renders a button with the name "Sign in".
**Steps to Reproduce:**
1. Run the frontend test suite.
**Expected Behavior:**
The tests should query for the correct button text and pass.
**Actual Behavior:**
The tests fail because they cannot find the button.
**Resolution:**
Updated all `getByRole` queries in `src/components/LoginForm.test.tsx` to use the correct name, `/sign in/i`.

---

**Bug ID:** 2025-07-21-19
**Title:** `LoginForm` component has incorrect submission logic and error handling.
**Module:** Authentication (Frontend)
**Reported By:** QA Engineer
**Date Reported:** 2025-07-21
**Classification:** Implementation (Frontend)
**Severity:** Critical
**Description:**
The `LoginForm` component is not functioning correctly.
1. It does not call the `api.loginUser` function on form submission, causing the corresponding test assertion to fail.
2. When an API error occurs, it displays a generic "Login failed" message instead of the specific error detail provided by the API response.
**Steps to Reproduce:**
1. Run the frontend test suite.
**Expected Behavior:**
The component should call the correct API service, and on failure, display the specific error message from the API.
**Actual Behavior:**
The API call is not made, and a generic error is shown, causing two tests to fail.
**Resolution:**
The `LoginForm.tsx` component was refactored to use `useState` for controlled inputs and a `handleSubmit` function that correctly calls `api.loginUser`. The new logic includes a `try/catch` block to set the specific error message from the API response into the component's state for rendering.

---

**Bug ID:** 2025-07-21-21
**Title:** Frontend build fails due to missing Dashboard components.
**Module:** Dashboard (Frontend), Core Frontend
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Implementation (Frontend)
**Severity:** Critical
**Description:**
The `DashboardPage.tsx` component attempts to import `SummaryCard` and `TopMoversTable` components, but these files do not exist in the project. This causes the Vite development server to fail with a "Failed to resolve import" error. The components were planned but never created.
**Steps to Reproduce:**
1. Run `docker-compose up --build`.
**Expected Behavior:**
The frontend application should build and start successfully.
**Actual Behavior:**
The Vite server crashes with a module resolution error.
**Resolution:**
Created the missing `SummaryCard.tsx` and `TopMoversTable.tsx` components inside a new `src/components/Dashboard/` directory, as per the feature plan. Updated the import paths in `DashboardPage.tsx` to correctly point to these new files.

---

**Bug ID:** 2025-07-21-22
**Title:** `DashboardPage` component is missing test coverage.
**Module:** Dashboard (Test Suite)
**Reported By:** QA Engineer
**Date Reported:** 2025-07-21
**Classification:** Test Suite
**Severity:** Medium
**Description:**
The `DashboardPage.tsx` component was recently refactored to use the `useDashboardSummary` hook and display live data. However, a corresponding test suite was not created, leaving this critical page without automated test coverage.
**Steps to Reproduce:**
1. Run the frontend test suite: `docker-compose run --rm frontend npm test`.
2. Observe that no tests for `DashboardPage.tsx` are executed.
**Expected Behavior:**
The `DashboardPage` should have a dedicated test suite that verifies its loading, error, and success states.
**Actual Behavior:**
The component has no test coverage.
**Resolution:**
Created a new test suite `frontend/src/__tests__/pages/DashboardPage.test.tsx`. The new tests mock the `useDashboardSummary` hook and verify that the component correctly renders the loading state, error messages, and successfully displays formatted data in the `SummaryCard` and `TopMoversTable` components.

---

**Bug ID:** 2025-07-21-23
**Title:** `DashboardPage` incorrectly formats negative currency values.
**Module:** Dashboard (Frontend), UI/Styling
**Reported By:** QA Engineer
**Date Reported:** 2025-07-21
**Classification:** Implementation (Frontend)
**Severity:** Medium
**Description:**
The `formatCurrency` helper function in `DashboardPage.tsx` incorrectly formats negative currency values by placing the currency symbol before the minus sign (e.g., `$-50.00` instead of `-$50.00`). This was caught by the test suite.
**Steps to Reproduce:**
1. Run the frontend test suite.
**Expected Behavior:**
Negative currency values should be formatted with the minus sign first (e.g., `-$50.00`). The test should pass.
**Actual Behavior:**
The test fails because it cannot find the correctly formatted negative currency string.
**Resolution:**
The `formatCurrency` function in `DashboardPage.tsx` was updated to correctly handle negative numbers. The corresponding test assertion in `DashboardPage.test.tsx` was also updated to match the correct format.

---

**Bug ID:** 2025-07-21-24
**Title:** Backend crashes with 500 Internal Server Error when fetching portfolios due to schema inconsistencies.
**Module:** Core Backend, Schemas
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
When the frontend requests the list of portfolios from `GET /api/v1/portfolios/`, the backend crashes. This is caused by a Pydantic serialization error. The `Portfolio` model has nested relationships (transactions, which in turn have assets), but the Pydantic schemas used for the response are either missing the necessary `from_attributes=True` configuration or are inconsistent with each other, causing a failure during nested data serialization.
**Steps to Reproduce:**
1. Log in to the application.
2. Navigate to the `/portfolios` page.
**Expected Behavior:**
The API should return a list of portfolios with a `200 OK` status.
**Actual Behavior:**
The API returns a `500 Internal Server Error`.
**Resolution:**
Replaced the schemas for `asset`, `transaction`, and `portfolio` with new, consistent versions that correctly handle nested relationships and use `from_attributes=True` in their `model_config`.

---

**Bug ID:** 2025-07-21-25
**Title:** Dashboard API requests fail due to incorrect URL.
**Module:** Dashboard (Frontend), API Integration
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Implementation (Frontend)
**Severity:** High
**Description:**
The `getDashboardSummary` function in `dashboardApi.ts` makes a request to `/dashboard/summary` instead of the correct, prefixed path `/api/v1/dashboard/summary`. This causes the request to bypass the Vite proxy, which results in the `index.html` file being served instead of the API response.
**Steps to Reproduce:**
1. Load the Dashboard page and observe network requests.
**Expected Behavior:**
The frontend should make a request to `/api/v1/dashboard/summary` and receive JSON data.
**Actual Behavior:**
The request goes to `/dashboard/summary` and receives an HTML document.
**Resolution:**
Corrected the URL in `frontend/src/services/dashboardApi.ts` to include the `/api/v1` prefix.

---

**Bug ID:** 2025-07-21-30
**Title:** Backend crashes on startup due to inconsistent Pydantic schemas.
**Module:** Core Backend, Schemas
**Reported By:** User via E2E Test
**Date Reported:** 2025-07-21
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The application is unusable as even the login page fails to load. The initial API call to `/api/v1/auth/status` returns a 500 Internal Server Error. This is caused by a fatal inconsistency between the Pydantic schemas. The `schemas/portfolio.py` file was updated to a new structure that expects a corresponding new structure for `schemas.Transaction`, but the `schemas/transaction.py` file still contains the old, incompatible schema. This conflict prevents the application's data models from being built correctly, leading to a crash on any database-accessing API call.
**Steps to Reproduce:**
1. Navigate to the `/login` page.
**Expected Behavior:**
The login form should be displayed.
**Actual Behavior:**
The page displays "Error: Failed to check setup status." and the browser console shows a 500 error for the `/api/v1/auth/status` request.
**Resolution:**
Replaced the outdated content of `backend/app/schemas/transaction.py` with the modern, consistent schema that aligns with the `portfolio.py` and `asset.py` schemas.

---

**Bug ID:** 2025-07-21-31
**Title:** Backend crashes on startup with ImportError for non-existent 'AssetUpdate' schema.
**Module:** Core Backend, Schemas
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The backend application fails to start, causing the frontend to fail with a connection refused error. The traceback shows a fatal `ImportError` because `app/schemas/__init__.py` attempts to import an `AssetUpdate` schema from `app/schemas/asset.py`, but this schema is not defined.
**Steps to Reproduce:**
1. Run `docker-compose up --build`.
**Expected Behavior:**
The backend service should start successfully.
**Actual Behavior:**
The backend container crashes immediately with an `ImportError`.
**Resolution:**
Corrected `app/schemas/__init__.py` to remove the import for the non-existent `AssetUpdate` schema. Also proactively fixed a related bug in `app/schemas/transaction.py` where `asset_id` was incorrectly marked as required.

---

**Bug ID:** 2025-07-21-32
**Title:** Backend crashes on startup with ImportError in CRUD layer.
**Module:** Core Backend, CRUD
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The backend application fails to start due to a fatal `ImportError`. The file `app/crud/crud_asset.py` attempts to import a non-existent Pydantic schema named `AssetUpdate`. This prevents the application from starting and causes the frontend to fail with a connection refused error.
**Steps to Reproduce:**
1. Run `docker-compose up --build`.
**Expected Behavior:**
The backend service should start successfully.
**Actual Behavior:**
The backend container crashes immediately with an `ImportError`.
**Resolution:**
Corrected `app/crud/crud_asset.py` to remove the import for the non-existent `AssetUpdate` schema and adjusted the `CRUDBase` type hint to use `AssetCreate` as a placeholder for the update schema, allowing the application to start.

---

**Bug ID:** 2025-07-21-33
**Title:** Asset CRUD layer uses a placeholder for its update schema.
**Module:** Core Backend, CRUD
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Implementation (Backend)
**Severity:** Medium
**Description:**
The `CRUDAsset` class in `crud_asset.py` uses `AssetCreate` as a placeholder for its `UpdateSchemaType`. While this was a temporary fix for a previous startup crash, it is not semantically correct and could lead to bugs if asset update functionality is ever implemented. The proper `AssetUpdate` schema was never created.
**Steps to Reproduce:**
1. Review the code in `app/crud/crud_asset.py`.
**Expected Behavior:**
The `CRUDAsset` class should be typed with a dedicated `AssetUpdate` schema.
**Actual Behavior:**
The class uses the `AssetCreate` schema as a placeholder for updates.
**Resolution:**
Created a dedicated `AssetUpdate` schema with optional fields in `app/schemas/asset.py`. Updated the `CRUDAsset` class in `app/crud/crud_asset.py` to use this new schema. Exposed the new schema in `app/schemas/__init__.py`.

---

**Bug ID:** 2025-07-21-34
**Title:** Backend crashes on startup with ImportError for non-existent 'PortfolioUpdate' schema.
**Module:** Core Backend, CRUD
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The backend application fails to start due to a fatal `ImportError`. The file `app/crud/crud_portfolio.py` attempts to import a non-existent Pydantic schema named `PortfolioUpdate`. This prevents the application from starting and causes the frontend to fail with a connection refused error.
**Steps to Reproduce:**
1. Run `docker-compose up --build`.
**Expected Behavior:**
The backend service should start successfully.
**Actual Behavior:**
The backend container crashes immediately with an `ImportError`.
**Resolution:**
Created the missing `PortfolioUpdate` schema in `app/schemas/portfolio.py` and exposed it in `app/schemas/__init__.py`.

---

**Bug ID:** 2025-07-21-35
**Title:** Backend crashes on startup with ImportError for non-existent 'TransactionUpdate' schema.
**Module:** Core Backend, CRUD
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The backend application fails to start due to a fatal `ImportError`. The file `app/crud/crud_transaction.py` attempts to import a non-existent Pydantic schema named `TransactionUpdate`. This prevents the application from starting and causes the frontend to fail with a connection refused error.
**Steps to Reproduce:**
1. Run `docker-compose up --build`.
**Expected Behavior:**
The backend service should start successfully.
**Actual Behavior:**
The backend container crashes immediately with an `ImportError`.
**Resolution:**
Created the missing `TransactionUpdate` schema in `app/schemas/transaction.py` and exposed it in `app/schemas/__init__.py`.

---

**Bug ID:** 2025-07-21-36
**Title:** Transaction creation test fails due to data type mismatch in assertion.
**Module:** Portfolio Management (Test Suite)
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Test Suite
**Severity:** High
**Description:**
The test `test_create_transaction_with_new_asset` fails because it compares the `quantity` value from the API response, which is a string representation of a `Decimal` (e.g., `'10.00000000'`), directly with a float (`10.0`). This causes an `AssertionError`.
**Steps to Reproduce:**
1. Run `docker-compose run --rm test`.
**Expected Behavior:**
The test should correctly handle the data type from the API response and pass.
**Actual Behavior:**
The test fails with `AssertionError: assert '10.00000000' == 10.0`.
**Resolution:**
Updated the assertion in `app/tests/api/v1/test_portfolios_transactions.py` to cast the string value from the response to a `float` before comparison.

---

**Bug ID:** 2025-07-21-37
**Title:** Transaction creation test for conflicting asset info returns incorrect status code.
**Module:** Portfolio Management (Test Suite)
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Test Suite
**Severity:** Medium
**Description:**
The test `test_create_transaction_conflicting_asset_info` in `test_portfolios_transactions.py` fails because it expects status code 422 (Unprocessable Entity) but receives 201 (Created). The backend logic currently ignores the conflicting asset information and proceeds with creation, which is not the intended behavior for this test case.
**Steps to Reproduce:**
1. Run the backend test suite.
**Expected Behavior:**
The test should expect status code 201, or the backend logic should be updated to return 422.
**Actual Behavior:**
The test fails with an `AssertionError: assert 201 == 422`.
**Resolution:**
Updated `test_create_transaction_conflicting_asset_info` to assert correctly that the status code is 201, aligning the test with the current backend behavior.

---

**Bug ID:** 2025-07-21-38
**Title:** Project documentation provides ambiguous `docker-compose` commands.
**Module:** Documentation, Build/Deployment
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Documentation
**Severity:** Medium
**Description:**
The `README.md` and `handoff_document.md` instruct the user to run `docker-compose up --build` to start the application. This is ambiguous because running the command without specifying services will also attempt to start the `test` service. The `test` service is designed for a one-off test run and will exit, causing `docker-compose up` to report an error (e.g., "unhealthy" or "exited with code..."). This can confuse developers trying to run the project.
**Steps to Reproduce:**
1. Follow the instructions in the README and run `docker-compose up --build` from the project root.
**Expected Behavior:**
The application services (`db`, `backend`, `frontend`) should start and continue running without error.
**Actual Behavior:**
The command fails with an error like `ERROR: for test Container ... is unhealthy.` because it also tries to run the short-lived test container.
**Resolution:**
Updated `README.md` and `handoff_document.md` to specify the exact services to start: `docker-compose up --build db backend frontend`.

---

**Bug ID:** 2025-07-21-39
**Title:** Docker Compose commands fail with "unhealthy" container error.
**Module:** Documentation, Build/Deployment
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Documentation
**Severity:** Medium
**Description:**
When a `docker-compose` command is interrupted or fails (e.g., by trying to run the short-lived `test` service with `up`), it can leave behind stopped containers. Subsequent commands like `docker-compose up` or `docker-compose run` then fail with a confusing `ERROR: for ... Container ... is unhealthy` message because they are trying to attach to the stale, stopped container.
**Steps to Reproduce:**
1. Run `docker-compose up` with a service that exits.
2. Attempt to run `docker-compose up` or `docker-compose run` again.
**Expected Behavior:**
The documentation should provide a clear way to recover from this common Docker state issue.
**Actual Behavior:**
The user is stuck with a non-functional environment and no clear instructions on how to fix it.
**Resolution:**
Added a new section to `docs/troubleshooting.md` explaining the "unhealthy container" error and instructing the user to run `docker-compose down` to perform a clean reset of the Docker environment.

---

**Bug ID:** 2025-07-21-40
**Title:** Backend crashes with 500 error on Dashboard and Portfolio pages due to data type mismatch.
**Module:** Core Backend, Schemas, Database
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
After a user logs in, both the Dashboard and Portfolios pages fail to load. The browser console shows that the API requests to `/api/v1/dashboard/summary` and `/api/v1/portfolios/` are failing with a `500 Internal Server Error`. This is caused by a data type mismatch in the `Transaction` schema. The SQLAlchemy model uses the `Numeric` type (which maps to `Decimal`), but the Pydantic schemas use `float`, causing a serialization error when the backend tries to prepare the response.
**Steps to Reproduce:**
1. Log in to the application.
2. Observe the network requests in the browser's developer tools.
**Expected Behavior:**
The Dashboard and Portfolios pages should load their data successfully.
**Actual Behavior:**
The pages show an error state, and the API requests fail with a 500 status code.
**Resolution:**
Updated `app/schemas/transaction.py` to use Python's `Decimal` type for all currency-related fields (`quantity`, `price_per_unit`, `fees`) to match the database model. Also corrected `app/schemas/__init__.py` to properly export the `TransactionUpdate` schema.

---

**Bug ID:** 2025-07-21-41
**Title:** Application crashes due to database schema being out of sync with application models.
**Module:** Architecture, Database, Build/Deployment
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Architecture / Implementation (Backend)
**Severity:** Critical
**Description:**
The application crashes with a `sqlalchemy.exc.ProgrammingError` because the SQLAlchemy models (e.g., the `Portfolio` model with a `description` column) have been updated, but the actual database schema has not. The application tries to select a column that does not exist in the database table. This is because the project lacks a database migration tool like Alembic.
**Steps to Reproduce:**
1. Update a SQLAlchemy model in the code.
2. Restart the application without resetting the database.
**Expected Behavior:**
The application should run without database errors.
**Actual Behavior:**
The backend crashes with a `ProgrammingError` when it tries to query a table with a mismatched schema.
**Resolution:**
For development, the fix is to completely reset the database by removing the Docker volume (`docker-compose down -v`). A proper migration tool should be implemented as a long-term solution.

---

**Bug ID:** 2025-07-21-42
**Title:** Confusing user experience after database reset.
**Module:** Documentation, User Experience
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Documentation / User Experience
**Severity:** Low
**Description:**
After a developer runs `docker-compose down -v` to reset the database, the application correctly requires a new initial setup. However, if the developer's browser has a stale authentication token in `localStorage`, they might be presented with the login form and try to use their old, now-deleted credentials, leading to a confusing "Incorrect email or password" error. The workflow is not immediately obvious.
**Steps to Reproduce:**
1. Log in to the application.
2. Run `docker-compose down -v`.
3. Run `docker-compose up --build db backend frontend`.
4. Refresh the application in the browser.
**Expected Behavior:**
The developer should have a clear understanding that they need to perform the initial setup again with a new user account.
**Actual Behavior:**
The developer may be confused by the login failure, not realizing their old account is gone.
**Resolution:**
Added a note to the `README.md` file in the "Running the Project" section and a dedicated section in `docs/troubleshooting.md` to clarify the expected behavior after resetting the database.

---

**Bug ID:** 2025-07-21-43
**Title:** AuthPage incorrectly renders LoginForm instead of SetupForm on a fresh installation.
**Module:** Authentication (Frontend)
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Implementation (Frontend)
**Severity:** Critical
**Description:**
When the database is empty, the `/api/v1/auth/status` endpoint correctly indicates that setup is needed. However, the `AuthPage.tsx` component fails to interpret this response correctly and defaults to showing the `LoginForm`. This is due to a state management bug where the `setupNeeded` flag is not being updated properly after the API call. This blocks the initial setup of the application.
**Steps to Reproduce:**
1. Run `docker-compose down -v` to reset the database.
2. Run `docker-compose up --build db backend frontend`.
3. Navigate to the `/login` route.
**Expected Behavior:**
The "Initial Setup" form should be displayed.
**Actual Behavior:**
The "Login" form is displayed, making it impossible to create the first user.
**Resolution:**
Created the missing `AuthPage.tsx` and `SetupForm.tsx` components with the correct logic to check the setup status and conditionally render the appropriate form.

---

**Bug ID:** 2025-07-21-44
**Title:** Frontend build fails due to incorrect import paths in AuthPage.
**Module:** Authentication (Frontend), Core Frontend
**Reported By:** User via E2E Test
**Date Reported:** 2025-07-21
**Classification:** Implementation (Frontend)
**Severity:** Critical
**Description:**
The application fails to start because the Vite development server cannot resolve the import paths for `LoginForm` and `SetupForm` within `AuthPage.tsx`. The components reside in `src/components/auth/`, but the `AuthPage` is attempting to import them from an incorrect location, causing a "Failed to resolve import" error.
**Steps to Reproduce:**
1. Run `docker-compose up --build db backend frontend`.
**Expected Behavior:**
The frontend application should build and start successfully.
**Actual Behavior:**
The Vite server crashes with a module resolution error.
**Resolution:**
The import paths in `AuthPage.tsx` were corrected to point to the `auth` subdirectory: `../components/auth/LoginForm` and `../components/auth/SetupForm`.

---

**Bug ID:** 2025-07-21-46
**Title:** Duplicate `LoginForm.tsx` component causes incorrect behavior and maintenance issues.
**Module:** Authentication (Frontend), Code Quality
**Reported By:** User
**Date Reported:** 2025-07-21
**Classification:** Implementation (Frontend)
**Severity:** High
**Description:**
There are two `LoginForm.tsx` files: one in `src/components/` and one in `src/components/auth/`. The `AuthPage` correctly imports from the `/auth` subdirectory, but this file contains an outdated implementation with incorrect API endpoint URLs. The file in `src/components/` has the correct, modern implementation but is not being used. This leads to confusing behavior and makes the code hard to maintain.
**Steps to Reproduce:**
1. Attempt to log in to the application.
**Expected Behavior:**
The login should use the correct, up-to-date component logic.
**Actual Behavior:**
The login fails because the application is using an outdated version of the `LoginForm` component.
**Resolution:**
The correct code from `src/components/LoginForm.tsx` was moved to `src/components/auth/LoginForm.tsx`, overwriting the old implementation. The now-redundant file at `src/components/LoginForm.tsx` was deleted. The associated test file was also moved to the `auth` subdirectory to maintain project structure.

---

**Bug ID:** 2025-07-21-47
**Title:** AuthPage fails to check setup status due to incorrect API response handling.
**Module:** Authentication (Frontend), API Integration
**Reported By:** User via E2E Test
**Date Reported:** 2025-07-21
**Classification:** Implementation (Frontend)
**Severity:** Critical
**Description:**
The `AuthPage.tsx` component incorrectly destructures the `data` property from the result of the `api.getAuthStatus()` function. The API service functions in this project are designed to return the data object directly, not the full Axios response. This causes a `TypeError` when the component tries to access `data.setup_needed`, which triggers the `catch` block and displays a generic error message, preventing users from setting up or logging into the application.
**Steps to Reproduce:**
1. Navigate to the `/login` page.
**Expected Behavior:**
The page should correctly determine if setup is needed and render the appropriate form.
**Actual Behavior:**
The page displays the error "Failed to check setup status."
**Resolution:**
Modified `AuthPage.tsx` to correctly handle the response from `api.getAuthStatus()` by assigning the result directly to a variable instead of destructuring a `data` property from it.

---

**Bug ID:** 2025-07-21-48
**Title:** Initial admin setup fails because `SetupForm` calls incorrect function.
**Module:** Authentication (Frontend), Code Quality
**Reported By:** User via E2E Test
**Date Reported:** 2025-07-21
**Classification:** Implementation (Frontend)
**Severity:** Critical
**Description:**
There are two `SetupForm.tsx` files. The one being used by the application (`src/components/auth/SetupForm.tsx`) has an incorrect implementation. It is missing the `fullName` field and calls a placeholder `register` function from `AuthContext` instead of the required `api.setupAdminUser` function. This prevents the initial admin user from being created, blocking all further use of the application.
**Steps to Reproduce:**
1. Start with a fresh database.
2. Navigate to the setup page and attempt to create an admin user.
**Expected Behavior:**
The admin user should be created, and the user should be taken to the login form.
**Actual Behavior:**
The form submission does nothing, and the user remains on the setup page.
**Resolution:**
The correct code from `src/components/SetupForm.tsx` was moved to `src/components/auth/SetupForm.tsx`, overwriting the old implementation. The now-redundant file at `src/components/SetupForm.tsx` was deleted.

---

**Bug ID:** 2025-07-21-49
**Title:** Initial admin setup fails due to function name mismatch in API service.
**Module:** Authentication (Frontend), API Integration
**Reported By:** User via E2E Test
**Date Reported:** 2025-07-21
**Classification:** Implementation (Frontend)
**Severity:** Critical
**Description:**
When submitting the initial setup form, the request fails with a generic "unexpected error" message. This is because the `SetupForm.tsx` component calls `api.setupAdminUser()`, but the corresponding function exported from `src/services/api.ts` is named `setupAdmin()`. This naming mismatch causes the API call to fail.
**Steps to Reproduce:**
1. Start with a fresh database.
2. Navigate to the setup page and attempt to create an admin user.
**Expected Behavior:**
The admin user should be created successfully.
**Actual Behavior:**
The form displays an "unexpected error" message, and the user cannot be created.
**Resolution:**
Renamed the `setupAdmin` function in `src/services/api.ts` to `setupAdminUser` to match the function call in the `SetupForm` component.

---

**Bug ID:** 2025-07-21-50
**Title:** User is stuck on the login page after a successful login.
**Module:** Authentication (Frontend), Routing
**Reported By:** User via E2E Test
**Date Reported:** 2025-07-21
**Classification:** Implementation (Frontend)
**Severity:** Critical
**Description:**
After a user successfully creates an account and then logs in, they are not redirected to the dashboard. The `AuthPage.tsx` component does not have any logic to handle the post-login state. It continues to render the login form even after the `AuthContext` has been updated with a valid token, effectively trapping the user on the login page.
**Steps to Reproduce:**
1. Start with a fresh database and complete the initial setup.
2. On the login form, enter the newly created credentials and log in.
**Expected Behavior:**
The user should be redirected to the `/dashboard` route.
**Actual Behavior:**
The user remains on the `/login` page, looking at the login form.
**Resolution:**
Added a `useEffect` hook to `AuthPage.tsx`. This hook uses the `useAuth` context to monitor the `token` state. If a token exists, it programmatically navigates the user to the `/dashboard` route.

---

**Bug ID:** 2025-07-21-51
**Title:** Unable to add new transaction due to incorrect API endpoint.
**Module:** Portfolio Management (Frontend), API Integration
**Reported By:** User via E2E Test
**Date Reported:** 2025-07-21
**Classification:** Implementation (Frontend)
**Severity:** Critical
**Description:**
When a user attempts to add a new transaction, the request fails with a `404 Not Found` error. The frontend is making a `POST` request to `/api/v1/transactions/`, but the correct endpoint is nested under a portfolio: `/api/v1/portfolios/{portfolio_id}/transactions/`. This is caused by a missing or incomplete `portfolioApi.ts` service file.
**Steps to Reproduce:**
1. Log in and create a portfolio.
2. Navigate to the portfolio detail page and attempt to add a transaction.
**Expected Behavior:**
The transaction should be created successfully.
**Actual Behavior:**
The API request fails with a 404 error, and the transaction is not added.
**Resolution:**
Created the missing `frontend/src/services/portfolioApi.ts` file and implemented all the necessary functions (`getPortfolios`, `getPortfolio`, `createPortfolio`, `deletePortfolio`, `lookupAsset`, `createTransaction`) with the correct API endpoint URLs.

---

**Bug ID:** 2025-07-21-52
**Title:** Asset lookup endpoint is broken, failing to check local DB and crashing.
**Module:** Portfolio Management (Backend), API Integration
**Reported By:** User via E2E Test
**Date Reported:** 2025-07-21
**Classification:** Implementation (Backend)
**Severity:** High
**Description:**
The `GET /api/v1/assets/lookup/{ticker}` endpoint is implemented incorrectly. It does not check the local database for an existing asset before trying to call an external service. Furthermore, it attempts to call a non-existent method (`lookup_ticker`) on the `FinancialDataService`, causing a 500 Internal Server Error. This prevents users from adding transactions for locally existing assets.
**Steps to Reproduce:**
1. Create a transaction with a new, previously unknown asset ticker.
2. Attempt to create a second transaction using the same ticker.
**Expected Behavior:**
The asset lookup should find the locally stored asset and return its details with a 200 OK status.
**Actual Behavior:**
The API request crashes with a 500 Internal Server Error or fails with a 404 Not Found.
**Resolution:**
Re-implemented the `lookup_ticker_symbol` function in `backend/app/api/v1/endpoints/assets.py`. The new logic first queries the local database using `crud.asset.get_by_ticker`. If the asset is not found locally, it then proceeds to call the correct `financial_service.get_asset_details` method.

---

**Bug ID:** 2025-07-21-54
**Title:** Backend crashes on startup with ImportError for 'deps' module.
**Module:** Core Backend, API Integration
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The backend application fails to start due to a fatal `ImportError`. The file `app/api/v1/endpoints/assets.py` attempts to import the `deps` module from `app.api` instead of the correct path `app.api.v1`. This incorrect import path prevents the application from starting.
**Steps to Reproduce:**
1. Run `docker-compose up --build`.
**Expected Behavior:**
The backend service should start successfully.
**Actual Behavior:**
The backend container crashes immediately with an `ImportError`.
**Resolution:**
Corrected the import path in `app/api/v1/endpoints/assets.py` to `from app.api.v1 import deps`.

---

**Bug ID:** 2025-07-21-55
**Title:** Backend crashes on startup due to incorrect dependency function name.
**Module:** Core Backend, API Integration
**Reported By:** User
**Date Reported:** 2025-07-21
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The `assets.py` endpoint attempts to import and use a dependency named `get_current_active_user`, which does not exist. The correct function name is `get_current_user`. This causes a fatal `ImportError` on application startup.
**Steps to Reproduce:**
1. Run `docker-compose up --build`.
**Expected Behavior:**
The backend service should start successfully.
**Actual Behavior:**
The backend container crashes immediately with an `ImportError`.
**Resolution:**
Corrected the import and usage in `app/api/v1/endpoints/assets.py` to use `get_current_user`.

---

**Bug ID:** 2025-07-21-57
**Title:** `LoginForm.test.tsx` fails to run due to incorrect module path.
**Module:** Authentication (Test Suite)
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-21
**Classification:** Test Suite
**Severity:** Critical
**Description:**
The test suite for `LoginForm.tsx` fails to run because it uses an incorrect relative path (`../services/api`) to mock the API service module. The test file is located in `src/components/auth/`, so the correct path should be `../../services/api`.
**Steps to Reproduce:**
1. Run `docker-compose run --rm frontend npm test`.
**Expected Behavior:**
The test suite for `LoginForm` should run without module resolution errors.
**Actual Behavior:**
The test suite fails with `Cannot find module '../services/api' from 'src/components/auth/LoginForm.test.tsx'`.
**Resolution:**
Corrected the mock path in `src/__tests__/components/auth/LoginForm.test.tsx` to `../../services/api`.

**Resolution:**
Renamed the `setupAdmin` function in `src/services/api.ts` to `setupAdminUser` to match the function call in the `SetupForm` component.

---

**Bug ID:** 2025-07-23-01
**Title:** Backend test suite fails to run due to missing singleton instance in FinancialDataService.
**Module:** Core Backend, Services
**Reported By:** QA Engineer
**Date Reported:** 2025-07-23
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The entire backend test suite fails during the collection phase with a fatal `ImportError`. The `crud_dashboard.py` module, which is imported by the API layer, attempts to import a singleton instance named `financial_data_service` from `app.services.financial_data_service`. However, this instance is not defined in the service file, which only contains the class definition. This prevents the application from initializing correctly and blocks all backend testing.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
The test suite should collect and run successfully.
**Actual Behavior:**
The test collection is interrupted with the error: `ImportError: cannot import name 'financial_data_service' from 'app.services.financial_data_service'`.
**Resolution:**
Instantiate the `FinancialDataService` class at the end of `app/services/financial_data_service.py` to create the required `financial_data_service` singleton instance, making it available for import by other modules.

**Resolution:**
Renamed the `setupAdmin` function in `src/services/api.ts` to `setupAdminUser` to match the function call in the `SetupForm` component.

---

**Bug ID:** 2025-07-23-02
**Title:** Backend test suite fails to run due to missing singleton instance in FinancialDataService.
**Module:** Core Backend, Services
**Reported By:** QA Engineer
**Date Reported:** 2025-07-23
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The entire backend test suite fails during the collection phase with a fatal `ImportError`. The `crud_dashboard.py` module, which is imported by the API layer, attempts to import a singleton instance named `financial_data_service` from `app.services.financial_data_service`. However, this instance is not defined in the service file, which only contains the class definition. This prevents the application from initializing correctly and blocks all backend testing.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
The test suite should collect and run successfully.
**Actual Behavior:**
The test collection is interrupted with the error: `ImportError: cannot import name 'financial_data_service' from 'app.services.financial_data_service'`.
**Resolution:**
Instantiate the `FinancialDataService` class at the end of `app/services/financial_data_service.py` to create the required `financial_data_service` singleton instance, making it available for import by other modules.

---

**Bug ID:** 2025-07-23-03
**Title:** Test suite collection fails with `AttributeError: module 'app.models' has no attribute 'User'`.
**Module:** Core Backend, CRUD
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-23
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The test suite fails to run because of an `AttributeError` during test collection. The `crud_dashboard.py` module uses an incorrect type hint `models.User` for function parameters. The `User` model is not directly available under the `app.models` namespace, which causes a fatal error during application startup.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
The test suite should collect and run successfully.
**Actual Behavior:**
Test collection is interrupted with `AttributeError: module 'app.models' has no attribute 'User'`.
**Resolution:**
Correct the import in `app/crud/crud_dashboard.py` to `from app.models.user import User` and update the type hints accordingly.

---

**Bug ID:** 2025-07-23-04
**Title:** Test suite collection fails with `AttributeError` in `dashboard.py`.
**Module:** Dashboard (Backend), API Integration
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-23
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The test suite fails to run because of an `AttributeError` during test collection. The `dashboard.py` endpoint file uses an incorrect type hint `models.User` for the `current_user` dependency. The `User` model is not directly available under the `app.models` namespace, which causes a fatal error during application startup.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
The test suite should collect and run successfully.
**Actual Behavior:**
Test collection is interrupted with `AttributeError: module 'app.models' has no attribute 'User'`.
**Resolution:**
Correct the import in `app/api/v1/endpoints/dashboard.py` to `from app.models.user import User` and update the type hints accordingly.

---

**Bug ID:** 2025-07-23-05
**Title:** Dashboard summary tests fail due to schema mismatch and unhandled exceptions.
**Module:** Dashboard (Backend)
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-23
**Classification:** Implementation (Backend) / Test Suite
**Severity:** High
**Description:**
Three tests for the `/dashboard/summary` endpoint are failing.
1. Tests expecting an `asset_allocation` field fail with a `KeyError` because the `DashboardSummary` Pydantic schema is missing this field, causing FastAPI to strip it from the response.
2. The test for handling financial service failures crashes with an unhandled `Exception` because the price lookup in `crud_dashboard.py` is not wrapped in a `try...except` block.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
All dashboard tests should pass. The summary endpoint should always include `asset_allocation` and should handle external service failures gracefully.
**Actual Behavior:**
Tests fail with `KeyError` and unhandled `Exception`.
**Resolution:**
1. Add `asset_allocation: List[AssetAllocation]` to the `DashboardSummary` schema in `app/schemas/dashboard.py`.
2. Wrap the `get_asset_price` call in `app/crud/crud_dashboard.py` in a `try...except` block to handle potential failures.

---

**Bug ID:** 2025-07-23-06
**Title:** Dashboard hook test suite fails to run due to incorrect file extension.
**Module:** Dashboard (Test Suite)
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-23
**Classification:** Test Suite
**Severity:** High
**Description:**
The test suite for the new dashboard hooks (`useDashboard.test.ts`) fails to run with multiple TypeScript syntax errors. The file contains JSX for the `QueryClientProvider` wrapper but has a `.ts` extension instead of `.tsx`. This causes the TypeScript compiler to fail, preventing the entire suite from being tested.
**Steps to Reproduce:**
1. Run the frontend test suite: `docker-compose run --rm frontend npm test`.
**Expected Behavior:**
The test suite for the dashboard hooks should run successfully.
**Actual Behavior:**
The test suite fails to compile with syntax errors.
**Resolution:**
The old test file `frontend/src/__tests__/hooks/useDashboard.test.ts` was deleted, and its content was moved to a new file with the correct `.tsx` extension: `frontend/src/__tests__/hooks/useDashboard.test.tsx`.

---

**Bug ID:** 2025-07-23-07
**Title:** Frontend tests fail due to Jest mock factory limitations and incomplete hook mocking.
**Module:** Dashboard (Test Suite)
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-23
**Classification:** Test Suite
**Severity:** High
**Description:**
Multiple test suites related to the new dashboard charts are failing.
1.  The test suites for `PortfolioHistoryChart` and `AssetAllocationChart` fail with a `ReferenceError` because the `jest.mock` factory for `react-chartjs-2` uses JSX, which conflicts with Jest's module hoisting.
2.  The test suite for `DashboardPage` fails with a `TypeError` because it does not mock the `useDashboardHistory` and `useDashboardAllocation` hooks, which are used by its child components.
**Steps to Reproduce:**
1. Run the frontend test suite: `docker-compose run --rm frontend npm test`.
**Expected Behavior:**
All dashboard-related test suites should pass.
**Actual Behavior:**
Tests fail with `ReferenceError` and `TypeError`.
**Resolution:**
1. Refactor the `jest.mock` factory in the chart component tests to use a standard function declaration to avoid the scoping issue.
2. Update `DashboardPage.test.tsx` to provide default mocks for all three dashboard hooks (`useDashboardSummary`, `useDashboardHistory`, `useDashboardAllocation`).
The old test file `frontend/src/__tests__/hooks/useDashboard.test.ts` was deleted, and its content was moved to a new file with the correct `.tsx` extension: `frontend/src/__tests__/hooks/useDashboard.test.tsx`.

---

**Bug ID:** 2025-07-23-07
**Title:** Frontend tests fail due to Jest mock factory limitations and incomplete hook mocking.
**Module:** Dashboard (Test Suite)
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-23
**Classification:** Test Suite
**Severity:** High
**Description:**
Multiple test suites related to the new dashboard charts are failing.
1.  The test suites for `PortfolioHistoryChart` and `AssetAllocationChart` fail with a `ReferenceError` because the `jest.mock` factory for `react-chartjs-2` uses JSX, which conflicts with Jest's module hoisting.
2.  The test suite for `DashboardPage` fails with a `TypeError` because it does not mock the `useDashboardHistory` and `useDashboardAllocation` hooks, which are used by its child components.
**Steps to Reproduce:**
1. Run the frontend test suite: `docker-compose run --rm frontend npm test`.
**Expected Behavior:**
All dashboard-related test suites should pass.
**Actual Behavior:**
Tests fail with `ReferenceError` and `TypeError`.
**Resolution:**
1. Refactor the `jest.mock` factory in the chart component tests to use a standard function declaration to avoid the scoping issue.
2. Update `DashboardPage.test.tsx` to provide default mocks for all three dashboard hooks (`useDashboardSummary`, `useDashboardHistory`, `useDashboardAllocation`).

---

**Bug ID:** 2025-07-23-08
**Title:** Frontend chart tests fail due to Jest mock scoping and unmocked canvas dependencies.
**Module:** Dashboard (Test Suite)
**Reported By:** Gemini Code Assist
**Date Reported:** 2025-07-23
**Classification:** Test Suite
**Severity:** High
**Description:**
Multiple test suites related to the new dashboard charts are failing or producing errors.
1.  The test suites for `PortfolioHistoryChart` and `AssetAllocationChart` fail with a `ReferenceError`. This is caused by using JSX syntax directly inside the `jest.mock` factory for `react-chartjs-2`, which conflicts with Jest's module hoisting and variable scoping.
2.  The test suite for `DashboardPage` passes but floods the console with `Not implemented: HTMLCanvasElement.prototype.getContext` errors. This is because the test renders the real chart components, which attempt to use the `<canvas>` API, an API that is not implemented in the JSDOM test environment.
**Steps to Reproduce:**
1. Run the frontend test suite: `docker-compose run --rm frontend npm test`.
**Expected Behavior:**
All dashboard-related test suites should pass without errors.
**Actual Behavior:**
Two test suites fail with `ReferenceError`, and one produces multiple console errors.
**Resolution:**
1. Refactor the `jest.mock` factory in all affected test suites (`PortfolioHistoryChart.test.tsx`, `AssetAllocationChart.test.tsx`, `DashboardPage.test.tsx`) to avoid using JSX directly. Instead, the mock will use `React.createElement` after lazily requiring the `react` module inside the factory. This resolves a variable scoping issue with Jest's module hoisting.
2. The mock in `DashboardPage.test.tsx` also serves to prevent the real chart components from being rendered, which would otherwise cause `<canvas>` API errors in the JSDOM test environment.

---

**Bug ID:** 2025-07-23-09
**Title:** Dashboard history endpoint crashes with 500 error on asset price lookup failure.
**Module:** Dashboard (Backend)
**Reported By:** User via E2E Test
**Date Reported:** 2025-07-23
**Classification:** Implementation (Backend)
**Severity:** High
**Description:**
The `GET /api/v1/dashboard/history` endpoint fails with a 500 Internal Server Error if any asset in the user's historical holdings does not have a price available from the financial data service. The price lookup call in `crud_dashboard.py` is not wrapped in a `try...except` block, causing any exception to crash the request.
**Steps to Reproduce:**
1. Log in to the application.
2. Create a portfolio and add a transaction for an asset whose price is not available (e.g., 'AAPL' in the current mock).
3. Navigate to the Dashboard page.
**Expected Behavior:**
The history chart should render, treating the value of the asset with the failed price lookup as 0 for the days it was held.
**Actual Behavior:**
The API request fails with a 500 error, and the history chart does not load.
**Resolution:**
Wrap the call to `financial_data_service.get_asset_price` within the `_get_portfolio_history` function in a `try...except` block to handle exceptions gracefully and default the price to 0.
The old test file `frontend/src/__tests__/hooks/useDashboard.test.ts` was deleted, and its content was moved to a new file with the correct `.tsx` extension: `frontend/src/__tests__/hooks/useDashboard.test.tsx`.

---

**Bug ID:** 2025-07-23-10
**Title:** Adding a transaction fails with 500 Internal Server Error.
**Module:** Portfolio Management (Backend)
**Reported By:** User via E2E Test
**Date Reported:** 2025-07-23
**Classification:** Implementation (Backend), API Integration
**Severity:** Critical
**Description:**
When a user adds a transaction for an asset that exists in the external financial service but not in the local database (e.g., 'GOOGL'), the operation fails with a `500 Internal Server Error`. This is caused by a `ForeignKeyViolation` in the database. The asset lookup endpoint (`GET /api/v1/assets/lookup/{ticker}`) correctly finds the asset externally but instead of creating it in the local database, it returns a placeholder object with `id: -1`. The frontend then attempts to create a transaction using this invalid `asset_id`, causing the database to reject the transaction.
**Steps to Reproduce:**
1. Log in to the application.
2. Attempt to add a transaction for a known ticker like 'GOOGL'.
**Expected Behavior:**
The asset should be created in the local database during the lookup, and the subsequent transaction creation should succeed.
**Actual Behavior:**
The API request fails with a 500 Internal Server Error.
**Resolution:**
The `lookup_ticker_symbol` endpoint in `backend/app/api/v1/endpoints/assets.py` must be updated. If an asset is found via the external service but not in the local database, the endpoint must first create the asset locally using `crud.asset.create` and then return the newly created, persisted asset object with its valid database ID.

---

**Bug ID:** 2025-07-23-11
**Title:** Backend crashes on startup with ImportError for 'deps' module.
**Module:** Core Backend, API Integration
**Reported By:** User via E2E Test
**Date Reported:** 2025-07-23
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The backend application fails to start due to a fatal `ImportError`. The file `app/api/v1/endpoints/assets.py` attempts to import the `deps` module from `app.api.v1` instead of the correct path `app.core.dependencies`. This incorrect import path prevents the application from starting.
**Steps to Reproduce:**
1. Run `docker-compose up --build`.
**Expected Behavior:**
The backend service should start successfully.
**Actual Behavior:**
The backend container crashes immediately with an `ImportError: cannot import name 'deps' from 'app.api.v1'`.
**Resolution:**
Correct the import path in `app/api/v1/endpoints/assets.py` to `from app.core import dependencies as deps`.

---

**Bug ID:** 2025-07-23-12
**Title:** Asset lookup for new assets fails with 503 Service Unavailable.
**Module:** Portfolio Management (Backend), API Integration
**Reported By:** User via E2E Test
**Date Reported:** 2025-07-23
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
When adding a transaction for an asset that exists externally but not locally (e.g., 'GOOGL'), the asset lookup endpoint (`GET /api/v1/assets/lookup/{ticker}`) fails with a 503 error. The backend logic fetches the asset details from the external service but fails to add the `ticker_symbol` to the details dictionary before passing it to the `AssetCreate` Pydantic schema. This causes a `ValidationError` which is incorrectly caught and re-raised as a 503 error.
**Steps to Reproduce:**
1. Log in and attempt to add a transaction for a known ticker like 'GOOGL'.
2. Observe the network request to the lookup endpoint fails.
**Expected Behavior:**
The asset should be created in the local database, and its details returned with a 200 OK status.
**Actual Behavior:**
The API returns a 503 Service Unavailable error.
**Resolution:**
Update the `lookup_ticker_symbol` endpoint in `backend/app/api/v1/endpoints/assets.py` to add the `ticker_symbol` to the `details` dictionary before creating the `AssetCreate` schema.

---

**Bug ID:** 2025-07-23-13
**Title:** Dashboard charts do not display all assets due to incomplete mock financial data.
**Module:** Dashboard (Backend), Mock Services
**Reported By:** User via E2E Test
**Date Reported:** 2025-07-23
**Classification:** Implementation (Backend)
**Severity:** High
**Description:**
When a user adds transactions for multiple assets (e.g., 'GOOGL' and 'AAPL'), the dashboard charts and summary only display data for assets that have a hardcoded price in the mock `FinancialDataService`. Assets without a mock price are silently skipped by the error handling, leading to an incomplete and incorrect dashboard view.
**Steps to Reproduce:**
1. Log in.
2. Add a transaction for 'GOOGL'.
3. Add a transaction for 'AAPL'.
4. Navigate to the Dashboard.
**Expected Behavior:**
The dashboard summary and charts should reflect the total value and allocation of both 'GOOGL' and 'AAPL'.
**Actual Behavior:**
The dashboard only shows data for 'GOOGL'.
**Resolution:**
Update the `get_asset_price` method in `backend/app/services/financial_data_service.py` to include a mock price for 'AAPL'.

---

**Bug ID:** 2025-07-23-14
**Title:** Active time range button in Portfolio History chart is invisible.
**Module:** Dashboard (Frontend), UI/Styling
**Reported By:** User via E2E Test
**Date Reported:** 2025-07-23
**Classification:** Implementation (Frontend)
**Severity:** Medium
**Description:**
When a time range button (e.g., "1Y") is selected on the Portfolio History chart, its background becomes white and its text becomes white, making it invisible against the card background. This is caused by the use of an undefined or misconfigured `bg-primary` CSS class.
**Steps to Reproduce:**
1. Navigate to the Dashboard.
2. Click on any of the time range buttons ("7D", "30D", "1Y", "All") on the "Portfolio History" chart.
**Expected Behavior:**
The active button should have a distinct background color (e.g., blue) with contrasting text (white) to clearly indicate the active state.
**Actual Behavior:**
The active button becomes invisible, appearing as a gap in the button group.
**Resolution:**
Replace the `bg-primary` class in `PortfolioHistoryChart.tsx` with a standard, visible Tailwind CSS class like `bg-blue-600`.

---

**Bug ID:** 2025-07-23-15
**Title:** Dashboard shows "0" for Unrealized and Realized P/L.
**Module:** Dashboard (Backend)
**Reported By:** User via E2E Test
**Date Reported:** 2025-07-23
**Classification:** Unimplemented Feature
**Severity:** Medium
**Description:**
The dashboard summary cards for "Unrealized P/L" and "Realized P/L" always display "0.0". This is the expected behavior for the current MVP, as the backend logic to calculate these metrics is a placeholder.
**Resolution:**
This is not a bug but a planned future enhancement. The business logic to calculate realized and unrealized profit and loss needs to be implemented in `crud_dashboard.py`.

---

**Bug ID:** 2025-07-23-16
**Title:** "Top Movers" table is always empty.
**Module:** Dashboard (Backend)
**Reported By:** User via E2E Test
**Date Reported:** 2025-07-23
**Classification:** Unimplemented Feature
**Severity:** Medium
**Description:**
The "Top Movers" table on the dashboard always shows "No market data available". This is the expected behavior for the current MVP, as the backend logic to identify top-moving assets is a placeholder and always returns an empty list.
**Resolution:**
This is not a bug but a planned future enhancement. The logic to calculate top movers needs to be implemented in `crud_dashboard.py`. This will likely require enhancing the `FinancialDataService` to provide 24-hour price change data.

---

**Bug ID:** 2025-07-23-17
**Title:** Users can create a SELL transaction for an asset on a date before they owned it.
**Module:** Portfolio Management (Backend)
**Reported By:** User via E2E Test
**Date Reported:** 2025-07-23
**Classification:** Implementation (Backend)
**Severity:** Critical
**Description:**
The transaction creation endpoint lacks validation to prevent a user from creating a SELL transaction for a quantity of an asset that is greater than the quantity they held on the specified transaction date. This allows for negative holdings and breaks data integrity. For example, a user can buy a stock in November but sell it in January of the same year.
**Steps to Reproduce:**
1. Create a BUY transaction for any asset with a future date.
2. Create a SELL transaction for the same asset with a past date.
**Expected Behavior:**
The API should return a 400 Bad Request error, preventing the creation of the SELL transaction.
**Actual Behavior:**
The transaction is created successfully, leading to incorrect portfolio data.
**Resolution:**
Add validation logic to the `create_with_portfolio` method in `crud_transaction.py`. Before creating a SELL transaction, the logic must calculate the user's holdings for that asset up to the transaction date and raise a 400 Bad Request error if the sell quantity is greater than the available holdings.

---

**Bug ID:** 2025-07-23-18
**Title:** Frontend displays a generic error message instead of the specific validation error from the backend.
**Module:** Portfolio Management (Frontend), Error Handling
**Reported By:** User via E2E Test
**Date Reported:** 2025-07-23
**Classification:** Implementation (Frontend)
**Severity:** Medium
**Description:**
When the backend correctly rejects a transaction with a 400 Bad Request and a specific error message (e.g., "Insufficient holdings to sell..."), the frontend `AddTransactionModal` does not display this specific message. Instead, it shows a generic "An unexpected error occurred" message, which provides no useful feedback to the user.
**Steps to Reproduce:**
1.  Attempt to create a SELL transaction for an asset with insufficient holdings.
2.  Submit the form.
**Expected Behavior:**
The modal should display the specific error message from the backend, e.g., "Insufficient holdings to sell. Current holdings: 0, trying to sell: 100."
**Actual Behavior:**
The modal displays "Error: An unexpected error occurred while adding the transaction".
**Resolution:**
The `AddTransactionModal.tsx` component must be updated. A new state variable should be added to hold the specific API error message. The `mutate` function call for creating a transaction needs an `onError` handler to parse the detailed error message from the Axios error response (`error.response.data.detail`) and set it in the new state variable for display in the UI.

---

**Bug ID:** 2025-07-23-19
**Title:** `AddTransactionModal` test fails due to outdated assertion after refactoring.
**Module:** Portfolio Management (Test Suite)
**Reported By:** User via Test Log
**Date Reported:** 2025-07-23
**Classification:** Test Suite
**Severity:** High
**Description:**
The test case "submits correct data for a new asset" in `AddTransactionModal.test.tsx` is failing. The test's assertion expects a flat object to be passed to the `createTransaction` mutation. However, after a recent refactoring to improve code quality, the mutation now expects a nested object: `{ portfolioId: number, data: TransactionCreate }`. The test was not updated to reflect this change.
**Steps to Reproduce:**
1. Run the frontend test suite: `docker-compose run --rm frontend npm test`.
**Expected Behavior:**
The test should pass.
**Actual Behavior:**
The test fails with an `expect(jest.fn()).toHaveBeenCalledWith(...)` error due to a payload mismatch.
**Resolution:**
Update the `toHaveBeenCalledWith` assertion in `AddTransactionModal.test.tsx` to match the new, correct call signature of the `useCreateTransaction` mutation hook.

---

**Bug ID:** 2025-07-24-01
**Title:** Test suite collection fails with `AttributeError` due to incorrect model imports.
**Module:** Core Backend, Test Suite
**Reported By:** QA Engineer
**Date Reported:** 2025-07-24
**Classification:** Test Suite
**Severity:** Critical
**Description:**
The test suite fails during the collection phase with `AttributeError: module 'app.models' has no attribute 'Asset'`. This is caused by test utility files (`app/tests/utils/asset.py`) and test files (`app/tests/api/v1/test_portfolios_transactions.py`) attempting to import SQLAlchemy models from the `app.models` package namespace. The project's architecture requires direct imports from the model's specific file.
**Steps to Reproduce:**
1. Run `docker-compose run --rm test`.
**Expected Behavior:**
The test suite should be collected and should run without import errors.
**Actual Behavior:**
Test collection is interrupted with `AttributeError: module 'app.models' has no attribute 'Asset'`.
**Resolution:**
Update the import statements in `app/tests/utils/asset.py` and `app/tests/api/v1/test_portfolios_transactions.py` to use direct imports (e.g., `from app.models.asset import Asset`) and remove the unused `app.models` import.
**Resolution:**
Update the import statements in `app/tests/utils/asset.py` and `app/tests/api/v1/test_portfolios_transactions.py` to use direct imports (e.g., `from app.models.asset import Asset`) and remove the unused `app.models` import.
The old test file `frontend/src/__tests__/hooks/useDashboard.test.ts` was deleted, and its content was moved to a new file with the correct `.tsx` extension: `frontend/src/__tests__/hooks/useDashboard.test.tsx`.

---

**Bug ID:** 2025-07-24-02
**Title:** Backend test suite has multiple failures due to incomplete FinancialDataService and outdated test helpers.
**Module:** Core Backend, Test Suite, Services
**Reported By:** QA Engineer
**Date Reported:** 2025-07-24
**Classification:** Implementation (Backend) / Test Suite
**Severity:** Critical
**Description:**
A large portion of the test suite (11 tests) is failing due to two primary root causes:
1. The `FinancialDataService` class is missing the `get_asset_price` and `get_asset_details` methods, causing `AttributeError` in any test that tries to mock them.
2. The `AssetCreate` Pydantic schema was updated to require an `exchange` field, but numerous test helpers (`create_test_transaction`) and direct test setups have not been updated to provide this field, leading to `ValidationError` and `422 Unprocessable Entity` errors.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
All backend tests should pass.
**Actual Behavior:**
11 tests fail with `AttributeError`, `ValidationError`, or `AssertionError`.
**Resolution:**
1. Implement the missing `get_asset_price` and `get_asset_details` methods in `app/services/financial_data_service.py`.
2. Update the test utility `app/tests/utils/transaction.py` and all direct instantiations of `schemas.AssetCreate` within the test files to include the required `exchange` field.

2. Update the test utility `app/tests/utils/transaction.py` and all direct instantiations of `schemas.AssetCreate` within the test files to include the required `exchange` field.
The old test file `frontend/src/__tests__/hooks/useDashboard.test.ts` was deleted, and its content was moved to a new file with the correct `.tsx` extension: `frontend/src/__tests__/hooks/useDashboard.test.tsx`.
The old test file `frontend/src/__tests__/hooks/useDashboard.test.ts` was deleted, and its content was moved to a new file with the correct `.tsx` extension: `frontend/src/__tests__/hooks/useDashboard.test.tsx`.

---

**Bug ID:** 2025-07-24-03
**Title:** Dashboard tests fail due to mocking incorrect FinancialDataService methods.
**Module:** Test Suite, Dashboard
**Reported By:** QA Engineer
**Date Reported:** 2025-07-24
**Classification:** Test Suite
**Severity:** High
**Description:**
The tests in `test_dashboard.py` are failing with `AssertionError`. The root cause is that the tests are mocking the `get_asset_price` method, but the dashboard's business logic actually calls `get_current_prices` (for summary/allocation) and `get_historical_prices` (for history). This causes the tests to use real data from `yfinance` instead of the intended mock data, leading to assertion failures.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
All dashboard tests should pass by using the mocked price data.
**Actual Behavior:**
Four dashboard tests fail because they use live market data instead of the mocked data.
**Resolution:**
Update the tests in `app/tests/api/v1/test_dashboard.py` to mock the correct methods (`get_current_prices` and `get_historical_prices`) with the appropriate return structures.

---

**Bug ID:** 2025-07-24-04
**Title:** Asset lookup tests fail due to testing obsolete external service logic.
**Module:** Test Suite, Portfolio Management
**Reported By:** QA Engineer
**Date Reported:** 2025-07-24
**Classification:** Test Suite
**Severity:** High
**Description:**
Two tests in `test_portfolios_transactions.py` (`test_lookup_asset_not_found` and `test_lookup_asset_external_and_create`) are failing with an `AttributeError`. This is because they attempt to mock the `get_asset_details` method on the `FinancialDataService`, which was intentionally removed during the refactoring to a local-database-only asset lookup strategy. The tests are now obsolete and need to be removed as they are testing a feature that no longer exists.
**Steps to Reproduce:**
1. Run the backend test suite: `docker-compose run --rm test`.
**Expected Behavior:**
All tests should pass.
**Actual Behavior:**
Two tests fail with `AttributeError` because they are trying to mock a method that has been deleted.
**Resolution:**
Remove the two obsolete tests from `app/tests/api/v1/test_portfolios_transactions.py`.
