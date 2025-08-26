# Troubleshooting Guide

This guide documents common setup and runtime issues and their solutions.

---

### 1. Mixed Content Error on HTTPS

*   **Symptom:** When accessing the application via a secure `https://` domain (e.g., through a Cloudflare tunnel), the browser console shows a "Mixed Content" error. The page loads, but API calls to the backend fail.

    ```
    Mixed Content: The page at 'https://...' was loaded over HTTPS, but requested an insecure XMLHttpRequest endpoint 'http://...'.
    ```

*   **Cause:** The frontend is configured with an absolute `http://` URL for the backend API (`VITE_API_BASE_URL`). When the frontend is loaded over HTTPS, the browser blocks these insecure HTTP requests for security.

*   **Solution:** Configure the Vite development server to act as a proxy. This makes the frontend environment-agnostic.

    1.  **Proxy Frontend Requests:** In `frontend/vite.config.ts`, add a `server.proxy` configuration to forward all requests starting with `/api` to the backend service within the Docker network (e.g., `target: 'http://backend:8000'`).
    2.  **Use Relative Paths:** Update the frontend API client (`frontend/src/services/api.ts`) to use relative paths (e.g., `/api/v1/auth/status`). Remove the hardcoded `baseURL` and the `VITE_API_BASE_URL` environment variable.
    3.  **Update CORS Origins:** Add your secure HTTPS domain to the `CORS_ORIGINS` list in `backend/.env`.


### 2. Vite "Host Not Allowed" Error

*   **Symptom:** When accessing the application via a custom domain, the browser console shows an error like:

    ```
    Blocked request. This host ("custom.domain.com") is not allowed.
    ```

*   **Cause:** This is a security feature in Vite to prevent DNS Rebinding attacks. By default, it only accepts requests from `localhost`.

*   **Solution:** Explicitly allow your custom domain in the Vite configuration.

    1.  In `frontend/vite.config.ts`, add an `allowedHosts` array to the `server` configuration and include your domain name (e.g., `"librephotos.aashish.ai.in"`).


### 3. API calls fail with 404 Not Found

*   **Symptom:** Some API calls succeed, but others fail with a `404 Not Found` error, even though the endpoint exists on the backend.

*   **Cause:** The failing API call is using a URL path that does not match the Vite proxy configuration. For our setup, all backend calls must be prefixed with `/api`.

*   **Solution:** Ensure all API calls in the frontend code (e.g., in `services/api.ts` or components like `SetupForm.tsx`) are prefixed correctly.

    *   **Incorrect:** `apiClient.post('/auth/setup', ...)`
    *   **Correct:** `apiClient.post('/api/v1/auth/setup', ...)`

### 4. Admin Features or User Name Not Appearing After Login

*   **Symptom:** After a user logs in, admin-specific UI elements (like a "User Management" link) or the user's full name do not appear in the navigation bar or dashboard.

*   **Cause:** This is typically due to a failure in fetching the user's details after the login is complete. The `AuthContext` likely attempts to fetch user data from an endpoint like `/api/v1/users/me` but the request fails. Common reasons include:
    1.  **Incorrect API Path:** The path in the `AuthContext`'s `fetchUserData` function is wrong (e.g., `/users/me` instead of `/api/v1/users/me`).
    2.  **Authentication Token Not Sent:** The API interceptor in `services/api.ts` is not correctly attaching the `Authorization: Bearer <token>` header. This can happen if the key used to retrieve the token from `localStorage` (e.g., `localStorage.getItem("authToken")`) does not match the key used when setting it during login (e.g., `localStorage.setItem("token", ...)`).

*   **Solution:**
    1.  Verify the API path for fetching user data in `AuthContext.tsx` is correct and includes the `/api/v1` prefix.
    2.  Ensure the `localStorage` key is consistent across your application for setting and getting the authentication token.

### 5. "No routes matched location" for Admin Pages

*   **Symptom:** Clicking a link to an admin-only section like `/admin/users` results in a blank page and a `No routes matched location` error in the console.

*   **Cause:** The main application router in `App.tsx` has not been configured to handle the specific admin path.

