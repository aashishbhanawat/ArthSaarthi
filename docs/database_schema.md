# Database Schema Documentation

This document explicitly outlines the constraints, defaults, and relationships for every table in the ArthSaarthi schema (as of version 1.5.0). 

> **Note:** For the visual **Entity-Relationship Diagram (ERD)**, please refer to the unified `[uml_design.md](./uml_design.md)`.

## 1. Core User & Portfolio Models

### `users`
Stores user credentials and profile information for authentication and multi-tenant data ownership.

| Column            | Type                | Constraints                               |
| ----------------- | ------------------- | ----------------------------------------- |
| `id`              | `UUID`              | `PRIMARY KEY`                             |
| `full_name`       | `String`            | `NOT NULL`                                |
| `email`           | `String`            | `UNIQUE`, `NOT NULL`, `INDEX`             |
| `hashed_password` | `String`            | `NOT NULL`                                |
| `is_admin`        | `Boolean`           | `DEFAULT FALSE`, `NOT NULL`               |
| `is_active`       | `Boolean`           | `DEFAULT TRUE`                            |
| `created_at`      | `TIMESTAMP(tz)`     | `NOT NULL`, `SERVER_DEFAULT(now())`       |

### `portfolios`
Acts as containers for a user's investments and history.

| Column        | Type                | Constraints                               |
| ------------- | ------------------- | ----------------------------------------- |
| `id`          | `UUID`              | `PRIMARY KEY`                             |
| `name`        | `String`            | `NOT NULL`                                |
| `description` | `String`            | `NULLABLE`                                |
| `user_id`     | `UUID`              | `FOREIGN KEY (users.id)`, `NOT NULL`      |

## 2. Asset Master Data Models

### `assets`
The master list of all unique financial instruments tracked in the system.

| Column             | Type        | Constraints                               |
| ------------------ | ----------- | ----------------------------------------- |
| `id`               | `UUID`      | `PRIMARY KEY`                             |
| `ticker_symbol`    | `String`    | `UNIQUE`, `NOT NULL`, `INDEX`             |
| `name`             | `String`    | `NOT NULL`                                |
| `asset_type`       | `String`    | `NOT NULL` (e.g., 'STOCK', 'MF', 'RSU')   |
| `currency`         | `String`    | `NOT NULL`, `DEFAULT 'INR'`               |
| `isin`             | `String`    | `UNIQUE`, `NULLABLE`, `INDEX`             |
| `exchange`         | `String`    | `NULLABLE` (e.g., 'NSE')                  |
| `sector`           | `String`    | `NULLABLE`                                |
| `investment_style` | `String`    | `NULLABLE` (e.g., 'Large Cap Growth')     |
| `fmv_2018`         | `Numeric`   | `NULLABLE` (For Grandfathering Capital Gains)|

### `bonds`
Polymorphic extension of the `assets` table for fixed-income instruments.

| Column               | Type        | Constraints                               |
| -------------------- | ----------- | ----------------------------------------- |
| `id`                 | `UUID`      | `PRIMARY KEY`                             |
| `asset_id`           | `UUID`      | `FOREIGN KEY (assets.id)`, `UNIQUE`       |
| `bond_type`          | `String`    | `NOT NULL` (e.g., 'Corporate', 'Government')|
| `face_value`         | `Numeric`   | `NOT NULL`                                |
| `coupon_rate`        | `Numeric`   | `NOT NULL`                                |
| `maturity_date`      | `Date`      | `NOT NULL`                                |
| `payment_frequency`  | `String`    | `NOT NULL`                                |

### `asset_aliases`
Handles mapping arbitrary broker ticker names to the canonical master asset names.

| Column      | Type        | Constraints                               |
| ----------- | ----------- | ----------------------------------------- |
| `id`        | `UUID`      | `PRIMARY KEY`                             |
| `asset_id`  | `UUID`      | `FOREIGN KEY (assets.id)`, `NOT NULL`     |
| `alias`     | `String`    | `NOT NULL`, `INDEX`                       |
| `source`    | `String`    | `NULLABLE` (e.g., 'Zerodha')              |

## 3. Transaction & Accounting Models

### `transactions`
Logs all financial actions against assets within a portfolio.

| Column             | Type           | Constraints                               |
| ------------------ | -------------- | ----------------------------------------- |
| `id`               | `UUID`         | `PRIMARY KEY`                             |
| `transaction_type` | `String`       | `NOT NULL` (e.g., 'BUY', 'SELL', 'DIVIDEND')|
| `quantity`         | `Numeric`      | `NOT NULL`                                |
| `price_per_unit`   | `Numeric`      | `NOT NULL`                                |
| `fees`             | `Numeric`      | `DEFAULT 0`                               |
| `transaction_date` | `TIMESTAMP`    | `NOT NULL`                                |
| `details`          | `JSON`         | `NULLABLE` (Stores arbitrary metadata like `fx_rate`) |
| `portfolio_id`     | `UUID`         | `FOREIGN KEY (portfolios.id)`, `NOT NULL` |
| `asset_id`         | `UUID`         | `FOREIGN KEY (assets.id)`, `NOT NULL`     |
| `user_id`          | `UUID`         | `FOREIGN KEY (users.id)`, `NOT NULL`      |

