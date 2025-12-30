# ArthSaarthi - User Guide

Welcome to ArthSaarthi! This guide will walk you through setting up and using the application.

---

## 1. Initial Installation & Setup

This application is designed to be self-hosted, giving you full control over your data. To get started, you'll need to install and run the application on your own system or server.

➡️ **For detailed installation instructions, please see the [Installation Guide](./installation_guide.md).**

**macOS Users:** If you see a "damaged" error, copy the app to Applications first, then run `xattr -cr /Applications/ArthSaarthi.app` in Terminal before launching.

### First-Time Admin Account Creation

The most important part of the installation is the initial setup. The first time you access the application, you will be greeted with a setup screen.

You **must** complete this form to create the first **administrator** account. This is the only time you will see this screen. After this account is created, all new users must be added by an administrator.

### Desktop Mode vs Server Mode

ArthSaarthi can run in two modes:

| Feature | Desktop Mode | Server Mode |
|---------|--------------|-------------|
| **Users** | Single user | Multiple users |
| **Database** | SQLite (encrypted) | PostgreSQL |
| **User Management** | ❌ Not available | ✅ Full access |
| **Interest Rates** | ✅ Available | ✅ Available |
| **Asset Sync** | ✅ Available | ✅ Available |
| **Data Storage** | Local files | Server database |

> **Desktop Mode** is designed for personal use on your own computer. Since there's only one user, the User Management feature is disabled - you don't need to manage users when you're the only one!

---

## 2. The Dashboard {#dashboard}

After logging in, you will land on your main dashboard. This is your central hub for viewing the overall health of your investment portfolios.

Here's what each section means:

### Summary Cards {#dashboard-summary-cards}

*   **Total Value:** The current market value of all assets across all your portfolios.
*   **Unrealized P/L:** The total paper profit or loss for assets you still hold.
*   **Realized P/L:** The total profit or loss you have locked in from selling assets.

### Top Movers {#dashboard-top-movers}

A table showing the assets that have had the largest price change over the last 24 hours.

### Portfolio History {#dashboard-portfolio-history}

An interactive line chart showing the total value of your portfolios over time. You can select different time ranges (7D, 30D, 1Y, All).

### Asset Allocation {#dashboard-asset-allocation}

A pie chart showing the distribution of your investments across different assets.

### 2.1. Privacy Mode {#privacy-mode}

If you wish to show your dashboard to others without revealing sensitive financial totals, you can use Privacy Mode.

*   **Location:** Look for the "eye" icon in the header of the Dashboard page.
*   **Toggle:** Clicking this icon will toggle Privacy Mode on or off.
    *   When **on** (slashed eye icon), all sensitive monetary values (like Total Value and P&L) will be replaced with a placeholder like `₹**,***.**`.
    *   When **off** (regular eye icon), all values will be visible.
*   **Persistence:** Your choice is saved in your browser, so the application will remember your preference the next time you visit.

---

## 3. Managing Your Portfolios {#managing-portfolios}

You can create multiple portfolios to track different investment strategies or accounts.

### Creating a Portfolio {#creating-portfolio}

1.  Navigate to the **Portfolios** page from the main menu.
2.  Click the **"Create New Portfolio"** button.
3.  A modal will appear. Enter a unique name for your portfolio.
4.  Click **"Create"**. You will be automatically taken to the detail page for your new portfolio.

### Viewing and Deleting a Portfolio {#deleting-portfolio}

*   From the **Portfolios** page, you can see a list of all your portfolios.
*   Click on any portfolio's name to go to its **Detail Page**, where you can see its transaction history.
*   Click the **"Delete"** button next to a portfolio to permanently remove it and all its associated transactions. You will be asked to confirm this action.

---

## 4. Managing Transactions {#managing-transactions}

The core of the application is tracking your individual buy and sell transactions.

### Adding a Transaction {#adding-transaction}

1.  Navigate to the detail page of the portfolio where you want to add a market-traded asset (like a Stock or Mutual Fund).
2.  Click the **"Add Transaction"** button.
3.  The "Add Transaction" modal will appear. Fill in the following details:
    *   **Asset:** Start typing the ticker symbol (e.g., 'AAPL', 'BTC-USD').
        *   If the asset exists, it will appear in a dropdown list. Click to select it.
        *   If the asset is not found, a **"Create new asset '[TICKER]'"** button will appear. Click this to validate the ticker with an external service and add it to your system.
    *   **Type:** Choose BUY or SELL.
    *   **Quantity:** The number of shares or units.
    *   **Price per Unit:** The price you paid or received for each unit.
    *   **Transaction Date:** The date the transaction occurred.
    *   **Fees:** Any associated fees (optional).
4.  Click **"Save Transaction"**.

The backend includes validation to prevent you from selling more of an asset than you own on a given date. If you attempt this, you will see a specific error message.

