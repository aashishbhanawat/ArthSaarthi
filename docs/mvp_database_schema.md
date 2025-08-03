# MVP Database Schema

This document outlines the initial database schema required to support the features defined for the Minimum Viable Product (MVP).

## 1. `users` Table

*   **Purpose:** Stores user credentials and profile information for authentication and data ownership.
*   **Schema:**

| Column Name       | Data Type           | Constraints                               |
| ----------------- | ------------------- | ----------------------------------------- |
| `id`              | `UUID`              | `PRIMARY KEY`                             |
| `full_name`       | `String`            | `NOT NULL`                                |
| `email`           | `String`            | `UNIQUE`, `NOT NULL`, `INDEX`             |
| `hashed_password` | `String`            | `NOT NULL`                                |
| `is_admin`        | `Boolean`           | `DEFAULT FALSE`, `NOT NULL`               |
| `is_active`       | `Boolean`           | `DEFAULT TRUE`                            |
| `created_at`      | `TIMESTAMP(timezone)` | `NOT NULL`, `SERVER_DEFAULT(now())`       |

## 2. `portfolios` Table

*   **Purpose:** Acts as containers for a user's investments, often tied to a specific financial goal.
*   **Schema:**

| Column Name | Data Type           | Constraints                               |
| ----------- | ------------------- | ----------------------------------------- |
| `id`        | `UUID`              | `PRIMARY KEY`                             |
| `description`| `String`           | `NULLABLE`                                |
| `name`      | `String`            | `NOT NULL`                                |
| `user_id`   | `UUID`              | `FOREIGN KEY (users.id)`, `NOT NULL`      |
| `created_at`| `TIMESTAMP(timezone)` | `NOT NULL`, `SERVER_DEFAULT(now())`       |

## 3. `assets` Table

*   **Purpose:** Creates a master list of all unique financial instruments tracked in the system to avoid data duplication.
*   **Schema:**

| Column Name     | Data Type | Constraints                   |
| --------------- | --------- | ----------------------------- |
| `id`            | `UUID`    | `PRIMARY KEY`                 |
| `ticker_symbol` | `String`  | `UNIQUE`, `NOT NULL`, `INDEX` |
| `name`          | `String`  | `NOT NULL`                    |
| `isin`          | `String`  | `UNIQUE`, `NULLABLE`, `INDEX` |
| `asset_type`    | `String`  | `NOT NULL` (e.g., 'STOCK')    |
| `exchange`      | `String`  | `NULLABLE` (e.g., 'NSE')      |
| `currency`      | `String`  | `NOT NULL` (e.g., 'USD')      |

## 4. `transactions` Table

*   **Purpose:** Logs all financial transactions for a user's assets within a specific portfolio.
*   **Schema:**

| Column Name      | Data Type           | Constraints                               |
| ---------------- | ------------------- | ----------------------------------------- |
| `id`             | `UUID`              | `PRIMARY KEY`                             |
| `transaction_type`| `String`            | `NOT NULL` (e.g., 'BUY', 'SELL')  |
| `quantity`       | `Numeric`           | `NOT NULL`                                |
| `price_per_unit` | `Numeric`           | `NOT NULL`                                |
| `fees`           | `Numeric`           | `DEFAULT 0`                               |
| `transaction_date`| `TIMESTAMP(timezone)` | `NOT NULL`                                |
| `portfolio_id`   | `UUID`              | `FOREIGN KEY (portfolios.id)`, `NOT NULL` |
| `asset_id`       | `UUID`              | `FOREIGN KEY (assets.id)`, `NOT NULL`     |
| `user_id`        | `UUID`              | `FOREIGN KEY (users.id)`, `NOT NULL`      |

## 5. `import_sessions` Table

*   **Purpose:** Tracks the state of file uploads for automated transaction importing.
*   **Schema:**

| Column Name        | Data Type           | Constraints                               |
| ------------------ | ------------------- | ----------------------------------------- |
| `id`               | `UUID`              | `PRIMARY KEY`                             |
| `file_name`        | `String`            | `NOT NULL`                                |
| `file_path`        | `String`            | `NOT NULL`                                |
| `parsed_file_path` | `String`            | `NULLABLE`                                |
| `status`           | `String`            | `NOT NULL`, `DEFAULT 'UPLOADED'`          |
| `error_message`    | `String`            | `NULLABLE`                                |
| `user_id`          | `UUID`              | `FOREIGN KEY (users.id)`, `NOT NULL`      |
| `portfolio_id`     | `UUID`              | `FOREIGN KEY (portfolios.id)`, `NOT NULL` |
| `created_at`       | `TIMESTAMP(timezone)` | `NOT NULL`, `SERVER_DEFAULT(now())`       |

## 6. Relationships
*   A **User** can have many **Portfolios**.
*   A **Portfolio** can have many **Transactions**.
*   An **Asset** can be involved in many **Transactions**.