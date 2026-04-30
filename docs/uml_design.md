# UML Design Document

This document provides architectural UML diagrams for ArthSaarthi's system structure and core logic. For operational sequences, see [code_flow_guide.md](code_flow_guide.md).

## 1. System Architecture

The following diagram illustrates the high-level decoupled architecture supporting Server (Docker) and Desktop (Electron) deployments.

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
        PostgreSQL[("PostgreSQL (Server) / SQLite (Desktop)")]:::database
        Redis[("Redis (Server) / DiskCache (Desktop)")]:::database
    end

    subgraph "External Integrations"
        direction TB
        YFinance["yfinance API"]:::external
        ExchangeData["NSE / BSE / AMFI Master Data"]:::external
    end

    Browser -- "HTTPS / REST API" --> API
    Desktop -- "Localhost API (PyInstaller binary)" --> API

    API -- "SQLAlchemy / Alembic" --> PostgreSQL
    API -- "Cache R/W" --> Redis

    AnalyticsService -- "Market Data Fetch" --> YFinance
    DataImportService -- "Security Master Fetch" --> ExchangeData
```

## 2. Core Domain Class Diagram

Defines the logical relationships between the primary entities in the system.

```mermaid
classDiagram
    class User {
        +UUID id
        +String email
        +String hashed_password
        +Role role
    }
    class Portfolio {
        +UUID id
        +String name
        +UUID user_id
        +calculate_valuation()
    }
    class Asset {
        +UUID id
        +String ticker_symbol
        +AssetType asset_type
        +String isin
        +fetch_latest_price()
    }
    class Transaction {
        +UUID id
        +String transaction_type
        +Date date
        +Numeric quantity
        +Numeric price_per_unit
        +UUID portfolio_id
        +UUID asset_id
    }
    class Goal {
        +UUID id
        +Float target_amount
        +Date target_date
    }
    class Watchlist {
        +UUID id
        +String name
    }

    User "1" *-- "many" Portfolio : owns
    User "1" *-- "many" Goal : defines
    User "1" *-- "many" Watchlist : maintains
    Portfolio "1" *-- "many" Transaction : contains
    Asset "1" -- "many" Transaction : "is traded in"
    Portfolio "many" -- "many" Goal : "contributes to"
```

## 2b. Backend Class Architecture

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

## 3. Entity Lifecycle State Machines

Describes the behavioral states of complex system entities.

### A. Data Import Session
```mermaid
stateDiagram-v2
    [*] --> UPLOADED
    UPLOADED --> PARSING : Backend Processing
    PARSING --> STAGING_PREVIEW : Success
    PARSING --> FAILED : Parser/Format Error

    state STAGING_PREVIEW {
        [*] --> READY
        READY --> MAPPING_REQUIRED : Missing Ticker
        MAPPING_REQUIRED --> READY : Alias Created
    }

    STAGING_PREVIEW --> COMMITTING : User Action
    COMMITTING --> COMPLETED : DB Sync
    COMMITTING --> FAILED : Conflict Error
```

### B. Financial Goal Tracking
```mermaid
stateDiagram-v2
    [*] --> ACTIVE
    ACTIVE --> ON_TRACK : Value > Required
    ACTIVE --> OFF_TRACK : Value < Required
    ON_TRACK --> ACHIEVED : Current >= Target
    OFF_TRACK --> ON_TRACK : Top-up / Growth
    ACHIEVED --> [*]
```

### C. RSU / ESPP Award Lifecycle
```mermaid
stateDiagram-v2
    [*] --> GRANTED
    GRANTED --> VESTING : Schedule Active
    VESTING --> VESTED : Vest Event
    VESTED --> TAX_SETTLED : "Sell to Cover" / Tax Paid
    TAX_SETTLED --> READY_FOR_SALE : Added to Holdings
    READY_FOR_SALE --> SOLD : Transaction Logged
```

### D. Asset Master Seeder
```mermaid
stateDiagram-v2
    [*] --> IDLE
    IDLE --> FETCHING : Request Triggered
    FETCHING --> SEEDING : Data Parsed
    SEEDING --> UPDATED : DB Merge Complete
    SEEDING --> FAILED : API/Network Error
    UPDATED --> IDLE : Reset Rate Limit
    FAILED --> IDLE
```

## 4. Core Logic Activity Diagrams

### A. Capital Gains Processing
```mermaid
activityDiagram
    start
    :Fetch Asset Transactions;
    if (Specific ID Selected?) then (yes)
        :Match user-selected Lots;
    else (no)
        :Apply FIFO (First-In-First-Out);
    endif
    :Check Holding Period;
    if (Period > Threshold?) then (yes)
        :Calculate LTCG;
        :Apply Indexation (if Debt);
        :Apply Grandfathering (if 112A);
    else (no)
        :Calculate STCG;
    endif
    :Aggregate Realized P&L;
    stop
```

### B. Benchmark Simulation
```mermaid
activityDiagram
    start
    :Select Reference Index;
    if (Hybrid Selected?) then (yes)
        :Load Blended Weights (e.g. 50/50);
        :Fetch Multiple Index Navs;
    else (no)
        :Fetch Single Index Nav;
    endif
    :Overlay Risk-Free Baseline (if enabled);
    :Simulate Portfolio Cashflows into Benchmark;
    :Calculate Benchmark XIRR;
    stop
```

## 6. Entity-Relationship Diagram (Physical Schema)

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