### Importing Transactions from a CSV File {#importing-transactions}

Instead of adding transactions one by one, you can use the data import feature to upload a CSV file.

1.  Navigate to the **"Import"** page from the main menu.
2.  Select the portfolio you want to import the transactions into.
3.  Select the **Statement Type** (e.g., "Generic CSV", "Zerodha", "ICICI Direct") that matches your file format. This ensures the file is parsed correctly.
4.  Choose the CSV file from your computer.
4.  Click **"Upload and Preview"**.
6.  The system will show you a preview of the transactions it has parsed, categorized into sections:
    *   **New Transactions:** Valid transactions that can be imported.
    *   **Transactions Requiring Mapping:** Transactions with a ticker symbol that is not recognized by the system (e.g., `INFY-BE` instead of `INFY.NS`).
    *   **Duplicate Transactions:** Transactions that appear to already exist in your portfolio.
    *   **Invalid Transactions:** Transactions with errors that prevent them from being imported.

### Mapping Unrecognized Tickers

For transactions in the "Requiring Mapping" section, you must map the unrecognized ticker from your file to an existing asset in the system.

1.  Click the **"Map Ticker"** button next to the transaction.
2.  In the modal that appears, search for the correct asset that the alias belongs to (e.g., search for "Infosys" or "INFY.NS").
3.  Select the correct asset from the search results and click **"Create Alias"**.
4.  Once the alias is created, the transaction will automatically move to the "New Transactions" section.

### Committing Transactions

1.  Use the checkboxes to select which "New" and "Duplicate" transactions you wish to import.
2.  Click **"Commit Transactions"** to save the selected transactions to your portfolio.

---

## 5. Tracking Other Asset Types

The "Add Transaction" modal is also your gateway to tracking non-market assets like Fixed Deposits, Recurring Deposits, and PPF accounts.

### 5.1. Tracking Fixed Deposits (FDs) {#tracking-fixed-deposits}

1.  **Adding an FD:** From the "Add Transaction" modal, select **"Fixed Deposit"** from the "Asset Type" dropdown. Fill in the FD-specific details, such as Institution Name, Principal Amount, Interest Rate, and Maturity Date, then save.
2.  **Viewing an FD:** FDs are displayed in the "Deposits" section of the holdings table. Clicking on an FD row opens a detailed drill-down view with its current value, projected maturity value, and XIRR analytics. You can also edit or delete the FD from this view.

### 5.2. Tracking Recurring Deposits (RDs) {#tracking-recurring-deposits}

1.  **Adding an RD:** From the "Add Transaction" modal, select **"Recurring Deposit"** from the "Asset Type" dropdown. Fill in the RD-specific details, such as Institution Name, Monthly Installment, Interest Rate, and Tenure.
2.  **Viewing an RD:** RDs are displayed in the "Deposits" section of the holdings table. Clicking on an RD row opens a detailed drill-down view with its current value, projected maturity value, and XIRR analytics.

### 5.3. Tracking Public Provident Fund (PPF) {#tracking-ppf}

The application has a specialized workflow for PPF accounts, as users typically only have one.

1.  **Adding Your First PPF Account:**
    *   From the "Add Transaction" modal, select **"PPF Account"** from the "Asset Type" dropdown.
    *   Because no PPF account exists, the form will show fields to **create the account** (Institution Name, Account Number, Opening Date) and fields for your **first contribution** (Amount, Date).
    *   Fill out all fields and click "Save". This will create both the PPF asset and its first transaction in one step.

2.  **Adding Subsequent Contributions:**
    *   The next time you select "PPF Account" from the "Asset Type" dropdown, the application will detect that you already have a PPF account.
    *   The form will now show your existing account details as read-only and will only ask for the **Contribution Amount** and **Contribution Date** for your new transaction.

3.  **Viewing PPF Details:**
    *   Your PPF account is displayed in the "Government Schemes" section of the holdings table.
    *   Clicking on the PPF row opens a special **passbook-style drill-down view**.
    *   This view shows a summary of your total contributions, interest earned, and the current balance. It also provides a chronological history of all your contributions and the system-generated interest credits for each financial year.

---
## 6. Tracking Your Goals {#managing-goals}

The Goals feature allows you to set financial targets and link your investments to track your progress.

### Creating a Goal
1.  Navigate to the **Goals** page from the main menu.
2.  Click **"Create Goal"**.
3.  In the modal, provide a name, a target amount, and a target date.

### Linking Investments to a Goal
1.  From the Goals page, click **"View"** on any goal card to go to its detail page.
2.  In the "Linked Items" section, click **"Link Item"**.
3.  A modal will appear. You can either select one of your existing portfolios or search for a specific asset to link to the goal.
4.  The system will automatically calculate your progress towards the goal based on the current value of all linked items.
---

