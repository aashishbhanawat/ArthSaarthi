# Native Setup Guide (Without Docker)

This guide provides instructions for setting up and running the Personal Portfolio Management System directly on your local machine without using Docker. This is for users who cannot or prefer not to install Docker.

**Note:** This method is more complex than using the provided Docker setup and requires manual installation of all dependencies.

---

## 1. Prerequisites

Before you begin, ensure you have the following installed on your system:

*   **Python:** Version 3.9 or higher.
*   **Node.js:** Version 18.x or higher (which includes `npm`).
*   **PostgreSQL:** A running instance of PostgreSQL. You will need to create a database and a user for the application.
*   **Redis:** A running instance of Redis.
*   **Git:** For cloning the repository.

---

## 2. Backend Setup

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd pms
    ```

2.  **Navigate to the Backend Directory:**
    ```bash
    cd backend
    ```

3.  **Create and Activate a Python Virtual Environment:**
    ```bash
    # For Unix/macOS
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configure Environment Variables:**
    *   Create a `.env` file in the `backend/` directory by copying the example:
        ```bash
        cp .env.example .env
        ```
    *   Edit the `backend/.env` file and update the `DATABASE_URL` and `REDIS_URL` to point to your local instances.
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