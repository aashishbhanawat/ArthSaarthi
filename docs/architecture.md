# System Architecture Document

This document outlines the high-level architecture for the Personal Portfolio Management System (PMS).

## 1. Architecture Diagram

The following diagram illustrates the components of the system and the flow of information. For the complete ERD and core class diagrams, please refer to the unified `[uml_design.md](./uml_design.md)`.

```mermaid
graph TD
    classDef frontend fill:#3498db,stroke:#2980b9,stroke-width:2px,color:#fff;
    classDef backend fill:#2ecc71,stroke:#27ae60,stroke-width:2px,color:#fff;
    classDef database fill:#f1c40f,stroke:#f39c12,stroke-width:2px,color:#000;
    classDef external fill:#95a5a6,stroke:#7f8c8d,stroke-width:2px,color:#fff;

    subgraph "Client Tier"
        direction TB
        Browser["User Browser (React SPA)"]:::frontend
        Desktop["Desktop App (Electron + React)"]:::frontend
        Mobile["Mobile App (Android / Capacitor.js)"]:::frontend
    end

    subgraph "Application Tier (Python / FastAPI)"
        direction TB
        API["FastAPI REST Router"]:::backend
        AuthService["Authentication & Security"]:::backend
        AnalyticsService["Portfolio Analytics (XIRR, Benchmarks)"]:::backend
        DataImportService["Data Import (File Parsers)"]:::backend

        API --> AuthService
        API --> AnalyticsService
        API --> DataImportService
    end

    subgraph "Data Tier"
        direction TB
        PostgreSQL[("PostgreSQL (Server) / SQLite (Desktop/Mobile)")]:::database
        Redis[("Redis (Server) / DiskCache (Desktop/Mobile)")]:::database
    end

    subgraph "External Integrations"
        direction TB
        YFinance["yfinance API"]:::external
        ExchangeData["NSE / BSE / AMFI Master Data"]:::external
    end

    %% Connections
    Browser -- "HTTPS / REST API" --> API
    Desktop -- "Localhost API (PyInstaller binary)" --> API
    Mobile -- "Localhost API (Chaquopy embedded CPython)" --> API

    API -- "SQLAlchemy / Alembic" --> PostgreSQL
    API -- "Cache R/W" --> Redis
    
    AnalyticsService -- "Market Data Fetch" --> YFinance
    DataImportService -- "Security Master Fetch" --> ExchangeData
```

## 2. Architectural Decisions

### 2.1. Architecture Pattern: Client-Server (SPA)

We will use a **decoupled Client-Server architecture**. The frontend will be a Single Page Application (SPA) that communicates with a backend via a RESTful API.

*   **Pros:** This pattern provides excellent separation of concerns, allows for independent development and scaling of the frontend and backend, and enables a modern, responsive user experience. It also allows the same API to be used by a future mobile application.

### 2.2. Technology Stack

*   **Backend:** **Python** with **FastAPI**. Chosen for its high performance, automatic data validation with Pydantic, and excellent ecosystem for data analysis and AI.
*   **Frontend:** **JavaScript** with **React**. Chosen for its component-based architecture, which is ideal for building complex UIs like our dashboard, and its vast ecosystem of libraries.
*   **Database:** **PostgreSQL**. Chosen for its reputation for reliability, data integrity (ACID compliance), and ability to handle complex queries, all of which are critical for a financial application.

### 2.3. Deployment Strategy

The entire application will be containerized using **Docker** and orchestrated with **Docker Compose**.

*   This creates a portable, self-contained application package that can be run on any machine with Docker installed, from a local development machine to a cloud server or a Raspberry Pi.
*   The setup will consist of three primary services: `backend`, `frontend`, and `db`.
*   A reverse proxy will manage incoming traffic, directing API calls to the backend and all other requests to the frontend.
*   This strategy directly supports the requirement for flexible deployment, including local offline use and self-hosting via services like Cloudflare Tunnels.

### 2.4. Desktop Mode (Electron)

For desktop deployments, the application uses **Electron** with:
*   Frontend served from local files in a Chromium WebView.
*   Backend bundled via **PyInstaller** as a native executable.
*   **SQLite** database and **DiskCache** instead of PostgreSQL and Redis.

### 2.5. Android Mode (Experimental)

For Android deployments, the application uses:
*   **Capacitor.js** to wrap the React frontend into an Android WebView.
*   **Chaquopy** to embed the CPython interpreter and run the FastAPI backend natively on the device.
*   The backend runs as a local HTTP server on `127.0.0.1:<port>`, identical to the Electron desktop architecture.
*   **SQLite** and **DiskCache** for storage (same as desktop mode).

```