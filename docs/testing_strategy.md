# Testing Strategy
 
This document outlines the testing strategy for the Personal Portfolio Management System to ensure code quality, reliability, and maintainability. We employ a multi-layered testing approach.

## Core Principles & Standards

These principles are the foundation of our testing approach and were established following postmortems on test suite stabilization. Adherence is mandatory for all new development.

1. **Explicit Configuration Over Convention:** Test environment configuration must be explicit. For the backend, the `test` service definition in `docker-compose.yml` is the single source of truth for environment variables like `DATABASE_URL`. We will avoid dynamic generation or modification of configuration values within the test code itself.
2.  **Test Isolation via Transactions:** Integration tests that interact with the database must be wrapped in a transaction that is rolled back after each test to ensure isolation. The `db` fixture in `backend/app/tests/conftest.py` enforces this.
3.  **Explicit Fixture Dependencies:** Use pytest's fixture dependency mechanism to explicitly define the order in which fixtures are set up. For example, if fixture `A` depends on fixture `B`, define `A` as `def A(B): ...`.
4.  **Proactive Logging:** Maintain clear and informative logging in test setup and teardown processes (e.g., in `conftest.py`) to aid in debugging test failures.
5.  **Align Test Helpers with Application Logic:** Any utility functions used in tests (e.g., for generating test data) must respect all validation rules and constraints enforced by the application itself.
6.  **Define UX Patterns for E2E Tests:** Critical user experience (UX) patterns must be documented before E2E tests are written. For example, a standard pattern is that after a user successfully creates a new resource (e.g., a portfolio), the application should automatically navigate to that resource's detail page.
6.  **Test Environment Sanity Check:** The QA Engineer role includes a "Test Environment Sanity Check" at the beginning of each new module to validate the test environment configuration.

## AI-Assisted Development Workflow

To ensure accuracy, improve code quality, and prevent recurring issues, the following rigorous process is adopted for all AI-assisted development. The developer (Master Orchestrator) is the final verifier.

1.  **Context-Aware Scaffolding:**
    *   Before generating a new feature, the AI will request a full project file listing (`ls -R`) to build an accurate context map and prevent code duplication.

2.  **Rigorous Root Cause Analysis (RCA):**
    *   When an error occurs, the AI must analyze the **full stack trace**, not just the final error line.
    *   The AI must validate dependencies. Before suggesting a fix, it will ask to see the contents of imported files to verify function names, class definitions, and other contracts.
    *   The AI will state its debugging hypothesis clearly before proposing a solution.

3.  **Formal Bug Triage:**
    *   Before filing a new bug, the AI must first search `docs/bug_reports.md` for existing, related issues.
    *   If a related bug is found, the AI will propose updating it. A new bug will only be created if the issue is genuinely new.

4.  **Stale Context Mitigation:**
    *   The developer is the **source of truth**. If the AI appears to be working with outdated file information, the developer will provide the full, current content of the relevant file(s) to resynchronize the AI's context.

5.  **Sandboxed Environment Workflow:**
    *   When working in a sandboxed environment without Docker or administrative privileges, the AI assistant must follow the instructions in the `AGENTS.md` file. This file provides a self-contained, Docker-less development and testing process that uses a local SQLite database.

## 1. Backend Testing

The backend is tested using the `pytest` framework along with `httpx` for asynchronous API requests.

### a. Backend Unit Tests

* **Objective:** Verify that individual, isolated pieces of the backend code work correctly.
* **Location:** `backend/app/tests/`
* **Scope:**
* **Core Logic:** Test utility functions like password hashing and verification (`core/security.py`).
* **Schemas:** Test Pydantic model validators, especially for complex rules like password strength (`schemas/user.py`).

### b. Backend Integration Tests

* **Objective:** Verify that different parts of the backend work together as expected, focusing on API endpoints and their interaction with a test database.
* **Location:** `backend/app/tests/api/`
* **Scope:**
* **API Endpoints:** Test each endpoint for correct responses with valid data (2xx status codes), invalid client input (4xx status codes), and server errors (5xx status codes).
* **Database Interaction:** Ensure that API calls result in the correct state changes in the database (e.g., creating a user, fetching data).

## 2. Frontend Testing

Frontend testing is implemented using **Jest** and **React Testing Library**.
 
### a. Frontend Unit Tests

*   **Objective:** Test individual React components in isolation.
*   **Scope:**
    *   Verify that components render correctly with different props.
    *   Test component state changes and internal logic.

