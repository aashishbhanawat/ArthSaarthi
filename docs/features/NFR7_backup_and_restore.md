# NFR7: User Data Backup and Restore

## 1. Introduction

This document outlines the plan for implementing a user-facing backup and restore mechanism. As users invest time manually entering their financial data, it is critical to provide them with a way to safeguard this data. This feature will allow users to export their entire portfolio to a local file and restore it later, providing peace of mind and ensuring data portability across application versions.

**Related NFRs**: NFR5 (Reliability & Data Integrity)

## 2. Problem Description

Currently, all user data resides solely within the application's database. There is no mechanism for a user to create an external backup of their information. This presents two significant risks:

1.  **Risk of Data Loss:** In the event of data corruption or accidental deletion, users have no way to recover their manually entered transactions and portfolio structure.
2.  **Upgrade Friction:** Future major releases may introduce breaking changes to the database schema. Without a portable backup format, users would be forced to re-enter all their data manually after an upgrade, which is a significant barrier to adoption.

## 3. Proposed Solution

A full-stack feature will be implemented to provide a simple, robust, and user-controlled backup and restore workflow.

### 3.1. Core Principle: Resilient JSON Format

The backup format will be a structured, versioned, and human-readable **JSON file**. This approach is intentionally chosen over a raw SQL dump for its resilience. A JSON backup can be processed by the application's business logic during a restore, allowing it to adapt to future database schema changes gracefully.

### 3.2. Backend Implementation

1.  **Backup Endpoint (`GET /api/v1/users/me/backup`)**
    *   **Authentication:** Protected route, accessible only to the authenticated user.
    *   **Logic:**
        1.  Query the database for all data owned by the user (portfolios, transactions, goals, watchlists, etc.).
        2.  Serialize this data into a well-defined JSON structure, including a metadata block with a version number and export date.
        3.  Return the JSON object as a file download (e.g., `arthsaarthi_backup_{timestamp}.json`).

2.  **Restore Endpoint (`POST /api/v1/users/me/restore`)**
    *   **Authentication:** Protected route.
    *   **Input:** Accepts a `multipart/form-data` request with a single JSON file.
    *   **Logic (Transactional & Safe):**
        1.  **Validation:** Validate the uploaded JSON file's structure and version.
        2.  **Deletion:** Within a single database transaction, delete all existing financial data for the user.
        3.  **Re-Creation:** Iterate through the data in the JSON file and use the application's existing CRUD services (e.g., `crud.portfolio.create`, `crud.transaction.create`) to re-insert the data. This ensures all business logic and validation from the current application version are applied.
        4.  **Commit/Rollback:** If any error occurs, the entire transaction is rolled back, leaving the user's original data intact.

### 3.3. Frontend Implementation
1.  **New Page (`/settings/backup`)**: A new page will be created under the user's settings area.
2.  **Backup Component**: A simple card with a "Download Backup" button that triggers the `GET` request to the backup endpoint.
3.  **Restore Component**: A card with a file input (`<input type="file" accept=".json">`) and a "Restore from Backup" button.
4.  **High-Friction Confirmation Modal**: Clicking the restore button will trigger a confirmation modal. The user must be explicitly warned that their current data will be deleted and will be required to type a confirmation word (e.g., `DELETE`) to enable the final restore button. This prevents accidental data loss.

### 3.4. Backup File JSON Format

The backup file will be a single JSON object with two root keys: `metadata` and `data`. All monetary values are stored as numbers, and all dates are stored as `YYYY-MM-DD` strings.

```json
{
  "metadata": {
    "version": "1.1",
    "export_date": "YYYY-MM-DDTHH:MM:SSZ"
  },
  "data": {
    "portfolios": [],
    "transactions": [],
    "fixed_deposits": [],
    "recurring_deposits": [],
    "ppf_accounts": [],
    "bonds": [],
    "goals": [],
    "watchlists": []
  }
}
```

*   **`metadata.version`**: A version string for the backup format itself. This will allow future versions of the application to correctly handle older backup files.
*   **`metadata.export_date`**: An ISO 8601 timestamp indicating when the backup was created.
*   **`data`**: An object containing arrays of all user-specific financial data. Relationships between entities (e.g., a transaction belonging to a portfolio) will be managed using human-readable names (e.g., `portfolio_name`).

