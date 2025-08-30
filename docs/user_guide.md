# ArthSaarthi - User Guide

Welcome to ArthSaarthi! This guide will walk you through setting up and using the application.

---

## 1. Initial Installation & Setup

This application is designed to be self-hosted, giving you full control over your data. To get started, you'll need to install and run the application on your own system or server.

➡️ **For detailed installation instructions, please see the [Installation Guide](./installation_guide.md).**

### First-Time Admin Account Creation

The most important part of the installation is the initial setup. The first time you access the application, you will be greeted with a setup screen.

You **must** complete this form to create the first **administrator** account. This is the only time you will see this screen. After this account is created, all new users must be added by an administrator.

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

1.  Navigate to the detail page of the portfolio where you want to add a transaction.
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
## 5. Tracking Your Goals {#managing-goals}

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

## 6. User Management (Admin Only) {#user-management}

If you are logged in as an administrator, you will see a **"User Management"** link in the navigation bar. This page allows you to manage all users of the application.

*   **Create User:** Click the "Create New User" button to add a new user. You can choose whether to make them an administrator.
*   **Edit User:** Click the "Edit" button on any user to change their details or admin status.
*   **Delete User:** Click the "Delete" button to permanently remove a user.

---

## 7. Getting Help & Reporting Bugs {#getting-help}

If you encounter a bug or have a feature request, please **open an issue on the project's GitHub repository**. Your feedback is essential for improving the application!