### b. Frontend Integration Tests

*   **Objective:** Test how multiple components work together, often involving user interaction and mocked API calls.
*   **Scope:**
    *   Simulate user interactions (e.g., filling out a form, clicking buttons).
    *   Mock API calls (`services/api.ts`) and custom hooks (`hooks/useUsers.ts`) to verify that components handle loading, success, and error states correctly.
    *   Ensure components are accessible by using `htmlFor` on labels and `id` on inputs, allowing tests to query elements by their accessible name.
    *   When testing components that appear in modals or overlays, use scoped queries (`within(screen.getByRole('dialog'))`) to avoid ambiguous matches with elements in the background.

### c. Frontend Manual E2E Smoke Test

*   **Objective:** To ensure that the newly developed feature is correctly integrated into the overall application flow.
*   **Scope:** After all automated tests pass, the developer will manually test the primary user flow of the new feature within the running application in a browser. This involves navigating through the relevant pages and verifying that all components are correctly connected and that data flows as expected (e.g., user data from `AuthContext` populating the `NavBar`).

## 3. Bug Tracking and Triage

To ensure accountability and maintain a high standard for both application and test code, all issues found during testing will be formally documented and tracked.

### Bug Classification

Bugs will be classified into two primary categories:

1.  **Implementation Bugs:**
    *   **Description:** An issue where the application does not behave according to the feature plan or requirements. This includes bugs in the backend logic, API behavior, or frontend UI/UX.
    *   **Team Assignment:** Filed against the **Backend Developer** or **Frontend Developer** role.

2.  **Test Suite Bugs:**
    *   **Description:** An issue within the test code itself. This includes incorrect test logic, flaky tests, faulty mocks, or tests that do not accurately verify the requirements.
    *   **Team Assignment:** Filed against the **QA Engineer** role.

### Bug Reporting Process

For this project, we will maintain a bug log in `docs/bug_reports.md`. All bugs found must be documented there before a fix is implemented. This creates a traceable history of issues and their resolutions.


## 4. End-to-End (E2E) Testing

The E2E test suite is implemented using **Playwright**. It is the final and most critical layer of our testing strategy, designed to validate complete user flows in an environment that closely mirrors production.

*   **Objective:** Simulate a real user's journey through the live application, interacting with both the frontend and the real backend.
*   **Scope:**
    *   Test critical user flows, such as user registration, login, and core feature interactions.
*   **Environment:**
    *   The E2E environment is defined in `docker-compose.e2e.yml`.
    *   It uses a dedicated test database (`pms_db_test`) to isolate test data from development data.
    *   A special backend endpoint (`/api/v1/testing/reset-db`) is exposed *only* in the test environment to allow for programmatic database resets between test runs.

### E2E Test Development Principles

The following principles were established after a rigorous E2E test suite stabilization phase and are mandatory for all new E2E tests:

1.  **Serial Execution:** Tests are executed serially (`workers: 1` in `playwright.config.ts`) to prevent race conditions. Since tests share a single database instance, parallel execution would lead to one test's setup interfering with another's.
2.  **Use Service Names for Networking:** When running inside Docker, tests must use Docker's service names for network requests (e.g., `baseURL: 'http://frontend:3000'`), not `localhost`.
3.  **Prefer User-Facing Locators:** Use locators that a user would see, such as `getByRole`, `getByLabel`, and `getByText`. This makes tests more resilient to code refactoring.
4.  **Scope Queries for Uniqueness:** When multiple identical elements exist (e.g., a "Delete" button in a list and another in a modal), scope the locator to a unique parent element (e.g., `page.getByRole('dialog').getByRole(...)`).
5.  **Rely on Auto-Waiting:** Prefer Playwright's built-in auto-waiting on assertions (`expect(locator).toBeVisible()`) over manual waits like `waitForTimeout`. This makes tests faster and more reliable.
6.  **Wait for Network Responses for State Changes:** When an action triggers an asynchronous data fetch (e.g., after creating a portfolio, the list re-fetches), use `page.waitForResponse()` to explicitly wait for the relevant API call to complete before asserting the UI has updated. This prevents race conditions.
7.  **Ensure Accessibility for Testability:** Frontend components, especially modals, must be accessible. A modal should have `role="dialog"` and `aria-modal="true"` so that it can be reliably located by the test runner.
8.  **Isolate Test Logic:** Each test file (`.spec.ts`) should be self-contained and perform its own setup in a `beforeAll` or `beforeEach` hook.