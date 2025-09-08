# Installation Guide

Welcome to ArthSaarthi! This guide provides detailed instructions for setting up the application. Please choose the mode that best fits your needs.

*   **Desktop Mode (Recommended for most users):** A simple, single-user application that you can install on your computer with one click. No technical knowledge is required.
*   **Server Mode (Advanced):** A multi-user web service that you can host for yourself or a small group. This requires some technical comfort with command-line tools.

---

## 1. Desktop Mode (Single-User)

This is the **easiest and recommended** way to use ArthSaarthi for personal portfolio management. It runs entirely on your computer, ensuring your financial data never leaves your machine. It uses a file-based SQLite database with **column-based encryption** for sensitive fields and does not require any external services.

### Installation

1.  **Download the Installer:** Go to the [**Project Releases Page**](https://github.com/aashishbhanawat/ArthSaarthi/releases) on GitHub.
2.  **Find the latest release** and download the correct file for your operating system:
    *   **Windows:** `ArthSaarthi-Setup-x.x.x.exe`
    *   **macOS:** `ArthSaarthi-x.x.x.dmg`
    *   **Linux:** `ArthSaarthi-x.x.x.AppImage` or `.deb`
3.  **Run the Installer:**
    *   **Windows:** Double-click the `.exe` file and follow the installation prompts.
    *   **macOS:** Double-click the `.dmg` file, then drag the ArthSaarthi icon into your "Applications" folder.
    *   **Linux:** Make the `.AppImage` file executable (`chmod +x ArthSaarthi-*.AppImage`) and then double-click to run it.

Once installed, you can launch ArthSaarthi like any other desktop application.

---

## 2. Server Mode (Multi-User)

This mode is for technically advanced users who wish to self-host ArthSaarthi as a web service. It supports multiple user accounts and is designed to run on a server.

### A) Docker Installation (Recommended for Server Mode)

This method uses pre-built Docker images from Docker Hub for a consistent and reliable environment. It is the recommended way to run ArthSaarthi in Server Mode.

#### Prerequisites

*   **Docker:** Get Docker
*   **Docker Compose:** Install Docker Compose

#### Step-by-Step Guide (Linux/macOS)

1.  **Create a directory** for the application and navigate into it:
    ```bash
    mkdir arthsaarthi && cd arthsaarthi
    ```
2.  **Download Configuration Files:** Download the `docker-compose.yml` and the production environment template.
    ```bash
    # Note: We are downloading the production compose file and naming it docker-compose.yml for simplicity.
    curl -L -o docker-compose.yml https://raw.githubusercontent.com/aashishbhanawat/ArthSaarthi/main/docker-compose.prod.yml
    curl -L -o .env.prod.example https://raw.githubusercontent.com/aashishbhanawat/ArthSaarthi/main/backend/.env.prod.example
    ```
3.  **Create Your Environment File:** Copy the example file. This file will hold your secret keys and domain settings.
    ```bash
    cp .env.prod.example .env.prod
    ```
4.  **Edit `.env.prod`:** You **must** edit this file to set a `SECRET_KEY` and your `CORS_ORIGINS`.
    *   Generate a secure secret key: `openssl rand -hex 32`
    *   Set `CORS_ORIGINS` to the domain name or IP address you will use to access the application. Example: `CORS_ORIGINS=http://localhost,http://192.168.1.50`
5.  **Start the Application:** This command pulls the official images from Docker Hub and starts all services.
    *   By default, this will pull the `latest` version. To pull a specific version (e.g., `v0.2.0`), you can set the `APP_VERSION` environment variable before running the command: `export APP_VERSION="v0.2.0"`
    ```bash
    docker-compose up -d
    ```
    *(The `-d` flag runs the services in the background.)*
6.  **Access the Application:**
    *   **Frontend:** `http://localhost` (or your server's IP/domain). The application runs on port 80 by default. You can change this by setting the `FRONTEND_PORT` environment variable (e.g., `export FRONTEND_PORT=8080`).
    *   **Backend API Docs:** `http://localhost:8000/docs`

#### First-Time Setup

The very first time you access the application, you will be prompted to create the initial **administrator account**. This is a one-time setup.

#### Using with a Domain Name and HTTPS (via Cloudflare Tunnel)

To expose your self-hosted ArthSaarthi instance to the internet securely, you can use a tunnel service like Cloudflare Tunnels (`cloudflared`). This is the recommended way to enable HTTPS.

The process is straightforward:

1.  **Run the application** using the Docker installation method described above. The frontend service (Nginx) will be available on your host machine at `http://localhost:80`.
2.  **Set up `cloudflared`** to create a tunnel that points traffic from your public domain (e.g., `https://appname.your-domain.com`) to your local service at `http://localhost:80`.
3.  **CRITICAL:** You **must** update the `CORS_ORIGINS` variable in your `.env.prod` file to include your full public HTTPS domain. If you don't, the frontend will be blocked from making API calls to the backend.

    *Example `CORS_ORIGINS` setting:*
    ```
    CORS_ORIGINS=https://appname.your-domain.com
    ```
4.  **Restart the application** for the new CORS setting to take effect: `docker-compose restart`.

#### Stopping and Resetting

*   **To stop services:** `docker-compose down`
*   **To reset all data:** `docker-compose down -v` (Warning: This is irreversible).

### B) Native Installation (Advanced, Not Recommended)

This method runs all services directly on your host machine without Docker. It is complex and only recommended if you cannot use Docker.

#### Prerequisites

*   **Operating System:** Linux (recommended), macOS, or Windows (with WSL).
*   **Software:** Python (3.9+), Node.js (18+), Git, PostgreSQL Server, Redis Server.

#### Setup

1.  **Install all prerequisites** using your system's package manager (e.g., `apt`, `brew`, `choco`).
2.  **Clone the repository** and `cd` into the `ArthSaarthi` directory.
3.  **Setup Backend:**
    *   `cd backend`
    *   Create and activate a Python virtual environment (e.g., `python3 -m venv venv && source venv/bin/activate`).
    *   Install dependencies: `pip install -r requirements.txt`
    *   Create and edit `backend/.env`, setting `DATABASE_URL` and `REDIS_URL` to point to your local PostgreSQL and Redis instances.
4.  **Setup Frontend:**
    *   `cd frontend`
    *   Install dependencies: `npm install`
    *   Create `frontend/.env.local` and add the line `VITE_API_PROXY_TARGET=http://localhost:8000`.

#### Running

You must run the backend and frontend in two separate terminals.

1.  **Terminal 1 (Backend):** Navigate to `backend/`, activate the virtual environment, and run `./entrypoint.sh`.
2.  **Terminal 2 (Frontend):** Navigate to `frontend/` and run `npm run dev`.

#### Using SQLite in Native Server Mode (Optional)

You can run a native server installation with SQLite and a file-based cache by setting `DATABASE_TYPE=sqlite` and `CACHE_TYPE=disk` in `backend/.env`.

**Security Warning:** This configuration is **not recommended** for a multi-user server environment. The SQLite database file is **not encrypted** in this mode, which poses a security risk. Encryption is only supported in the single-user Desktop Mode.