### `transaction_links`
Specific Tax Lot Identification mapping for calculating exact realized gains.

| Column               | Type      | Constraints                               |
| -------------------- | --------- | ----------------------------------------- |
| `id`                 | `UUID`    | `PRIMARY KEY`                             |
| `sell_transaction_id`| `UUID`    | `FOREIGN KEY (transactions.id)`           |
| `buy_transaction_id` | `UUID`    | `FOREIGN KEY (transactions.id)`           |
| `quantity`           | `Numeric` | `NOT NULL` (Amount of the Buy lot consumed)|

### `daily_portfolio_snapshots`
Caches historical calculations for rapid dashboard rendering.

| Column             | Type        | Constraints                               |
| ------------------ | ----------- | ----------------------------------------- |
| `id`               | `UUID`      | `PRIMARY KEY`                             |
| `portfolio_id`     | `UUID`      | `FOREIGN KEY (portfolios.id)`, `NOT NULL` |
| `snapshot_date`    | `Date`      | `NOT NULL`                                |
| `total_value`      | `Numeric`   | `NOT NULL`                                |
| `holdings_snapshot`| `JSON`      | `NULLABLE`                                |
| `Unique Constraint`|             | `(portfolio_id, snapshot_date)`           |

## 4. Alternative Investments

### `fixed_deposits`
| Column                  | Type      | Constraints                               |
| ----------------------- | --------- | ----------------------------------------- |
| `principal_amount`      | `Numeric` | `NOT NULL`                                |
| `interest_rate`         | `Numeric` | `NOT NULL`                                |
| `compounding_frequency` | `String`  | `DEFAULT 'Annually'`                      |
| `interest_payout`       | `String`  | `DEFAULT 'Cumulative'`                    |
| *+ portfolio_id, user_id*| UUID      | Foreign Keys                              |

### `recurring_deposits`
| Column                  | Type      | Constraints                               |
| ----------------------- | --------- | ----------------------------------------- |
| `monthly_installment`   | `Numeric` | `NOT NULL`                                |
| `interest_rate`         | `Numeric` | `NOT NULL`                                |
| `tenure_months`         | `Integer` | `NOT NULL`                                |
| *+ portfolio_id, user_id*| UUID      | Foreign Keys                              |

## 5. Automated Data Import System

### `import_sessions`
Tracks the upload and processing state of bulk data imports.

| Column         | Type        | Constraints                               |
| -------------- | ----------- | ----------------------------------------- |
| `file_name`    | `String`    | `NOT NULL`                                |
| `status`       | `String`    | `DEFAULT 'UPLOADED'` (UPLOADED, PARSED, COMPLETED)|
| `error_message`| `String`    | `NULLABLE`                                |
| *+ portfolio_id, user_id*| UUID| Foreign Keys                              |

### `parsed_transactions`
Temporary staging table storing parsed CSV lines before user commits them.

| Column         | Type        | Constraints                               |
| -------------- | ----------- | ----------------------------------------- |
| `session_id`   | `UUID`      | `FOREIGN KEY (import_sessions.id)`        |
| `row_number`   | `Integer`   | `NOT NULL`                                |
| `data`         | `JSON`      | `NOT NULL` (Parsed Python Dict Dump)      |
| `is_selected`  | `Boolean`   | `DEFAULT TRUE`                            |

## 6. Miscellaneous

### `audit_logs`
Immutable ledger of security-sensitive events.

| Column         | Type        | Constraints                               |
| -------------- | ----------- | ----------------------------------------- |
| `event_type`   | `String`    | `NOT NULL` (e.g., 'ADMIN_CREATED')        |
| `details`      | `JSON`      | `NULLABLE`                                |
| `ip_address`   | `String`    | `NULLABLE`                                |
| `timestamp`    | `TIMESTAMP` | `SERVER_DEFAULT(now())`                   |
| *+ user_id*    | UUID        | Foreign Key                               |

### `goals` & `goal_links`
*   **goals**: `target_amount` (Numeric), `target_date` (Date).
*   **goal_links**: Polymorphic mapping table linking a specific `goal_id` to either a `portfolio_id` OR an `asset_id`.

### `watchlists` & `watchlist_items`
*   **watchlists**: Name and `user_id`.
*   **watchlist_items**: M2M associative table linking `watchlist_id` to `asset_id`.

