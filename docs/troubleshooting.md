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

---

*After applying any of these fixes, always remember to rebuild your Docker containers (`docker-compose up --build`) to ensure the changes take effect.*