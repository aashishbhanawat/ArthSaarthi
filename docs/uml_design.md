# Unified UML Design Documentation

This document serves as the single source of truth for the technical design and data models of the ArthSaarthi Personal Portfolio Management System.

---

## 1. System Architecture

The following diagram illustrates the high-level decoupled architecture supporting Server (Docker), Desktop (Electron), and Mobile (Android) deployments.

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

---

## 2. Entity-Relationship Diagram (ERD)

The core data model follows a strict multi-tenant ownership structure via the `user_id` foreign key.

```mermaid
erDiagram
    Users ||--o{ Portfolios : owns
    Users ||--o{ Transactions : initiates
    Users ||--o{ AuditLogs : generates
    Users ||--o{ Goals : sets
    Users ||--o{ Watchlists : maintains
    Users ||--o{ FixedDeposits : owns
    Users ||--o{ RecurringDeposits : owns
    Users ||--o{ ImportSessions : runs

    Portfolios ||--o{ Transactions : contains
    Portfolios ||--o{ DailyPortfolioSnapshots : tracks
    Portfolios ||--o{ FixedDeposits : linked_to
    Portfolios ||--o{ RecurringDeposits : linked_to
    Portfolios ||--o{ GoalLinks : linked_via

    Assets ||--o{ Transactions : involves
    Assets ||--o{ Bonds : extends
    Assets ||--o{ AssetAliases : has
    Assets ||--o{ WatchlistItems : in
    Assets ||--o{ GoalLinks : linked_via

    Transactions ||--o{ TransactionLinks : sell_side
    Transactions ||--o{ TransactionLinks : buy_side

    ImportSessions ||--o{ ParsedTransactions : stages

    Goals ||--o{ GoalLinks : defines

    Users {
        uuid id PK
        string email UK
        string hashed_password
    }
    Portfolios {
        uuid id PK
        string name
        uuid user_id FK
    }
    Assets {
        uuid id PK
        string ticker_symbol UK
        string asset_type
    }
    Transactions {
        uuid id PK
        string transaction_type
        numeric quantity
        numeric price_per_unit
        uuid portfolio_id FK
        uuid asset_id FK
    }
```

---

## 3. Backend Class Architecture

The backend implements the **Repository Pattern** via SQLAlchemy CRUD classes, decoupled from the Pydantic-validated FastAPI routers.

```mermaid
classDiagram
    class BaseRouter {
        <<FastAPI>>
        +get_db()
        +get_current_user()
    }
    class CRUDBase {
        <<SQLAlchemy>>
        +get()
        +get_multi()
        +create()
        +update()
    }
    class PortfolioService {
        +calculate_valuation()
        +get_xirr()
    }
    
    BaseRouter <|-- PortfolioRouter
    CRUDBase <|-- CRUDPortfolio
    PortfolioRouter --> CRUDPortfolio : uses
    PortfolioRouter --> PortfolioService : uses
    CRUDPortfolio --> PortfolioModel : manages
```

---

## 4. Key Sequence Diagrams

### 4.1. Adding a Transaction

```mermaid
sequenceDiagram
    actor User
    participant Frontend as React Frontend
    participant ReactQuery as React Query / API Client
    participant Router as FastAPI Router
    participant CRUD as SQLAlchemy CRUD
    participant DB as Database

    User->>Frontend: Clicks "Add Transaction"
    Frontend->>Frontend: Opens Modal, validates input
    User->>Frontend: Submits Form
    Frontend->>ReactQuery: mutate(portfolioId, transactionData)
    ReactQuery->>Router: POST /api/v1/portfolios/{id}/transactions/
    
    activate Router
    Router->>Router: Pydantic Validation (TransactionCreate)
    Router->>CRUD: create_with_portfolio(db, obj_in, user_id)
    
    activate CRUD
    CRUD->>CRUD: Validate user owns portfolio
    CRUD->>DB: INSERT INTO transactions ...
    DB-->>CRUD: Return new row data
    CRUD-->>Router: Return Transaction Model
    deactivate CRUD
    
    Router-->>ReactQuery: 201 Created (JSON Response)
    deactivate Router
    
    ReactQuery->>Frontend: onSuccess trigger
    Frontend->>ReactQuery: Invalidate ['portfolios'] cache
    ReactQuery->>Router: GET /api/v1/portfolios (Refetch data)
    Frontend->>User: Close modal, show updated UI
```

### 4.2. Data Import Pipeline

```mermaid
sequenceDiagram
    actor User
    participant Frontend as React Frontend
    participant Parser as File Parsers (Python)
    participant Staging as Local File System (.parquet)
    participant DB as Database

    User->>Frontend: Uploads CSV & Submits
    Frontend->>Parser: POST /api/v1/import-sessions/ (Multipart Form)
    activate Parser
    Parser->>Parser: Validate File, Select Parser Engine
    Parser->>Parser: Parse Raw Data into Pydantic Models
    Parser->>Staging: Save intermediate data as .parquet file
    Parser->>DB: Create ImportSession record in database
    Parser-->>Frontend: 200 OK (Return session ID)
    deactivate Parser
    
    User->>Frontend: Selects rows & Clicks "Commit"
    Frontend->>DB: POST /api/v1/import-sessions/{id}/commit
    activate DB
    DB->>DB: BEGIN TRANSACTION
    DB->>DB: INSERT all selected Transactions
    DB->>DB: Update ImportSession status = 'COMPLETED'
    DB->>DB: COMMIT (Atomic)
    DB-->>Frontend: 200 OK
    deactivate DB
```