*   **Solution:**
    1.  Create a dedicated `AdminRoute.tsx` component that checks if the `user` from `AuthContext` has the `is_admin` flag set to true.
    2.  In `App.tsx`, update the `<Routes>` to include a nested route structure for admin pages, protected by both the standard `ProtectedRoute` (checks for a token) and the new `AdminRoute` (checks for admin privileges).

### 6. User Management Page Crashes with "No QueryClient set"

*   **Symptom:** After fixing routing, navigating to the `UserManagementPage` immediately crashes the application with the error `Uncaught Error: No QueryClient set, use QueryClientProvider to set one`.

*   **Cause:** The page or one of its child components uses React Query hooks (`useQuery`, `useMutation`), but the root of the application is not wrapped in the required `<QueryClientProvider>`.

*   **Solution:** In the main `App.tsx` file, instantiate a new `QueryClient` and wrap the entire application (typically the `<Router>` component) with the `<QueryClientProvider client={queryClient}>`.

---

### 7. Docker Compose fails with "unhealthy" container error

*   **Symptom:** Running `docker-compose up` or `docker-compose run` fails immediately with an error similar to:

    ```
    ERROR: for backend  Container "..." is unhealthy.
    ```

*   **Cause:** This typically happens when a previous `docker-compose up` command was interrupted or included a service that is designed to exit (like our `test` service). This leaves behind a stopped container that Docker marks as "unhealthy". Subsequent commands are trying to attach to this stale container instead of creating a new one.

*   **Solution:** Perform a clean reset of the Docker environment for the project.

    1.  **Stop and remove all containers, networks, and volumes** associated with the project by running the following command from the project root:
        ```bash
        docker-compose down
        ```
    2.  You can now start the application fresh with `docker-compose up --build db backend frontend`.

*   **If the error persists,** you may need to perform a more aggressive system-wide prune to remove all unused Docker data (stopped containers, networks, and build cache). **Warning:** This will affect all projects on your machine, not just this one.

    ```bash
    # This is a more forceful cleanup
    docker system prune -a -f
    ```

    After running the prune command, try starting the application again.

---

### 8. Backend crashes with `UndefinedColumn` or `ProgrammingError`

*   **Symptom:** The backend starts but then crashes when you try to access a page. The logs show an error like:

    ```
    sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedColumn) column "..." does not exist
    ```

*   **Cause:** The application's SQLAlchemy models (in `backend/app/models/`) have been updated, but the corresponding Alembic migration has not been generated or applied. This causes the database schema to be out of sync with the application's expectations.

*   **Solution:** You need to generate a new migration script to align the database schema with your model changes.

    1.  **Generate a new migration script.** Run the following command from the project root, replacing the message with a description of your change. This command executes Alembic inside a temporary backend container.
        ```bash
        docker-compose run --rm backend alembic revision --autogenerate -m "Describe your model change here"
        ```
    2.  **Apply the migration.** Restart the application. The `entrypoint.sh` script will automatically apply the new migration script on startup.
        ```bash
        docker-compose up --build -d backend
        ```

---

### 9. E2E tests fail with `net::ERR_CONNECTION_REFUSED`

*   **Symptom:** The Playwright E2E test suite fails immediately with a connection error.

    ```
    Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/
    ```

*   **Cause:** The E2E tests run inside a Docker container (`e2e-tests`). From within this container, `localhost` refers to the container itself, not the `frontend` service. The test runner is trying to connect to a web server that doesn't exist at that address.

*   **Solution:** The `baseURL` in the Playwright configuration must be updated to use the Docker service name, which is resolvable on the shared Docker network.

    1.  Open the Playwright config file: `e2e/playwright.config.ts`.
    2.  Change the `baseURL` from `http://localhost:3000` to `http://frontend:3000`.

---

### 10. How to Reset the Database

*   **Symptom:** You need to completely wipe all data and start with a fresh, empty database. This is often necessary after major schema changes or to clear out test data.

*   **Cause:** The database data is stored in a persistent Docker volume (`postgres_data`). Simply stopping and starting the containers with `docker-compose down` and `docker-compose up` will not delete this data.

