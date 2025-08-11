# Native Setup Guide (Without Docker)

This guide provides instructions on how to set up and run the Personal Portfolio Management System on your local machine without using Docker. This is useful for development or for environments where Docker is not available.

## 1. Prerequisites

Before you begin, you need to install the following software on your system. Please use the recommended versions to ensure compatibility.

*   **Git:** For cloning the repository.
*   **Python:** Version 3.11.x
*   **Node.js:** Version 18.x (which includes `npm`)
*   **PostgreSQL:** Version 13.x
*   **Redis:** Version 6.x or later

### Installation Guides

*   **macOS (using Homebrew):**
    ```bash
    brew install python@3.11 node@18 postgresql@13 redis
    brew services start postgresql@13
    brew services start redis
    ```
*   **Windows (using Chocolatey or official installers):**
    *   Install Chocolatey from [chocolatey.org](https://chocolatey.org/install).
    *   Run PowerShell as Administrator:
        ```powershell
        choco install python --version=3.11.5
        choco install nodejs --version=18.17.1
        choco install postgresql13
        choco install redis-64
        ```
    *   Follow the post-installation instructions for PostgreSQL to set up a user and password.

## 2. Initial Setup

### Clone the Repository

```bash
git clone <repository-url>
cd personal-portfolio-management-system
```

### Configure Environment Variables

The application uses environment variables for configuration.

1.  **Backend:**
    *   Navigate to the `backend` directory: `cd backend`
    *   Copy the example environment file: `cp .env.prod.example .env`
    *   Edit the `.env` file with your local settings. Key variables to change are:
        *   `POSTGRES_SERVER`: `localhost`
        *   `POSTGRES_PORT`: `5432`
        *   `POSTGRES_USER`: Your PostgreSQL username.
        *   `POSTGRES_PASSWORD`: Your PostgreSQL password.
        *   `POSTGRES_DB`: A name for the database (e.g., `pms_native`).
        *   `REDIS_HOST`: `localhost`
        *   `SECRET_KEY`: Generate a strong secret key. You can use `openssl rand -hex 32` to generate one.

2.  **Frontend:**
    *   The frontend reads its configuration from the backend, so no separate `.env` file is typically needed for it to connect.

## 3. Backend Setup

1.  **Create and Activate a Virtual Environment:**
    From the `backend` directory:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    # On Windows, use: venv\Scripts\activate
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Create the Database:**
    *   Open the PostgreSQL command-line tool (`psql`).
    *   Create the database specified in your `.env` file:
        ```sql
        CREATE DATABASE pms_native;
        ```

4.  **Run Database Migrations:**
    *   Make sure you are in the `backend` directory with the virtual environment activated.
    *   Run the Alembic migrations to create the database tables:
        ```bash
        alembic upgrade head
        ```

## 4. Frontend Setup

1.  **Navigate to the Frontend Directory:**
    From the root of the project: `cd frontend`

2.  **Install Dependencies:**
    ```bash
    npm install
    ```

## 5. Running the Application

You will need two separate terminal windows to run the backend and frontend servers.

1.  **Run the Backend Server:**
    *   Open a terminal in the `backend` directory.
    *   Activate the virtual environment (`source venv/bin/activate`).
    *   Start the FastAPI server with Uvicorn:
        ```bash
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
        ```

2.  **Run the Frontend Server:**
    *   Open a second terminal in the `frontend` directory.
    *   Start the Vite development server:
        ```bash
        npm run dev
        ```

The application should now be running:
*   **Frontend:** `http://localhost:3000`
*   **Backend API Docs:** `http://localhost:8000/docs`

To run the application in a production-like mode, you would first build the frontend (`npm run build`) and then serve the static files in the `frontend/dist` directory with a web server like Nginx. The backend should be run with a production-grade server like `gunicorn`.