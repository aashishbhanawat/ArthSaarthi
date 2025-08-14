# Native Setup Guide (Without Docker)

This guide provides instructions for setting up and running **ArthSaarthi** directly on your local machine without using Docker.

**The recommended approach for native setup is to use SQLite**, as it simplifies the process by removing the need for external database and Redis servers.

---

## 1. Prerequisites

*   **Python:** Version 3.9 or higher.
*   **Node.js:** Version 18.x or higher (which includes `npm`).
*   **Git:** For cloning the repository.

---

## 2. Backend Setup

### SQLite Setup (Recommended)

This is the simplest way to get the backend running.

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd pms/backend
    ```

2.  **Create and Activate a Python Virtual Environment:**
    ```bash
    # For Unix/macOS
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    *   Create a `.env` file in the `backend/` directory by copying the example:
        ```bash
        cp .env.example .env
        ```
    *   Edit the `backend/.env` file and set `DATABASE_TYPE=sqlite`. You can leave the other database variables as they are; they will be ignored.

### PostgreSQL Setup

This method is more complex and requires a running PostgreSQL and Redis instance.

1.  **Prerequisites:**
    *   A running instance of PostgreSQL.
    *   A running instance of Redis.

2.  **Follow steps 1-4 from the SQLite setup.**

3.  **Configure Environment Variables:**
    *   In the `backend/.env` file, ensure `DATABASE_TYPE` is set to `postgres`.
    *   Update the `DATABASE_URL` and `REDIS_URL` to point to your local instances.
        *   **`DATABASE_URL`:** `postgresql://<your_user>:<your_password>@localhost:5432/<your_db_name>`
        *   **`REDIS_URL`:** `redis://localhost:6379/0`

---

## 3. Frontend Setup

1.  **Navigate to the Frontend Directory:**
    *   From the project root, run:
        ```bash
        cd frontend
        ```

2.  **Install Dependencies:**
    ```bash
    npm install
    ```

3.  **Configure Environment Variables (Optional but Recommended):**
    *   The frontend uses a proxy in `vite.config.ts` to forward API requests. By default, it points to `http://backend:8000`, which only works inside Docker. To run natively, you need to point it to your local backend server.
    *   While you can edit `vite.config.ts` directly, the best practice is to create a `.env.local` file in the `frontend/` directory to override this setting.
    *   Create `frontend/.env.local` with the following content:
        ```
        VITE_API_PROXY_TARGET=http://localhost:8000
        ```
    *   If you need to access the dev server from a different machine on your network (e.g., from your phone), you will also need to add your machine's IP address or hostname to the `ALLOWED_HOSTS` variable in your `frontend/.env.local` file:
        ```
        ALLOWED_HOSTS=192.168.1.100,your-pc-name.local
        ```

---

## 4. Running the Application

You will need to run the backend and frontend servers in two separate terminal windows.

1.  **Start the Backend Server:**
    *   Open a terminal, navigate to the `backend/` directory, and ensure your virtual environment is activated.
    *   Run the startup script:
        ```bash
        ./entrypoint.sh
        ```
    *   The backend will be running at `http://localhost:8000`.

2.  **Start the Frontend Server:**
    *   Open a second terminal and navigate to the `frontend/` directory.
    *   Run the development server:
        ```bash
        npm run dev
        ```
    *   The frontend will be accessible at `http://localhost:3000`.

You can now access the application in your browser at `http://localhost:3000`.

---

## 5. Enabling Debug Logs (Optional)

To get more detailed logs for troubleshooting, you can start the services with debug flags.

*   **PostgreSQL:**
    *   You will need to edit your local `postgresql.conf` file and set `log_statement = 'all'`. The location of this file varies by operating system.

*   **Redis:**
    *   Start the Redis server with the `loglevel` flag: `redis-server --loglevel debug`

*   **Frontend (Vite):**
    *   Start the frontend dev server with the `--debug` flag: `npm run dev -- --debug`

---

For troubleshooting common issues, please refer to the main Troubleshooting Guide.