#### 3.4.1. `transactions` Schema

The `transactions` array is a polymorphic list where the structure depends on the `transaction_type`. This includes `BUY`, `SELL`, `PPF_CONTRIBUTION`, and all corporate actions.

**Example `BUY`/`SELL` (Stock/MF):**
```json
{
  "portfolio_name": "Retirement Fund",
  "ticker_symbol": "RELIANCE",
  "isin": "INE002A01018",
  "transaction_type": "BUY",
  "quantity": 10,
  "price_per_unit": 2500.00,
  "transaction_date": "2023-01-15",
  "fees": 10.50
}
```

**Example `DIVIDEND`/`COUPON`:**
For cash income events, `quantity` is repurposed to store the total cash amount, and `price_per_unit` is set to `1`.

**Example `SPLIT`/`BONUS`:**
For stock splits and bonuses, `quantity` and `price_per_unit` are repurposed to store the ratio (e.g., new shares vs. old shares).

**Example `PPF_CONTRIBUTION`:**
```json
{
  "ppf_account_number": "PPF-SBI-Main",
  "transaction_type": "PPF_CONTRIBUTION",
  "amount": 50000,
  "transaction_date": "2023-04-10"
}
```

#### 3.4.2. Other Data Schemas

**`portfolios`**
```json
{
  "name": "Retirement Fund",
  "description": "Long term investments."
}
```

**`fixed_deposits`**
```json
{
  "account_number": "FD-001",
  "institution": "HDFC Bank",
  "principal": 100000,
  "interest_rate": 6.5,
  "start_date": "2023-05-01",
  "maturity_date": "2024-05-01",
  "compounding_frequency": "QUARTERLY",
  "payout_type": "CUMULATIVE"
}
```

**`recurring_deposits`**
```json
{
  "account_number": "RD-001",
  "institution": "ICICI Bank",
  "monthly_installment": 5000,
  "interest_rate": 6.2,
  "start_date": "2023-06-01",
  "tenure_months": 12
}
```

**`ppf_accounts`**
```json
{
  "account_number": "PPF-SBI-Main",
  "institution": "State Bank of India",
  "opening_date": "2020-04-01"
}
```

**`bonds`**
This array stores the definitions of the bond assets themselves. Their transactions are stored in the main `transactions` array.
```json
{
  "name": "NHAI N2 8.3% 2027",
  "isin": "INE906B07CB9",
  "bond_type": "CORPORATE",
  "coupon_rate": 8.30,
  "face_value": 1000,
  "maturity_date": "2027-01-25"
}
```
**`goals`**
```json
{
  "name": "Buy a Car",
  "target_amount": 1000000,
  "target_date": "2026-12-31",
  "linked_portfolios": ["Retirement Fund"]
}
```

**`watchlists`**
```json
{
  "name": "Tech Stocks",
  "description": "Watchlist for tech sector stocks.",
  "items": ["TCS", "INFY"]
}
```

### 3.5. Restore Logic Order

To ensure data integrity and correctly re-establish relationships, the restore process must create entities in a specific order. The backend will process the `data` object from the JSON file as follows:

1.  **Create Independent Entities:** First, create all items that do not depend on others.
    *   `portfolios`
    *   `bonds` (creates the bond as an asset)
    *   `watchlists`
    *   `ppf_accounts`
2.  **Create Dependent Entities:** Next, create items that link to the entities from step 1.
    *   `fixed_deposits` and `recurring_deposits` will be created.
    *   `transactions` (all types) will be created. For each transaction, the system will first find or create the associated asset (matching by `isin` or `ticker_symbol`), then create the transaction and link it to the correct portfolio by `portfolio_name`. This ensures that `STOCK` and `MUTUAL_FUND` assets are created on-the-fly during the restore process.
    *   `goals` will be created and linked to portfolios.
    *   `watchlist_items` will be created and added to their respective watchlists.


## 4. Task Prioritization

This is a high-priority feature for the next major release, as it directly impacts user trust and data safety.

## 5. Status

**Implemented:** 2025-11-20
- Backend endpoints and service logic created.
- Frontend UI integrated into Profile page.
- Automated tests and manual verification completed.
