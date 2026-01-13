# ArthSaarthi - Comprehensive User Guide

**Your Personal Investment Portfolio Manager**

ArthSaarthi is a powerful web-based application designed to help you track, manage, and analyze your investment portfolios across multiple asset classes including stocks, mutual funds, bonds, fixed deposits, recurring deposits, PPF, and RSU/ESPP awards.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Managing Portfolios](#managing-portfolios)
4. [Adding Transactions](#adding-transactions)
5. [Viewing Transaction History](#viewing-transaction-history)
6. [Import Data](#import-data)
7. [Goals](#goals)
8. [Watchlists](#watchlists)
9. [Profile & Settings](#profile--settings)
10. [Admin Features](#admin-features)
11. [Themes & Privacy](#themes--privacy)

---

## Getting Started

### Login

Access ArthSaarthi by navigating to the application URL. You'll be greeted with the login page where you can enter your credentials.

![Login Page](./images/login_page_1768317181108.png)

**To log in:**
1. Enter your **Email** address
2. Enter your **Password**
3. Click the **Login** button

> [!TIP]
> If you don't have an account, contact your administrator to create one for you.

---

## Dashboard Overview

After logging in, you'll be taken to the **Dashboard** - your central hub for portfolio insights.

![Dashboard Main View](./images/dashboard_main_1768317306374.png)

### Key Dashboard Components

| Component | Description |
|-----------|-------------|
| **Total Value** | The combined current value of all your investments |
| **Unrealized P/L** | Profit or loss on holdings you still own |
| **Realized P/L** | Profit or loss from investments you've sold |
| **Portfolio History** | Interactive chart showing value changes over time (7D, 30D, 1Y, All) |
| **Asset Allocation** | Pie chart showing distribution across different stocks/assets |

### Dark Theme

For comfortable viewing in low-light environments, switch to dark theme:

![Dashboard Dark Theme](./images/dark_theme_1768319158480.png)

---

## Managing Portfolios

### Viewing Your Portfolios

Navigate to **Portfolios** from the sidebar to see all your investment portfolios.

![Portfolios List](./images/portfolios_list_1768317371312.png)

Each portfolio card shows:
- Portfolio name
- Total invested amount
- Current value
- Profit/Loss percentage

### Creating a New Portfolio

Click the **Create New Portfolio** button to add a new portfolio.

![Create Portfolio Modal](./images/create_portfolio_modal_1768317398646.png)

**Steps:**
1. Enter a **Portfolio Name** (e.g., "Retirement Fund", "Children's Education")
2. Click **Create Portfolio**

### Portfolio Detail View

Click on any portfolio to see its detailed holdings and performance.

![Portfolio Detail with Holdings](./images/portfolio_detail_holdings_1768317659010.png)

The portfolio detail view shows:
- Summary cards (Invested, Current Value, Unrealized P/L, Realized P/L)
- Holdings breakdown by asset type (Stocks, Mutual Funds, etc.)
- Individual holding details with quantity, average price, and returns

### Holding Transaction History

Click on any holding to drill down into its complete transaction history.

![Holding Drilldown](./images/holding_drilldown_1768318989034.png)

This view displays:
- Complete list of all BUY/SELL transactions
- Date, quantity, price per unit, and total value
- CAGR and XIRR (Current & Historical) calculations
- Edit and delete options for each transaction

### Portfolio Analytics

Scroll down on the portfolio detail page to access comprehensive analytics for your investments.

#### Advanced Analytics & Diversification

![Advanced Analytics](./images/portfolio_analytics_full_1768320754826.png)

**Advanced Analytics** includes:
- **XIRR**: Extended Internal Rate of Return - measures actual annualized returns
- **Sharpe Ratio**: Risk-adjusted return metric

**Diversification Analysis** shows your portfolio distribution across:
- Asset Class
- Geography
- Market Cap (Large/Mid/Small)
- Sector
- Industry
- Investment Style (Growth/Value)

#### Benchmark Comparison

![Benchmark Comparison](./images/portfolio_benchmark_comparison_clean_1768320996408.png)

Compare your portfolio's performance against market benchmarks like **Nifty 50**:
- **Your Portfolio XIRR**: Your actual returns
- **Benchmark XIRR**: What you'd have earned in the benchmark
- **Alpha (Excess Return)**: The difference - positive means you outperformed!

---

## Adding Transactions

### Stock Transactions

Click **Add Transaction** button in your portfolio and select **Stock** as the asset type.

![Add Stock Modal](./images/add_stock_modal_1768317698208.png)

**Required fields:**
- **Asset Type**: Stock
- **Transaction Type**: Buy or Sell
- **Stock Symbol**: Search and select the stock
- **Quantity**: Number of shares
- **Price per Unit**: Purchase/sale price
- **Transaction Date**: Date of transaction
- **Broker Fee** (Optional): Brokerage charges

### Mutual Fund Transactions

For mutual fund investments, select **Mutual Fund** as the asset type.

![Add Mutual Fund Modal](./images/add_mutual_fund_modal_1768317753510.png)

**Required fields:**
- **Mutual Fund Name**: Search and select the fund
- **Transaction Type**: Buy/Sell/Corporate Action
- **Units**: Number of units
- **NAV**: Net Asset Value per unit
- **Transaction Date**: Date of transaction

### Bond Transactions

Track your bond investments by selecting **Bond** as the asset type.

![Add Bond Modal](./images/add_bond_modal_1768317964289.png)

### Fixed Deposit

Record your fixed deposits with maturity tracking.

![Add Fixed Deposit Modal](./images/add_fixed_deposit_modal_1768317823011.png)

**Key fields:**
- **Principal Amount**: Invested amount
- **Interest Rate**: Annual interest rate
- **Start Date** and **Maturity Date**
- **Bank/Institution Name**

### Recurring Deposit

Track your recurring deposits with monthly contribution tracking.

![Add Recurring Deposit Modal](./images/add_rd_modal_1768317857506.png)

### PPF Account

Manage your Public Provident Fund investments.

![Add PPF Modal](./images/add_ppf_modal_1768318247973.png)

### RSU/ESPP Awards

For employees with stock compensation, track RSU and ESPP awards via **Additional Actions > Add ESPP/RSU Award**.

![RSU ESPP Modal](./images/rsu_espp_modal_1768318354551.png)

---

## Viewing Transaction History

Navigate to **Transactions** from the sidebar to see all transactions across portfolios.

![Transactions History](./images/transactions_history_1768318393022.png)

**Features:**
- Filter by date range, asset type, or transaction type
- Sort by any column
- Quick edit or delete transactions
- Export transaction data

---

## Import Data

Bulk import your transaction history from CSV files or brokerage statements.

![Import Page](./images/import_page_1768318416664.png)

**Supported formats:**
- CSV files with transaction data
- Brokerage statement exports

> [!IMPORTANT]
> Ensure your CSV follows the expected format. Download the template for reference.

---

## Goals

Set and track your financial goals in the **Goals** section.

![Goals Page](./images/goals_page_1768318441380.png)

**Features:**
- Create goals with target amounts and dates
- Link portfolios to specific goals
- Track progress with visual indicators
- Get insights on whether you're on track

---

## Watchlists

Monitor stocks and funds you're interested in without adding them to your portfolio.

![Watchlists Page](./images/watchlists_page_1768318466860.png)

**Features:**
- Create multiple watchlists
- Add stocks/mutual funds to track
- View real-time price updates
- Quick add to portfolio when ready to invest

---

## Profile & Settings

Manage your account settings from the **Profile** page.

![Profile Page](./images/profile_page_1768318495413.png)

**Available settings:**
- Update profile information (name, email)
- Change password
- Configure notification preferences

---

## Admin Features

Admin users have access to additional management features.

### User Management

Create and manage user accounts from **Admin > User Management**.

![Admin User Management](./images/admin_user_management_1768318655458.png)

**Capabilities:**
- Create new user accounts
- Assign roles (Admin, User)
- Edit or delete existing users

### Interest Rates

Configure system-wide interest rates for fixed deposits and other instruments.

![Admin Interest Rates](./images/admin_interest_rates_1768318880092.png)

### System Maintenance

Perform system maintenance tasks like data cleanup and cache refresh.

![Admin System Maintenance](./images/admin_system_maintenance_1768318837854.png)

---

## Themes & Privacy

### Theme Toggle

Switch between **Light**, **Auto**, and **Dark** themes using the toggle in the sidebar.

| Light Theme | Dark Theme |
|-------------|------------|
| ![Light Theme](./images/dashboard_main_1768317306374.png) | ![Dark Theme](./images/dark_theme_1768319158480.png) |

### Privacy Mode

Click the **eye icon** next to the page title to toggle privacy mode, which hides sensitive financial data.

![Dashboard with Privacy Mode](./images/dashboard_privacy_on_1768317339237.png)

> [!TIP]
> Use privacy mode when viewing your portfolio in public spaces.

---

## Quick Reference

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Esc` | Close modal dialogs |

### Navigation Menu

| Menu Item | Description |
|-----------|-------------|
| Dashboard | Overview of all portfolios |
| Portfolios | Manage individual portfolios |
| Transactions | View all transactions |
| Import | Bulk import data |
| Watchlists | Track potential investments |
| Goals | Financial goal tracking |

---

## Support

For questions or issues, please contact your system administrator.

---

*ArthSaarthi - Empowering Your Investment Journey* 🚀
