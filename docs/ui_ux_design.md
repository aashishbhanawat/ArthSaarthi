# UI/UX Design Document

This document outlines the user interface design and user flow for the key screens of the Personal Portfolio Management System (PMS).

The overall aesthetic will be clean, modern, and professional, using clear typography and a color palette that inspires confidence (e.g., blues, greens, and neutral grays), with a full dark mode theme available (**FR11.1**).

## 1. Initial Setup & Login Page (FR1)

### User Flow
*   **First-time user:** The backend determines no users exist. The user is presented with the "Initial Admin Setup" form. Upon completion, they are logged in and redirected to the main dashboard.
*   **Returning user:** The user is presented with the standard "Login" form. Upon successful login, they are redirected to the main dashboard.

### Wireframe Description

A single, centered card on the page that dynamically shows one of two forms.

*   **Initial Admin Setup Form:**
    *   Title: "Welcome! Create Your Admin Account"
    *   Fields: Full Name, Email Address, Password, Confirm Password
    *   Button: `Create Admin Account`
*   **Login Form:**
    *   Title: "Sign In"
    *   Fields: Email Address, Password
    *   Link: "Forgot Password?"
    *   Button: `Sign In`

```
+-------------------------------------------+
|                                           |
|      [ App Logo ]                         |
|      PMS Tracker                          |
|                                           |
|      +---------------------------------+  |
|      |  Sign In                        |  |
|      |---------------------------------|  |
|      | Email: [_____________________]  |  |
|      |                                 |  |
|      | Pass:  [_____________________]  |  |
|      |                                 |  |
|      |          [ Sign In Button ]     |  |
|      |                                 |  |
|      |        Forgot Password?         |  |
|      +---------------------------------+  |
|                                           |
+-------------------------------------------+
```

## 2. Main Dashboard (FR3)

### User Flow
The user logs in and lands here. This is their main overview page. They can see top-level numbers, view charts, and navigate to more detailed pages. They can click the "Privacy Mode" icon to obscure all monetary values.

### Wireframe Description
A multi-section layout with a main navigation sidebar on the left.

### 2.1. Privacy Mode

The "Privacy Mode" is a global toggle that allows users to obscure sensitive financial data.

*   **Icon:** The toggle is represented by an eye icon in the top bar.
    *   **Visible State:** A regular eye icon (`EyeIcon`) indicates that all data is visible.
    *   **Hidden State:** A slashed eye icon (`EyeSlashIcon`) indicates that sensitive data is obscured.
*   **Placeholder:** When active, all sensitive monetary values are replaced with a generic placeholder: `₹**,***.**`. This format is designed to mimic the shape of a currency value without revealing any actual numbers.

```
+-------------------------------------------------------------------+
| [NAV] | Top Bar: Search [_________] (👁️) [User Profile]           |
|-------|-----------------------------------------------------------|
| Dash  |  +---------------+  +---------------+  +---------------+  |
| Ports |  | Total Value   |  | Overall P/L   |  | Day's Gain    |  |
| Goals |  | $1,234,567.89 |  | +$56,789.01   |  | -$1,234.56    |  |
| Risk  |  +---------------+  +---------------+  +---------------+  |
| ...   |                                                           |
|       |  +---------------------------+ +------------------------+ |
|       |  | Portfolio Value Over Time | | Asset Allocation       | |
|       |  |                           | |       /-----\          | |
|       |  |      /\      /''\         | |      |  O--+ | Stocks  | |
|       |  |     /  \/\  /    \        | |      | / \ | | Bonds   | |
|       |  |    /      \/      \       | |       \-----/          | |
|       |  | [1D][1W][1M][1Y][ALL]     | |                        | |
|       |  +---------------------------+ +------------------------+ |
|       |                                                           |
|       |  [1D][1W][1M][1Y][ALL]     | |                        | |
|       |  +---------------------------+ +------------------------+ |
|       |                                                           |
|       |  Top Holdings Overview                                    |
|       |  [ Asset Name | Value | P/L% ]                            |
|       |  [------------|-------|------]                            |
|       |  [ GOOGL      | ...   | ...  ]                            |
+-------------------------------------------------------------------+
```

### 2.2. Sectioned Consolidated Holdings Table (v1.2.0)

A major feature of v1.2.0 is replacing flat transaction lists with a consolidated, groupable table.

*   **Grouping:** Assets are grouped by type (e.g., `Equity`, `Mutual Funds`, `Fixed Deposits`). Each section acts as a collapsible accordion.
*   **Sorting:** Each column (Name, Qty, Avg Cost, Current Price, Value, PNL, XIRR) is sortable within its section.
*   **Drill-Down Modal:** Clicking on any row opens the **Tax Lot Details Modal** (see Section 3.1).

```
+-------------------------------------------------------------------+
|  [ ▼ ] EQUITY (Total Value: $500,000)                             |
|-------------------------------------------------------------------|
|  Asset Name | Qty  | Avg Price | Current | Total Value | PNL      |
|  GOOGL      | 10   | $100      | $150    | $1,500      | +$500    |
|  AAPL       | 5    | ...       | ...     | ...         | ...      |
|-------------------------------------------------------------------|
|  [ ▶ ] MUTUAL FUNDS (Total Value: $100,000)                       |
|-------------------------------------------------------------------|
|  [ ▶ ] FIXED DEPOSITS (Total Value: $50,000)                      |
+-------------------------------------------------------------------+
```