*   **Solution:** Use the `-v` flag with `docker-compose down` to remove the volumes along with the containers.

    1.  **Stop and remove all containers, networks, and volumes:**
        ```bash
        docker-compose down -v
        ```
    2.  **Start the application fresh:**
        ```bash
        docker-compose up --build db backend frontend
        ```
    3.  **Perform initial setup:** Since the database is now empty, you will need to go to `http://localhost:3000` and create the initial admin user again.

---

### 11. E2E tests are "flaky" or fail with database errors

*   **Symptom:** The E2E test suite fails intermittently with errors like `relation "users" does not exist` or other database-related issues. The failures might not happen on every run, and a re-run might pass.

*   **Cause:** This is a race condition. By default, Playwright runs test files in parallel. Both of our E2E test files (`admin-user-management.spec.ts` and `portfolio-and-dashboard.spec.ts`) have a `beforeAll` hook that resets the same shared database. When run in parallel, one test's setup can wipe the database while the other is in the middle of its run, causing unpredictable failures.

*   **Solution:** The project has been configured to force serial execution for E2E tests to prevent this race condition.

    1.  Open the Playwright config file: `e2e/playwright.config.ts`.
    2.  Ensure that the `workers` property is set to `1`. This forces all test files to run one after another in the same process.
        ```typescript
        import { defineConfig } from '@playwright/test';

        export default defineConfig({
          // ...
          /* Run tests in files in parallel */
          fullyParallel: false,
          /* Fail the build on CI if you accidentally left test.only in the source code. */
          forbidOnly: !!process.env.CI,
          /* Opt out of parallel tests on CI. */
          workers: 1,
          // ...
        });
        ```

---

*After applying any of these fixes, always remember to rebuild your Docker containers (`docker-compose up --build`) to ensure the changes take effect.*

---

### 15. Backend crashes with `DetachedInstanceError` on DELETE

*   **Symptom:** An API endpoint that deletes an object from the database fails with a `500 Internal Server Error`. The backend logs show `DetachedInstanceError: Parent instance <...> is not bound to a Session; lazy load operation of attribute '...' cannot proceed`.

*   **Cause:** This happens when you delete an object from the database and then try to return that same object in the API response. After `db.commit()`, the SQLAlchemy object becomes "detached" from the session. If your Pydantic `response_model` for the endpoint includes a related field (e.g., returning a `WatchlistItem` that includes its `asset`), FastAPI/Pydantic will try to access that relationship. Because the object is detached, SQLAlchemy tries to lazy-load the relationship from the database, but it can't, which causes the crash.

*   **Solution:** You must eagerly load any required relationships *before* you delete the object. This ensures all the data needed for the response is already loaded into the object's memory before it's detached from the session.

    *   **Incorrect (will crash):**
        ```python
        @router.delete("/items/{item_id}")
        def delete_item(item_id: int, db: Session = Depends(get_db)):
            item = crud.item.remove(db, id=item_id) # Fetches and deletes
            db.commit()
            return item # Crashes here if response_model needs item.related_thing
        ```

    *   **Correct:**
        ```python
        from sqlalchemy.orm import joinedload

        @router.delete("/items/{item_id}")
        def delete_item(item_id: int, db: Session = Depends(get_db)):
            # Eagerly load the item AND its relationship first
            item = (
                db.query(ItemModel)
                .options(joinedload(ItemModel.related_thing))
                .filter(ItemModel.id == item_id)
                .first()
            )
            # ... (add checks for not found, permissions, etc.)

            # Now delete the object that has the data pre-loaded
            db.delete(item)
            db.commit()
            return item # Works because item.related_thing is already loaded
        ```

### 12. Frontend tests fail with "Cannot find module" for libraries like Heroicons.

*   **Symptom:** The Jest test suite fails with errors like `Cannot find module '@heroicons/react/24/solid' from 'src/...'`. This happens even if the library is correctly installed.

*   **Cause:** This is a complex issue with multiple potential causes, often related to how Jest's module resolver interacts with modern JavaScript packages, especially in a Vite + TypeScript + Docker environment. Common causes include:
    1.  **Jest's `moduleNameMapper` is not configured:** Jest doesn't know how to handle non-JavaScript imports (like SVGs from an icon library) by default.
    2.  **ES Module (ESM) vs. CommonJS (CJS) Conflict:** The project's `package.json` may have `"type": "module"`, which tells Node.js to treat `.js` files as ES Modules. However, Jest's configuration files (`jest.config.js`) and mock files often use the older CommonJS syntax (`module.exports`). This conflict can break module resolution.