## 7. Tracking RSU & ESPP Awards {#espp-rsu}

Track Restricted Stock Units (RSUs) and Employee Stock Purchase Plan (ESPP) awards with proper tax lot accounting.

### Adding an RSU Award

1.  From a portfolio detail page, click the "Additional actions" dropdown menu.
2.  Select **"Add ESPP/RSU Award"**.
3.  Search for and select the company stock.
4.  Fill in the vest date, quantity, and Fair Market Value (FMV) at vesting.
5.  Optionally record **Sell to Cover** shares sold to cover taxes.

### Adding an ESPP Purchase

1.  Follow the same steps as RSU, but enter the purchase price (usually discounted).
2.  The system will track your cost basis correctly for tax purposes.

---

## 8. Corporate Actions {#corporate-actions}

Handle mergers, demergers, and ticker renames that affect your holdings.

### 8.1. Adding a Merger

When two companies merge (e.g., HDFC Bank absorbed HDFC Ltd):

1.  From a portfolio detail page, click **"Add Transaction"**.
2.  Select the **old asset** you held (e.g., HDFC).
3.  Select **"Corporate Action"** as Transaction Type.
4.  Select **"Merger/Amalgamation"** as Action Type.
5.  Enter the **Record Date** and **Conversion Ratio** (e.g., 1.68 for HDFC-HDFCBANK merger).
6.  Search for and select the **new merged company ticker**.
7.  Click **"Save Transaction"**.

> **Cost Basis:** The system preserves your original acquisition dates and cost basis. XIRR calculations reflect your true investment timeline.

### 8.2. Adding a Demerger

When a company spins off a division (e.g., Reliance spun off Jio Financial):

1.  From a portfolio detail page, click **"Add Transaction"**.
2.  Select the **parent asset** (e.g., RELIANCE).
3.  Select **"Corporate Action"** > **"Demerger/Spin-off"**.
4.  Enter the **Record Date** and **Demerger Ratio** (shares of new company per old share).
5.  Enter the **Cost Allocation %** to the demerged entity (from official sources).
6.  Search for and select the **demerged company ticker**.
7.  Click **"Save Transaction"**.

> **Multi-Entity Demergers:** For 3-way splits (e.g., HDFC → HDFCBANK + HDFCLIFE + remaining), create separate demerger transactions for each child entity with their respective cost allocations.

### 8.3. Ticker Rename

When a company changes its ticker symbol only (e.g., VEDL → VEDANTA):

1.  Select the **old ticker** and choose **"Ticker Rename"**.
2.  Enter the effective date and search for the **new ticker**.
3.  Click **"Save Transaction"**.

### 8.4. Viewing Adjusted Holdings

After a corporate action:
- **Holdings Table:** Shows adjusted quantity and average buy price
- **Transaction History:** Displays both adjusted and original prices (e.g., "₹360.00 (orig: ₹900.00)")
- **XIRR/CAGR:** Calculated using adjusted investment amount

> **Note:** Corporate actions require existing holdings on the record date. If you have no holdings, the transaction will be rejected.

---

## 9. Backup & Restore {#backup-restore}

Protect your financial data with the backup and restore feature.

### Creating a Backup

1.  Navigate to your **Profile** page.
2.  In the "Backup & Restore" section, click **"Download Backup"**.
3.  Save the JSON file to a secure location.

### Restoring from Backup

1.  Click **"Restore from Backup"** and select your backup file.
2.  **Warning:** Restoring will replace all your current data. Type "DELETE" to confirm.
3.  Your data will be restored from the backup file.

---

## 10. User Management (Admin Only - Server Mode) {#user-management}

> **Note:** User Management is only available in **Server Mode** (multi-user). In Desktop Mode, the application is single-user, so user management is not needed.

If you are logged in as an administrator in Server Mode, you will see a **"User Management"** link in the navigation bar. This page allows you to manage all users of the application.

*   **Create User:** Click the "Create New User" button to add a new user. You can choose whether to make them an administrator.
*   **Edit User:** Click the "Edit" button on any user to change their details or admin status.
*   **Delete User:** Click the "Delete" button to permanently remove a user.

---

## 11. System Maintenance (Admin Only) {#system-maintenance}

Administrators can trigger asset master database updates without restarting the server.

### Syncing Asset Data

1.  Navigate to **System Maintenance** from the admin menu.
2.  Click the **"Sync Assets"** button.
3.  The system will download and process updated data from NSDL, BSE, NSE, and other sources.
4.  **Rate Limit:** This can only be done once every 5 minutes.

---

## 12. Getting Help & Reporting Bugs {#getting-help}

If you encounter a bug or have a feature request, please **open an issue on the project's GitHub repository**. Your feedback is essential for improving the application!

➡️ **For a visual guide with screenshots, see the [HTML User Guide](./user_guide/index.html).**