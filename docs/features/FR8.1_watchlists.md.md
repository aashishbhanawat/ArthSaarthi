# Feature Plan: Watchlists (FR8.1)

**Feature ID:** FR8.1
**Title:** Watchlists
**User Story:** As a user, I want to create and manage lists of assets that I don't own, so I can monitor their performance and make informed decisions about future investments.

---

## 1. Objective

This document outlines the implementation plan for the "Watchlists" feature. The goal is to allow users to create, manage, and monitor custom lists of financial assets.

This plan is designed to be executed by the AI assistant **Jules** in parallel with other development work. The feature is self-contained to minimize merge conflicts.

---

## 2. Database Schema Design

Two new tables are required to support this feature.

### 2.1. `watchlists` Table

This table will store the user-created watchlists.

| Column Name  | Data Type | Constraints                               | Description                           |
| ------------ | --------- | ----------------------------------------- | ------------------------------------- |
| `id`         | `UUID`    | `PRIMARY KEY`                             | Unique identifier for the watchlist.  |
| `name`       | `String`  | `NOT NULL`                                | User-defined name for the watchlist.  |
| `user_id`    | `UUID`    | `FOREIGN KEY (users.id)`, `NOT NULL`      | Links the watchlist to a user.        |
| `created_at` | `TIMESTAMP` | `NOT NULL`, `SERVER_DEFAULT(now())`       | Timestamp of when the list was created. |

### 2.2. `watchlist_items` Table

This table will link assets to a specific watchlist, creating a many-to-many relationship.

| Column Name    | Data Type | Constraints                               | Description                               |
| -------------- | --------- | ----------------------------------------- | ----------------------------------------- |
| `id`           | `UUID`    | `PRIMARY KEY`                             | Unique identifier for the watchlist item. |
| `watchlist_id` | `UUID`    | `FOREIGN KEY (watchlists.id)`, `NOT NULL` | The watchlist this item belongs to.       |
| `asset_id`     | `UUID`    | `FOREIGN KEY (assets.id)`, `NOT NULL`     | The asset being watched.                  |
| `user_id`      | `UUID`    | `FOREIGN KEY (users.id)`, `NOT NULL`      | The owner of the item.                    |

**Constraint:** A `UNIQUE` constraint should be added on (`watchlist_id`, `asset_id`) to prevent adding the same asset to the same watchlist more than once.

---

## 3. Backend Implementation Plan

### 3.1. New Files to Create

*   **Models:** `backend/app/models/watchlist.py`
*   **Schemas:** `backend/app/schemas/watchlist.py`
*   **CRUD:** `backend/app/crud/crud_watchlist.py`
*   **API Endpoint:** `backend/app/api/v1/endpoints/watchlists.py`
*   **Tests:** `backend/app/tests/api/v1/test_watchlists.py`

### 3.2. API Endpoints

A new router will be created at `/api/v1/watchlists`.

*   `POST /`: Create a new watchlist.
*   `GET /`: Get all watchlists for the current user.
*   `GET /{watchlist_id}`: Get details for a single watchlist, including its assets.
*   `PUT /{watchlist_id}`: Update a watchlist's name.
*   `DELETE /{watchlist_id}`: Delete a watchlist and its associated items.
*   `POST /{watchlist_id}/items`: Add an asset to the watchlist.
*   `DELETE /{watchlist_id}/items/{item_id}`: Remove an asset from the watchlist.

---

## 4. Frontend Implementation Plan

### 4.1. New Files to Create

*   **Page:** `frontend/src/pages/WatchlistsPage.tsx`
*   **Components:**
    *   `frontend/src/components/Watchlists/WatchlistSelector.tsx`
    *   `frontend/src/components/Watchlists/WatchlistTable.tsx`
    *   `frontend/src/components/modals/WatchlistFormModal.tsx`
    *   `frontend/src/components/modals/AddAssetToWatchlistModal.tsx`
*   **Data Layer:**
    *   `frontend/src/hooks/useWatchlists.ts`
    *   `frontend/src/services/watchlistApi.ts`
*   **Types:** `frontend/src/types/watchlist.ts`
*   **Tests:** Corresponding test files in `frontend/src/__tests__/`.

### 4.2. User Flow & UI Components

1.  **Watchlists Page (`/watchlists`):** A new link in the main navigation will lead to this page.
2.  **`WatchlistSelector.tsx`:** A component (e.g., a sidebar or dropdown) to list all created watchlists and allow the user to select one. It will also have controls to create a new watchlist or edit/delete the selected one.
3.  **`WatchlistTable.tsx`:** The main component on the page. It will display a table of all assets in the currently selected watchlist. The table should show key metrics for each asset (e.g., Ticker, Current Price, Day's Change).
4.  **`WatchlistFormModal.tsx`:** A modal for creating or renaming a watchlist.
5.  **`AddAssetToWatchlistModal.tsx`:** A modal that allows the user to search for and add an existing asset to the current watchlist.

---

## 5. Phased Implementation Strategy

This feature should be implemented in phases to ensure manageable pull requests.

1.  **Phase 1: Backend Foundation.**
    *   Create the `watchlists` and `watchlist_items` database models and generate the Alembic migration.
    *   Implement the Pydantic schemas.
    *   Implement the basic backend CRUD operations and API endpoints for creating, reading, updating, and deleting the watchlists themselves (not the items yet).
    *   Write corresponding backend tests.

2.  **Phase 2: Frontend Watchlist Management.**
    *   Implement the `WatchlistsPage` and the `WatchlistSelector` component.
    *   Implement the `WatchlistFormModal` to create and edit watchlists.
    *   Users should be able to create, rename, and delete watchlists.

3.  **Phase 3: Full-Stack Item Management.**
    *   Implement the backend API endpoints for adding and removing assets from a watchlist.
    *   Implement the frontend `AddAssetToWatchlistModal` and the logic in the `WatchlistTable` to remove items.
    *   Write corresponding full-stack tests.

4.  **Phase 4: Real-time Data Display.**
    *   Integrate the `WatchlistTable` with the financial data service to display live market data for the assets in the list.
