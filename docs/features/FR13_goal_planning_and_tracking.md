# Feature Plan: Goal Planning & Tracking (FR13)

**Feature ID:** FR13
**Title:** Goal Planning & Tracking
**User Story:** As a user, I want to define my financial goals, link my investments to them, and track my progress over time, so that I can stay motivated and make informed decisions to reach my financial targets.

---

## 1. Objective

This document outlines the implementation plan for the "Goal Planning & Tracking" feature. The goal is to provide users with a comprehensive toolset to define, link, and monitor their financial goals within the ArthSaarthi application.

This plan is designed to be executed by the AI assistant **Jules** in parallel with other development work. The feature is self-contained to minimize merge conflicts.

---

## 2. Database Schema Design

Two new tables are required to support this feature.

### 2.1. `goals` Table

This table will store the core details of each financial goal defined by a user.

| Column Name     | Data Type | Constraints                               | Description                               |
| --------------- | --------- | ----------------------------------------- | ----------------------------------------- |
| `id`            | `UUID`    | `PRIMARY KEY`                             | Unique identifier for the goal.           |
| `name`          | `String`  | `NOT NULL`                                | User-defined name for the goal.           |
| `target_amount` | `Numeric` | `NOT NULL`                                | The monetary target for the goal.         |
| `target_date`   | `Date`    | `NOT NULL`                                | The date by which the goal should be met. |
| `user_id`       | `UUID`    | `FOREIGN KEY (users.id)`, `NOT NULL`      | Links the goal to a user.                 |
| `created_at`    | `TIMESTAMP` | `NOT NULL`, `SERVER_DEFAULT(now())`       | Timestamp of when the goal was created.   |

### 2.2. `goal_links` Table

This table will create a many-to-many relationship, linking assets or entire portfolios to specific goals.

| Column Name    | Data Type | Constraints                               | Description                                     |
| -------------- | --------- | ----------------------------------------- | ----------------------------------------------- |
| `id`           | `UUID`    | `PRIMARY KEY`                             | Unique identifier for the link.                 |
| `goal_id`      | `UUID`    | `FOREIGN KEY (goals.id)`, `NOT NULL`      | The goal being linked to.                       |
| `portfolio_id` | `UUID`    | `FOREIGN KEY (portfolios.id)`, `NULLABLE` | The portfolio being linked.                     |
| `asset_id`     | `UUID`    | `FOREIGN KEY (assets.id)`, `NULLABLE`     | The specific asset being linked.                |
| `user_id`      | `UUID`    | `FOREIGN KEY (users.id)`, `NOT NULL`      | The owner of the link.                          |

**Constraint:** A `CHECK` constraint must be added to ensure that for each row, either `portfolio_id` is `NOT NULL` or `asset_id` is `NOT NULL`, but not both. This enforces that a link is tied to either a portfolio or an asset, but not a mix.

---

## 3. Backend Implementation Plan

### 3.1. New Files to Create

*   **Models:** `backend/app/models/goal.py`
*   **Schemas:** `backend/app/schemas/goal.py`
*   **CRUD:** `backend/app/crud/crud_goal.py`
*   **API Endpoint:** `backend/app/api/v1/endpoints/goals.py`
*   **Tests:** `backend/app/tests/api/v1/test_goals.py`

### 3.2. API Endpoints

A new router will be created at `/api/v1/goals`.

*   `POST /`: Create a new goal.
*   `GET /`: Get all goals for the current user.
*   `GET /{goal_id}`: Get details for a single goal, including linked assets/portfolios and progress.
*   `PUT /{goal_id}`: Update a goal's details (name, target amount, target date).
*   `DELETE /{goal_id}`: Delete a goal and its associated links.
*   `POST /{goal_id}/links`: Link a portfolio or an asset to the goal.
*   `DELETE /{goal_id}/links/{link_id}`: Unlink a portfolio or asset from the goal.

### 3.3. Business Logic (`crud_goal.py`)

*   Implement standard CRUD operations for goals and links.
*   Implement the logic for **FR13.4: Projection & Analysis**. This will involve:
    *   Fetching the current value of all linked assets/portfolios.
    *   Calculating the current progress towards the `target_amount`.
    *   (Advanced) Projecting future value based on historical performance (e.g., using XIRR of the linked assets).

---

## 4. Frontend Implementation Plan

### 4.1. New Files to Create

*   **Page:** `frontend/src/pages/GoalsPage.tsx`
*   **Components:**
    *   `frontend/src/components/Goals/GoalCard.tsx`
    *   `frontend/src/components/Goals/GoalDetailView.tsx`
    *   `frontend/src/components/modals/GoalFormModal.tsx`
    *   `frontend/src/components/modals/AssetLinkModal.tsx`
*   **Data Layer:**
    *   `frontend/src/hooks/useGoals.ts`
    *   `frontend/src/services/goalApi.ts`
*   **Types:** `frontend/src/types/goal.ts`
*   **Tests:** Corresponding test files in `frontend/src/__tests__/`.

### 4.2. User Flow & UI Components

1.  **Goals Page (`/goals`):** A new link in the main navigation will lead to this page. It will display a list of all user-defined goals using the `GoalCard` component. A "Create New Goal" button will be present.
2.  **`GoalCard.tsx`:** This component will display a summary of a single goal, including its name, target amount, and a progress bar showing current completion.
3.  **`GoalFormModal.tsx`:** A modal for creating or editing a goal (name, target amount, target date).
4.  **`GoalDetailView.tsx`:** (Could be a separate page or an expandable section) This view will show detailed analytics for a single goal, including projection charts and a list of linked assets/portfolios.
5.  **`AssetLinkModal.tsx`:** From the detail view, a user can open this modal to search for and link their existing portfolios or individual assets to the goal.

---

## 5. Phased Implementation Strategy

To ensure manageable and testable pull requests, this feature should be implemented in phases:

1.  **Phase 1: Backend Foundation.**
    *   Create the database models (`goals`, `goal_links`) and generate the Alembic migration.
    *   Implement the Pydantic schemas.
    *   Implement the basic backend CRUD operations and API endpoints for goals (Create, Read, Update, Delete).
    *   Write corresponding backend tests.

2.  **Phase 2: Frontend Goal Management.**
    *   Implement the frontend `GoalsPage` to list goals.
    *   Implement the `GoalFormModal` to create and edit goals.
    *   Write corresponding frontend tests.

3.  **Phase 3: Asset Linking.**
    *   Implement the backend API endpoints for linking/unlinking assets and portfolios.
    *   Implement the frontend `AssetLinkModal` and the UI for managing links.
    *   Write corresponding full-stack tests.

4.  **Phase 4: Analytics & Projections.**
    *   Implement the backend business logic for calculating progress and projections.
    *   Implement the frontend `GoalDetailView` to display these analytics with charts.
    *   Write corresponding tests for the calculation logic.

This phased approach will allow for iterative development and testing, making the process more robust and easier to manage.