## 7. Tax Readiness & Income Ledger (v1.4.0)

*   **`income_sources` & `income_entries`**: Stores user income sources and entry records with AES-256 encrypted fields (`EncryptedString`) for gross, TDS, net, salary breakdown (Basic, DA, HRA, Rent Paid), and notes.
*   **`tax_deductions`**: Tracks Chapter VI-A deductions (80C, 80D, 80CCD(1B), 80TTA/80TTB) with encrypted titles, amounts, and proof notes.
*   **`capital_loss_ledgers`**: Tracks carried-forward STCL and LTCL balances by financial year for Section 70/71/74 set-off.

## 8. Infrastructure, Automation & Research Intelligence (v1.5.0)

### `broker_credentials`
Stores encrypted API credentials for direct broker integrations (`zerodha`, `icici`).

| Column                   | Type           | Constraints                               |
| ------------------------ | -------------- | ----------------------------------------- |
| `id`                     | `UUID`         | `PRIMARY KEY`                             |
| `user_id`                | `UUID`         | `FOREIGN KEY (users.id)`, `INDEX`         |
| `provider_name`          | `String(50)`   | `NOT NULL`, `UNIQUE(user_id, provider_name)`|
| `api_key`                | `String(255)`  | `NOT NULL`                                |
| `encrypted_api_secret`   | `Text`         | `NOT NULL` (AES-256-GCM encrypted)        |
| `encrypted_access_token` | `Text`         | `NULLABLE` (AES-256-GCM encrypted)        |
| `is_active`              | `Boolean`      | `NOT NULL`, `DEFAULT TRUE`                |

### `scheduled_job_logs`
Audit trail for APScheduler background job executions (`SUCCESS`, `FAILED`, `MISSED`).

| Column                   | Type           | Constraints                               |
| ------------------------ | -------------- | ----------------------------------------- |
| `id`                     | `UUID`         | `PRIMARY KEY`                             |
| `job_id`                 | `String(100)`  | `NOT NULL`, `INDEX`                       |
| `job_name`               | `String(255)`  | `NOT NULL`                                |
| `status`                 | `String(20)`   | `NOT NULL`, `INDEX`                       |
| `started_at`             | `TIMESTAMP(tz)`| `NOT NULL`                                |
| `finished_at`            | `TIMESTAMP(tz)`| `NULLABLE`                                |
| `execution_time_seconds` | `Float`        | `NULLABLE`                                |
| `error_message`          | `Text`         | `NULLABLE`                                |

### `corporate_action_events`
Tracks automated bond coupon/maturity and stock corporate action notifications.

| Column           | Type            | Constraints                               |
| ---------------- | --------------- | ----------------------------------------- |
| `id`             | `UUID`          | `PRIMARY KEY`                             |
| `user_id`        | `UUID`          | `FOREIGN KEY (users.id)`                  |
| `portfolio_id`   | `UUID`          | `FOREIGN KEY (portfolios.id)`, `INDEX`    |
| `asset_id`       | `UUID`          | `FOREIGN KEY (assets.id)`, `INDEX`        |
| `transaction_id` | `UUID`          | `FOREIGN KEY (transactions.id)`, `NULLABLE`|
| `event_type`     | `String(50)`    | `NOT NULL`                                |
| `event_date`     | `Date`          | `NOT NULL`                                |
| `units`          | `Numeric(18,8)` | `NOT NULL`                                |
| `amount`         | `Numeric(18,8)` | `NOT NULL`                                |
| `status`         | `String(20)`    | `NOT NULL`, `DEFAULT 'NEW'`               |

### `market_news_articles`
Stores aggregated corporate announcements, broker research, and earnings concall analyses.

| Column          | Type           | Constraints                               |
| --------------- | -------------- | ----------------------------------------- |
| `id`            | `String(64)`   | `PRIMARY KEY` (SHA-256 of URL or GUID)    |
| `title`         | `String(500)`  | `NOT NULL`                                |
| `summary`       | `Text`         | `NULLABLE`                                |
| `url`           | `String(1000)` | `UNIQUE`, `NOT NULL`, `INDEX`             |
| `source`        | `String(100)`  | `NOT NULL`, `INDEX`                       |
| `category`      | `String(30)`   | `NOT NULL`, `DEFAULT 'NEWS'`, `INDEX`     |
| `published_at`  | `TIMESTAMP(tz)`| `NOT NULL`, `INDEX`                       |
| `symbols`       | `JSON`         | `NOT NULL`                                |
| `sentiment`     | `String(20)`   | `NOT NULL`, `DEFAULT 'NEUTRAL'`           |
| `metadata_json` | `JSON`         | `NULLABLE` (Stores concall AI insights)   |