## 3. Portfolio Management & "Add New Asset" Flow (FR4)

### User Flow
The user navigates to the "Portfolios" page from the sidebar. They see a list of their created portfolios (e.g., "Retirement", "Vacation Fund"). They can click on a portfolio to see its specific assets or click a global "Add New..." button.

### "Add New..." Modal Flow
This is a multi-step process to handle complexity gracefully.

1.  **Step 1: Select Category**
    A modal appears with large, clear buttons for each asset category.
    `[Market-Traded]` `[Fixed Income]` `[Govt. Scheme]` `[Employee Plan]`

2.  **Step 2: Enter Details**
    The form dynamically changes based on the selection in Step 1.
    *   If **Market-Traded** was chosen:
        *   `Portfolio to add to: [Retirement Fund ▼]`
        *   `Asset Type: [Stock ▼]` (Stock, ETF, MF, Bond)
        *   `Ticker: [GOOGL]`
        *   `Transaction Type: [Buy ▼]`
        *   Fields: Quantity, Price, Date, Fees.
    *   If **Employee Plan** was chosen:
        *   `Plan Type: [RSU ▼]` (RSU, ESPP)
        *   `Currency: [USD ▼]`
        *   Fields: Grant ID, Grant Date, Shares Granted, Vesting Schedule.

This guided flow makes adding complex assets intuitive.

### 3.1. Tax Lot Drill-Down & Sell Link Modal (v1.2.0)

When a user clicks on a holding in the Consolidated Table or attempts to SELL an asset, they are presented with the **Tax Lot Modal**.

*   This modal lists every `BUY` transaction that makes up the total quantity of the holding.
*   It shows the `Original Qty`, `Remaining Qty` (after previous sells), and `Purchase Date` for each lot.
*   If the user is selling, checkboxes appear next to each lot, allowing them to perform **Specific Lot Identification** (e.g., selling the highest-cost lots first to minimize capital gains tax).

## 4. Risk Profile Page (FR12)

### User Flow
A first-time visitor to this page is shown the questionnaire. After submitting, they are shown the results page. On subsequent visits, they see the results page directly, with an option to "Retake Questionnaire."

### Wireframe Description (Results View)

```
+-------------------------------------------------------------------+
| [NAV] | Top Bar: Search [_________] (👁️) [User Profile]           |
|-------|-----------------------------------------------------------|
| ...   |  Risk Profile Analysis                                    |
| Risk  |                                                           |
| ...   |  +---------------------+   +----------------------------+ |
|       |  | Your Profile        |   | Your Portfolio's Risk      | |
|       |  |   MODERATE          |   |   AGGRESSIVE               | |
|       |  | (Description...)    |   | (Description...)           | |
|       |  +---------------------+   +----------------------------+ |
|       |                                                           |
|       |  +----------------------------------------------------+ |
|       |  | ⚠️ Mismatch Detected! Your portfolio is riskier...  | |
|       |  +----------------------------------------------------+ |
|       |                                                           |
|       |  [ Retake Questionnaire Button ]                          |
+-------------------------------------------------------------------+
```

## 5. Goal Planning Page (FR13)

### User Flow
The user navigates to the "Goals" page. They see a summary of all their financial goals. They can click "Add New Goal" to define a new one or click into an existing goal to see its detailed projection.

### Wireframe Description (Goal List View)

```
+-------------------------------------------------------------------+
| [NAV] | Top Bar: Search [_________] (👁️) [User Profile]           |
|-------|-----------------------------------------------------------|
| ...   |  Your Financial Goals            [ Add New Goal + ]       |
| Goals |                                                           |
| ...   |  +----------------------------------------------------+ |
|       |  | Retirement Fund               Target: $2,000,000   | |
|       |  | [|||||||||||||||||65%||......]  On Track           | |
|       |  | Projected to meet goal by 2048. [Details ->]       | |
|       |  +----------------------------------------------------+ |
|       |  +----------------------------------------------------+ |
|       |  | House Down Payment            Target: $150,000     | |
|       |  | [||||||||||40%||..............]  Off Track          | |
|       |  | Increase contributions by $250/mo. [Details ->]    | |
+-------------------------------------------------------------------+
```

## 6. Automated Data Import Wizard (v1.2.0)

### User Flow
The user navigates to "Import Data". They upload a file, the system parses it, and then presents a "Staging Preview" where they can review, edit, or reject the parsed transactions before committing them to the permanent database.

### 6.1. Staging Preview Wireframe

The preview differentiates between new, valid transactions, duplicates (already identical hashes in DB), and invalid/unrecognized rows.

```
+-------------------------------------------------------------------+
|  Import Session Preview: zerodha_tradebook.csv                    |
|-------------------------------------------------------------------|
|  [ ▼ ] Valid Transactions (150 Ready to Import)                   |
|-------------------------------------------------------------------|
|  [x] Date       | Ticker  | Action | Qty | Price                  |
|  [x] 2024-01-01 | RELIANCE| BUY    | 10  | ₹2500                  |
|  [ ] 2024-01-02 | UNKNOWN | BUY    | 5   | ₹100    [Map Alias ✏️] |
|-------------------------------------------------------------------|
|  [ ▶ ] Ignored Duplicates (5 Already in DB)                       |
|-------------------------------------------------------------------|
|                                    [ Discard ]   [ Commit Data ]  |
+-------------------------------------------------------------------+
```