*   **Solution:** A robust, multi-step solution is required to stabilize the test environment.

    1.  **Use a dedicated Jest config file.** Move all Jest configuration out of `package.json` and into a dedicated `frontend/jest.config.cjs` file. **Note the `.cjs` extension**, which explicitly tells Node.js to treat this file as a CommonJS module, resolving the ESM/CJS conflict.
    2.  **Configure `moduleNameMapper` in `jest.config.cjs`.** Add a `moduleNameMapper` to intercept imports from problematic libraries and redirect them to a manual mock.
        ```javascript
        // frontend/jest.config.cjs
        module.exports = {
          // ... other config
          moduleNameMapper: {
            '^@heroicons/react/24/(outline|solid)$': '<rootDir>/src/__mocks__/heroicons.cjs',
          },
        };
        ```
    3.  **Create a robust mock file.** Create a mock file at `frontend/src/__mocks__/heroicons.cjs`. **Note the `.cjs` extension.** This file should also use CommonJS syntax. Using a JavaScript `Proxy` is a robust way to mock any named export from the library.
        ```javascript
        // frontend/src/__mocks__/heroicons.cjs
        const React = require('react');
        module.exports = new Proxy({}, { get: () => () => React.createElement('div') });
        ```
    4.  **Update `package.json`.** Ensure the `test` script points to the new configuration file: `"test": "jest --config jest.config.cjs"`.

---

### 13. Data Import Commit Fails

*   **Symptom:** You upload a CSV file, the preview looks correct, but when you click "Commit Transactions", the process fails.
*   **Cause:** The most common cause is that the transactions in the source CSV file are not in the correct chronological order. If a 'SELL' transaction for an asset appears in the file *before* its corresponding 'BUY' transaction, the backend validation will correctly reject the 'SELL' because it would result in a negative holding.
*   **Solution:** The application logic has been updated to automatically sort all parsed transactions by date, ticker, and then type (BUY before SELL) before they are committed. This should resolve most issues. If you are still encountering errors, ensure your CSV file has the correct columns required by the selected parser (e.g., Zerodha, ICICI Direct).

---

### 14. Proactive Error Avoidance Plan

*   **Objective:** To formalize a set of checks to avoid common environmental and access-related errors experienced in previous sessions.

*   **Disk Space Issues (`df -h`)**
    *   **Problem:** Previous sessions have failed due to "out of space" errors, especially when running tests or building large Docker images.
    *   **Mitigation:** Before running any potentially disk-intensive command (like `docker-compose up --build`, `npm install`, or `pytest`), first check the available disk space.
        ```bash
        df -h
        ```
    *   **Action:** If disk space is low (e.g., usage is > 90%), proactively clean up old Docker images, volumes, and build caches (`docker system prune -a -f`) or other temporary files before proceeding. When running containers, use the `--rm` flag where appropriate (e.g., `docker-compose run --rm test`) to ensure they are removed after execution.

*   **Access/Path Failures (`pwd`, `ls -l`)**
    *   **Problem:** Commands have failed because they were run from the wrong directory, or because a file or directory did not have the expected permissions.
    *   **Mitigation:** Before running a command that depends on the current working directory or specific file paths, always verify your location and the existence/permissions of the target files.
        ```bash
        pwd
        ls -l path/to/your/file
        ```
    *   **Action:** Ensure you are in the project's root directory before running `docker-compose` commands. Double-check that any file paths passed as arguments are correct and that the files are readable.

*   **Docker Compose Pull Failures**
    *   **Problem:** `docker-compose up --build` can sometimes fail if it has trouble pulling a base image from a remote registry.
    *   **Mitigation:** To improve reliability, you can pre-pull the necessary images before running the main build command.
        ```bash
        # You can specify multiple services
        docker-compose pull db backend frontend
        ```
    *   **Action:** If a pull fails, running `docker-compose pull <service_name>` directly can often provide a more specific error message than the generic `up` command. This also helps in caching the images locally for faster and more reliable subsequent builds.
