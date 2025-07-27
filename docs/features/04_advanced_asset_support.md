# Feature Plan: Advanced Asset Support

This document outlines the development plan for adding support for advanced asset classes, as specified in the product backlog.

**Related Requirements:** FR4.3

---

## 1. Objective

To extend the application's capabilities to allow users to track a wider variety of financial instruments beyond publicly traded securities. This includes fixed-income products, government savings schemes, and employee stock plans.

---

## 2. Backend Development Plan

This plan was created by the **Backend Developer** and **Database Administrator**.

### 2.1. Database Schema Changes

Supporting these new asset types will require significant schema extensions. We will introduce new tables to handle the unique attributes of each asset class, linked to the main `assets` table.

**New Table: `fixed_income_details`**
*   **Purpose:** To store details for FDs, RDs, and Bonds.
*   **Columns:**
    *   `id`: Primary Key
    *   `asset_id`: Foreign Key to `assets.id`
    *   `principal_amount`: Numeric
    *   `interest_rate`: Numeric (e.g., 7.5 for 7.5%)
    *   `maturity_date`: Date
    *   `compounding_frequency`: String (e.g., 'QUARTERLY', 'ANNUALLY')

**New Table: `employee_stock_plan_details`**
*   **Purpose:** To store details for RSUs and ESPPs.
*   **Columns:**
    *   `id`: Primary Key
    *   `asset_id`: Foreign Key to `assets.id`
    *   `grant_id`: String
    *   `grant_date`: Date
    *   `vesting_schedule`: JSONB (to store vesting dates and quantities)

**Changes to `assets` table:**
*   The `asset_type` column will be used to determine which details table to join with. New types will include 'FIXED_DEPOSIT', 'BOND', 'RSU', 'ESPP', 'PPF', 'NPS'.

### 2.2. API Endpoints

The existing API structure will be extended.

*   `POST /api/v1/assets/fixed-income`: A new endpoint to create a fixed-income asset (FD, Bond) and its associated details.
*   `POST /api/v1/assets/employee-plan`: A new endpoint to create an employee stock plan asset (RSU, ESPP).
*   The existing `POST /api/v1/portfolios/{portfolio_id}/transactions/` endpoint will be used for subsequent transactions related to these assets (e.g., interest payments, stock vesting).

### 2.3. Backend Logic

*   New CRUD modules (`crud_fixed_income.py`, `crud_employee_plan.py`) will be created to handle the business logic for these new asset types.
*   The dashboard calculation logic in `crud_dashboard.py` will be updated to correctly value these new asset types.

---

## 3. Frontend Development Plan

This plan was created by the **Frontend Developer** and **UI/UX Designer**.

### 3.1. UI/UX Flow: "Add New Asset" Modal

The "Add Transaction" modal will be enhanced to become an "Add New..." modal, guiding the user through the creation process.

1.  **Step 1: Select Category:** A new initial step in the modal will ask the user to select the asset category: `[Market-Traded]`, `[Fixed Income]`, `[Government Scheme]`, `[Employee Plan]`.
2.  **Step 2: Dynamic Forms:** Based on the category selected, a specific form will be rendered.
    *   **Fixed Income Form:** Will include fields for Principal, Interest Rate, Maturity Date, etc.
    *   **Employee Plan Form:** Will include fields for Grant ID, Vesting Schedule, etc.

### 3.2. State Management & API Integration

*   New React Query mutations will be created in `usePortfolios.ts` (or a new `useAssets.ts`) to handle the creation of these new asset types via the new API endpoints.
*   The `AddTransactionModal` will be refactored into a more generic `AssetCreationModal` to handle the multi-step flow.

### 3.3. Display Components

*   The `TransactionList` and portfolio detail views will be updated to correctly display the unique attributes of these new asset types.