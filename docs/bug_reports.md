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


