# Testing Strategy
 
This document outlines the testing strategy for the Personal Portfolio Management System to ensure code quality, reliability, and maintainability. We employ a multi-layered testing approach.

## Core Principles & Standards

These principles are the foundation of our testing approach and were established following postmortems on test suite stabilization. Adherence is mandatory for all new development.

1. **Explicit Configuration Over Convention:** Test environment configuration must be explicit. For the backend, the `test` service definition in `docker-compose.yml` is the single source of truth for environment variables like `DATABASE_URL`. We will avoid dynamic generation or modification of configuration values within the test code itself.
2.  **Test Isolation via Transactions:** Integration tests that interact with the database must be wrapped in a transaction that is rolled back after each test to ensure isolation. The `db` fixture in `backend/app/tests/conftest.py` enforces this.
3.  **Explicit Fixture Dependencies:** Use pytest's fixture dependency mechanism to explicitly define the order in which fixtures are set up. For example, if fixture `A` depends on fixture `B`, define `A` as `def A(B): ...`.
4.  **Proactive Logging:** Maintain clear and informative logging in test setup and teardown processes (e.g., in `conftest.py`) to aid in debugging test failures.
5.  **Align Test Helpers with Application Logic:** Any utility functions used in tests (e.g., for generating test data) must respect all validation rules and constraints enforced by the application itself.
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

E2E tests will be implemented using a framework like **Cypress** or **Playwright**.

*   **Objective:** Simulate a real user's journey through the live application, interacting with both the frontend and the real backend.
*   **Scope:**
    *   Test critical user flows, such as user registration, login, and core feature interactions.