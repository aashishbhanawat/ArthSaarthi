# ArthSaarthi - Comprehensive User Guide

**Your Personal Investment Portfolio Manager**

ArthSaarthi is a powerful web-based application designed to help you track, manage, and analyze your investment portfolios across multiple asset classes including stocks, mutual funds, bonds, fixed deposits, recurring deposits, PPF, and RSU/ESPP awards.

---

## Table of Contents

1. [Getting Started](#getting-started)
   - Desktop Mode vs Server Mode
   - First-Time Setup
2. [Dashboard Overview](#dashboard-overview)
   - Top Movers
3. [Managing Portfolios](#managing-portfolios)
   - Portfolio Analytics
   - Benchmark Comparison
4. [Adding Transactions](#adding-transactions)
   - Tax Lot Selection
   - Corporate Actions
   - Dividends & Income
   - Stock Splits & Bonus Shares
5. [Viewing Transaction History](#viewing-transaction-history)
6. [Import Data](#import-data)
   - Supported Formats (v1.2.0)
7. [Goals](#goals)
8. [Watchlists](#watchlists)
9. [Profile & Settings](#profile--settings)
   - Backup & Restore
10. [Admin Features](#admin-features)
11. [Capital Gains & Tax](#capital-gains--tax)
12. [Themes & Privacy](#themes--privacy)

---

## Getting Started

### First-Time Setup

The first time you access the application, you will be greeted with a setup screen.

You **must** complete this form to create the first **administrator** account. This is the only time you will see this screen. After this account is created, all new users must be added by an administrator.

### Login

Access ArthSaarthi by navigating to the application URL. You'll be greeted with the login page where you can enter your credentials.

![Login Page](./images/login_page_1768317181108.png)

**To log in:**
1. Enter your **Email** address
2. Enter your **Password**
3. Click the **Login** button

> [!TIP]
> **Server Mode Users:** If you don't have an account, contact your system administrator to create one for you.
> **Desktop Mode Users:** You are the administrator of your local instance.

### Desktop Mode vs Server Mode

ArthSaarthi supports two deployment modes:

| Mode | Use Case | Database | Features |
|------|----------|----------|----------|
| **Desktop** | Personal use, single user | SQLite (local, encrypted) | All features except User Management |
| **Server** | Self-hosted, multiple users | PostgreSQL | Full features including User Management |

> [!NOTE]
> In Desktop Mode, your data is stored locally on your machine and encrypted. User Management is disabled since you're the only user.

#### Desktop System Tray

When running the Desktop App:
- Closing the window doesn't stop the backend services. Use the **System Tray** (near the clock on Windows/macOS) to **Quit** the application completely.
- The tray icon also provides quick status checks for the local server.

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
| **Portfolio History** | Interactive chart showing value changes over time. **(v1.2.0)**: Includes **Daily Snapshots** that automatically record your portfolio's total value every 6 hours to provide a smooth historical curve. |
| **Asset Allocation** | Pie chart showing distribution across different stocks/assets |
| **Top Movers** | Your best and worst performing assets today |

> [!WARNING]
> **Valuation Data Availability:** Components like the **Portfolio History** chart and **Benchmark Comparison** metrics will not display valuation data for assets where reliable price history is unavailable (e.g., Gold, certain Bonds, or unlisted instruments). These assets are still tracked at their acquisition cost in the holdings list.

### Top Movers

The **Top Movers** section highlights assets driving your portfolio's daily performance:
- **Top Gainers**: Assets with the highest positive change today
- **Top Losers**: Assets with the largest decline today

This helps you quickly identify what's moving your portfolio without checking each holding individually.

---

## Managing Portfolios

### Viewing Your Portfolios

Navigate to **Portfolios** from the sidebar to see all your investment portfolios.

![Portfolios List](./images/portfolios_list_1768317371312.png)

Each portfolio card shows:
- Portfolio name
- **Delete** button to remove the portfolio

### Creating a New Portfolio

Click the **Create New Portfolio** button to add a new portfolio.

![Create Portfolio Modal](./images/create_portfolio_modal_1768317398646.png)

**Steps:**
1. Enter a **Portfolio Name** (e.g., "Retirement Fund", "Children's Education")
2. Click **Create Portfolio**

### Deleting a Portfolio

To delete a portfolio:
1. Navigate to **Portfolios** page
2. Click the **Delete** button on the portfolio card
3. Confirm the deletion when prompted

> [!CAUTION]
> Deleting a portfolio permanently removes all holdings and transactions within it. This action cannot be undone.

### Portfolio Detail View

Click on any portfolio to see its detailed holdings and performance.

![Portfolio Detail with Holdings](./images/portfolio_detail_holdings_1768317659010.png)

The portfolio detail view shows:
- Summary cards (Invested, Current Value, Unrealized P/L, Realized P/L)
- **Consolidated Holdings Table:** Grouped by asset type (Stocks, Mutual Funds, FDs, etc.)
- Each section is collapsible and shows a total value for that category
- Sortable columns for Qty, Avg Price, Current Price, Total Value, PNL, and XIRR

### Holding Transaction History

Click on any holding to drill down into its complete transaction history.

![Holding Drilldown](./images/holding_drilldown_1768318989034.png)

This view displays:
- **Active Tax Lots (v1.2.0):** A list of all specific BUY transactions still constituting the current holding.
- **CAGR per Lot:** See the annualized return for every individual purchase.
- **Specific Lot Deletion/Edit:** Correct specific errors in your acquisition history without affecting other lots.
- **Exclusion of Closed Sales:** This view focuses on *what you still own*. For a complete history including closed SELL transactions, refer to the **Transactions** page.

### Portfolio Analytics

Comprehensive analytics for your investments are displayed at the top of the portfolio detail page, above the holdings list.

#### Advanced Analytics & Diversification

![Advanced Analytics](./images/portfolio_analytics_full_1768320754826.png)

**Advanced Analytics** includes:
- **XIRR**: Extended Internal Rate of Return - measures actual annualized returns
- **Sharpe Ratio**: Risk-adjusted return metric. *Note: Calculated only for market-traded assets (Stocks, MFs) to accurately measure volatility risk; excludes fixed-income assets like FDs/PPF.*

**Diversification Analysis** shows your portfolio distribution across:
- Asset Class
- Geography
- Market Cap (Large/Mid/Small)
- Sector
- Industry
- Investment Style

#### Investment Style Classification

Understand whether your portfolio leans toward **Growth** or **Value** investing:

| Style | Characteristics | Typical Metrics |
|-------|-----------------|-----------------|
| **Growth** | High growth potential, reinvested earnings | High P/E, High P/B |
| **Value** | Undervalued, dividend-paying | Low P/E, Low P/B |
| **Blend** | Mix of both styles | Moderate ratios |

The Investment Style gauge analyzes your holdings based on:
- **P/E Ratio**: Price-to-Earnings ratio classification
- **P/B Ratio**: Price-to-Book ratio classification

> [!NOTE]
> Investment style is calculated for equity holdings only. Mutual funds, FDs, and other assets are excluded from this analysis.

#### Benchmark Comparison

![Benchmark Comparison](./images/portfolio_benchmark_comparison_clean_1768320996408.png)

Compare your portfolio's performance against market benchmarks like **Nifty 50**:
- **Your Portfolio XIRR**: Your actual returns
- **Benchmark XIRR**: What you'd have earned in the benchmark
- **Alpha (Excess Return)**: The difference - positive means you outperformed!

#### Hybrid Benchmarks & Risk-Free Overlay (v1.2.0)

v1.2.0 introduces advanced benchmarking modes:
- **Hybrid Benchmarks**: Select from presets like "CRISIL Hybrid 35/65" or "Balanced 50/50" to compare against blended equity/debt indices.
- **Risk-Free Rate Overlay**: Toggle a dashed green line to see how your portfolio compares against a steady risk-free compound growth (e.g., 7% p.a.).

#### Category Comparison (v1.2.0)

Drill down into specific asset class performance:
- **Equity Category**: Compares all your stocks and equity MFs against the Nifty 50.
- **Debt Category**: Compares your FDs, RDs, and Bonds against a standard 10Y G-Sec yield.

#### Foreign Currency Support (v1.2.0)

For users with US Stocks, RSUs, or ESPPs, ArthSaarthi automatically handles multi-currency tracking:
- **Automatic FX Rates**: The system fetches historical USD/INR rates based on the transaction date.
- **Consolidated Valuation**: All assets are converted to your portfolio's base currency (typically INR) in the holdings table.
- **CAGR/XIRR in Base Currency**: returns are calculated after factoring in both price appreciation and currency fluctuations.

---

## Adding Transactions

### Stock Transactions

Click **Add Transaction** button in your portfolio and select **Stock** as the asset type.

![Add Stock Modal](./images/add_stock_modal_1768317698208.png)

**Required fields:**
- **Asset Type**: Stock
- **Transaction Type**: Buy, Sell, or Corporate Action
- **Stock Symbol**: Search by **Ticker** (e.g., RELIANCE) or **Company Name** (e.g., Reliance Industries)
- **Quantity**: Number of shares
- **Price per Unit**: Purchase/sale price
- **Transaction Date**: Date of transaction
- **Broker Fee** (Optional): Brokerage charges

### Selling with Tax Lot Selection

When selling shares, ArthSaarthi lets you choose which specific lots to sell from — crucial for tax optimization.

**Tax Lot Methods:**

| Method | Description | Best For |
|--------|-------------|----------|
| **FIFO** | First In, First Out - sells oldest shares first | Default method, simple |
| **LIFO** | Last In, First Out - sells newest shares first | Minimizing short-term gains |
| **Specific Lot** | Manually select which lots to sell | Maximum tax control |

**To use Specific Lot selection:**
1. When adding a SELL transaction, select **Specific Lot** as the method
2. View available lots with their purchase date, quantity, and cost basis
3. Select the lots you want to sell from
4. The system calculates capital gains based on your selection

> [!IMPORTANT]
> **Indian Tax Compliance Notice:**
> For standard **Demat holdings** (Stocks, Mutual Funds), Indian tax laws generally mandate the **FIFO (First-In, First-Out)** method for Capital Gains calculation. You cannot arbitrarily choose tax lots for these assets to lower tax liability.
>
> **Tax Lot Selection** in ArthSaarthi is primarily intended for:
> 1. **ESPP & RSU Sales:** Where specific shares are vested and sold, often with different cost bases (FMV vs Purchase Price).
> 2. **Physical Shares / Private Equity:** Assets not held in a standard demat account.
> 3. **Non-Indian Jurisdictions:** For users subject to tax laws where Specific Identification is permitted.



### Mutual Fund Transactions

For mutual fund investments, select **Mutual Fund** as the asset type.

![Add Mutual Fund Modal](./images/add_mutual_fund_modal_1768317753510.png)

**Required fields:**
- **Mutual Fund Name**: Search and select the fund
- **Transaction Type**: Buy, Sell, Corporate Action, or **DRIP** (Dividend Reinvestment)
- **Units**: Number of units
- **NAV**: Net Asset Value per unit
- **Transaction Date**: Date of transaction

> [!NOTE]
> **DRIP (Dividend Reinvestment Plan):** Use this option when dividends are automatically reinvested into additional units. Enter the dividend amount as the reinvestment value.

### Bond Transactions

Track your bond investments by selecting **Bond** as the asset type.

![Add Bond Modal](./images/add_bond_modal_1768317964289.png)
> [!WARNING]
> **Verify Data Accuracy:** The system attempts to pre-fill **Coupon Rate**, **Face Value**, and **Maturity Date**, but reliable public data for bonds is limited.
> **You must review these fields manually.** If they are missing or incorrect, please update them to ensure accurate calculations.

### Fixed Deposit

Record your fixed deposits with maturity tracking.

![Add Fixed Deposit Modal](./images/add_fixed_deposit_modal_1768317823011.png)

**Key fields:**
- **Principal Amount**: Invested amount
- **Interest Rate**: Annual interest rate
- **Start Date** and **Maturity Date**
- **Bank/Institution Name**
- **Compounding Frequency**: e.g., Quarterly, Annually
- **Payout Frequency**: e.g., On Maturity, Monthly

### Recurring Deposit

Track your recurring deposits with monthly contribution tracking.

![Add Recurring Deposit Modal](./images/add_rd_modal_1768317857506.png)

**Key fields:**
- **Institution Name**: Bank or post office
- **Monthly Installment**: Amount deposited each month
- **Interest Rate**: Annual interest rate
- **Tenure**: Number of months
- **Start Date**: When the RD began
- **Compounding Frequency**: e.g., Quarterly

### PPF Account

Manage your Public Provident Fund investments with automatic interest calculation.

![Add PPF Modal](./images/add_ppf_modal_1768318247973.png)

**First-time setup:**
1. Select **PPF Account** as asset type
2. Enter institution name and account number
3. Set the account opening date
4. Add your first contribution amount and date
5. Click **Save** — this creates both the PPF asset and first transaction

**Adding subsequent contributions:**
- When you select PPF Account again, the system detects your existing account
- The form only asks for contribution amount and date
- New contributions are automatically linked to your existing PPF

**PPF Passbook View:**
- Click on your PPF holding to see a passbook-style statement
- View all contributions and system-calculated interest credits
- Interest is calculated using official government rates for each financial year

> [!NOTE]
> PPF interest rates are managed by administrators and updated quarterly based on government announcements.

### RSU/ESPP Awards

For employees with stock compensation, track RSU and ESPP awards.

**How to navigate:**
3. Select **Add ESPP/RSU Award**

![RSU ESPP Modal](./images/rsu_espp_modal_1768318354551.png)

#### Acquisition Types

v1.2.0 tracks how shares were acquired to ensure accurate tax basis:
- **RSU Vest**: Market value at vest date is treated as your cost basis (already taxed as perquisite).
- **ESPP Purchase**: Your actual purchase price vs. Fair Market Value (FMV) is used to calculate the taxable benefit and eventual capital gains.

#### RSU Vest Form

**Key fields:**
- **Stock Symbol**: Your company's stock
- **Vest Date**: When shares were delivered
- **Quantity**: Number of shares vested
- **Fair Market Value (FMV)**: Stock price at vesting
- **Sell to Cover** (Optional): Shares sold to pay withholding taxes

#### ESPP Purchase Form

**Key fields:**
- **Stock Symbol**: Your company's stock
- **Purchase Date**: Date of ESPP purchase
- **Quantity**: Number of shares purchased
- **Purchase Price**: Discounted price you paid
- **Fair Market Value (FMV)**: Market price at purchase (used for tax basis)

> [!TIP]
> The "Sell to Cover" option (RSU only) automatically records shares sold to pay withholding taxes — a common RSU vesting scenario.

### Editing & Deleting Transactions

**To edit a transaction:**
1. Click on the transaction in the holding drill-down or Transactions page
2. Modify any field (quantity, price, date, fees)
3. Click **Save** — all metrics recalculate automatically

**To delete a transaction:**
1. Click the **Delete** button on the transaction
2. Confirm the deletion
3. Portfolio values update accordingly

> [!WARNING]
> Deleting transactions cannot be undone. Consider editing instead if you need to correct an error.

### Corporate Actions

Record corporate actions that affect your holdings via **Additional Actions** menu:

**Mergers & Amalgamations:**
- Record when two companies merge (e.g., HDFC Bank merger)
- Enter the conversion ratio
- System adjusts holdings while preserving cost basis

**Demergers & Spin-offs:**
- Record when a company splits (e.g., Reliance-Jio Financial)
- Specify demerger ratio and cost allocation
- Creates new holding with proportional cost basis

**Ticker Renames:**
- Record when a stock symbol changes (e.g., VEDL → VEDANTA)
- Historical transactions remain linked correctly

### Dividends & Income

**Recording Dividends:**
- **Automatic:** Import your broker's dividend statement (e.g., Zerodha, ICICI) to bulk add all dividend income.
- **Manual:** Use "Add Transaction" → **Dividend** type to record individual payouts.
  > [!NOTE]
  > When adding manually, enter the **Total Amount** received (e.g., ₹500), NOT the amount per share.

**Tracking:**
- View total dividend income in **Advanced Analytics**
- Check asset drill-down to see dividends received per holding
- **Dividend Report (v1.2.0):** Access the dedicated report in the **Capital Gains** section to see dividends grouped into **Quarterly Advance Tax Buckets** (e.g., Upto 15/6, 16/6 - 15/9) for easy ITR filing.

### Stock Splits & Bonus Shares

**Stock Split:**
- Use **Corporate Actions** → **Stock Split**
- Enter the Split Ratio (e.g., 5:1 for 5 new shares for every 1 held)
- The system increases your quantity and reduces buy price proportionally

**Bonus Shares:**
- Use **Corporate Actions** → **Bonus Issue**
- Enter Ratio (e.g., 1:1 for 1 bonus share for every 1 held)
- This increases your total quantity; cost basis per share decreases accordingly

---

## Viewing Transaction History

Navigate to **Transactions** from the sidebar to see all transactions across portfolios.

![Transactions History](./images/transactions_history_1768318393022.png)

**Features:**
- Filter by date range, asset type, or transaction type
- Quick edit or delete transactions
- Export transaction data

---

## Import Data

Bulk import your transaction history from CSV files or brokerage statements.

![Import Page](./images/import_page_1768318416664.png)

### Import Workflow

1. Navigate to **Import** from the sidebar
2. Select the **Portfolio** to import into
3. Choose the **Statement Type** matching your file format
4. Upload your file
5. Click **Upload and Preview**
6. Review parsed transactions in the **Staging Preview**:
   - **Valid Transactions**: Ready to import (checked by default)
   - **Ignored Duplicates**: Transactions already found in the database (unchecked by default)
   - **Unrecognized Assets**: Transactions where the ticker/ISIN isn't recognized (requires [Mapping](#mapping-unrecognized-tickers))
7. Select or deselect specific rows you wish to commit
8. Click **Commit Data** to save to your portfolio

### Mapping Unrecognized Tickers

When the system doesn't recognize a ticker from your file:
1. Click **Map Ticker** next to the transaction
2. Search for the correct asset (e.g., "Infosys" for "INFY-BE")
3. Select the match and click **Create Alias**
4. Future imports will use this mapping automatically

### Supported Formats

| Category | Format | File Type |
|----------|--------|-----------|
| **Stocks** | Generic CSV | .csv |
| **Stocks** | Zerodha Contract Notes | .csv |
| **Stocks** | ICICI Direct Statements | .csv |
| **Mutual Funds** | MFCentral CAS | .xlsx |
| **Mutual Funds** | CAMS Statement | .xlsx |
| **Mutual Funds** | KFintech Statement | .pdf |
| **Mutual Funds** | Zerodha Coin | .xlsx |
| **Mutual Funds** | ICICI Securities MF | .xlsx |
| **Dividends** | Zerodha Dividend Statement | .xlsx |
| **Dividends** | ICICI DEMAT Dividend | .pdf |

> [!TIP]
> For Mutual Funds, download your Consolidated Account Statement (CAS) from MFCentral for the most complete data.

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

### Backup & Restore

Protect your financial data with backup and restore capabilities.

**Creating a Backup:**
1. Go to **Profile** page
2. Click **Download Backup**
3. Save the JSON file to a secure location

The backup includes:
- All portfolios and holdings
- Complete transaction history
- Goals and watchlists
- Asset aliases and mappings

**Restoring from Backup:**
1. Go to **Profile** page
2. Click **Restore from Backup**
3. Select your backup JSON file
4. Confirm the restoration

> [!CAUTION]
> Restoring from backup **replaces all current data**. This cannot be undone. Always create a fresh backup before restoring.

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

Perform system maintenance tasks including Asset Master synchronization.

![Admin System Maintenance](./images/admin_system_maintenance_1768318837854.png)

**Asset Master Sync (Asset Seeding):**
- Click **Sync Assets** to update the internal database of stocks, mutual funds, and ETFs
- Downloads latest data from NSDL, BSE, NSE, and AMFI sources
- Ensures newly listed securities are searchable in the application
- **Rate Limit:** Can only be triggered once every 5 minutes

> [!NOTE]
> **Server Mode:** Asset seeding runs automatically on every server launch/restart. Use **Sync Assets** to update without restarting.
> **Desktop Mode:** Asset seeding runs only once on first boot. After that, you must manually run **Sync Assets** to get the latest securities.

---

## Capital Gains & Tax

ArthSaarthi provides robust reporting for Indian Income Tax compliance.

### Realized Capital Gains

Navigate to **Analytics > Capital Gains** to view your tax liability for a specific Financial Year.

**Key Features:**
- **LTCG vs STCG**: Automatically classifies gains based on holding periods (e.g., 1 year for Stocks, 2 years for Unlisted/Bonds, etc.).
- **Grandfathering (Sec 112A)**: For equity sold after 2018, the system factors in the **Jan 31, 2018 FMV** to calculate taxable gains.
- **Indexation**: For Debt assets and Bonds, the system applies the cost inflation index (CII) to reduce taxable burden.
- **FIFO Enforcement**: Standard market-traded assets are calculated using the FIFO method as per Indian tax norms.

### Tax Buckets

The **Dividend Report** groups income into government-mandated quarterly buckets:
1. Upto June 15
2. June 16 - Sept 15
3. Sept 16 - Dec 15
4. Dec 16 - March 15
5. March 16 - March 31

This allows you to accurately fill the "Schedule OS" (Other Sources) in your ITR.

### Symbol Alias Management (v1.2.0)

Admins can now manage the "Aliases" used during data import:
1. Navigate to **Admin > Symbol Aliases**.
2. View all existing mappings (e.g., "RELIANCE-EQ" → "RELIANCE").
3. **Edit** or **Delete** incorrect mappings to fix future imports.
4. **Manual Add**: Create a new mapping if the auto-map fails for a specific broker's format.

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
