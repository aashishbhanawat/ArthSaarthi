# ArthSaarthi - User Guide

This comprehensive guide covers everything from initial setup to advanced portfolio analytics and tax reporting.

---

## 1. Setup, Administration & Settings

### 1.1 First-Time Setup & Login
The first time you access ArthSaarthi, you will be prompted to create an **Administrator** account. This account has full control over the server, including user management and system maintenance.

*   **Login Page**: Navigate to the base URL and enter your `Email` and `Password`.
*   **Privacy Mode**: In the top-right header, you can toggle **Privacy Mode** (eye icon). When enabled, all monetary values (Total Value, P/L, etc.) are obscured with `***`, allowing you to use the app in public spaces.

![Privacy Mode Enabled](file:///home/developer/pms/ArthSaarthi/temp_qa_run/dashboard_privacy_v3_1774610848938.png)

### 1.2 User Management (Server Mode Only)
Administrators can manage multiple users. Note that data isolation is strict: users can only see their own portfolios and data.

*   **Create User**: Navigate to **User Management** in the sidebar. Click **"Create New User"**. Fill in the Full Name, Email, and Password. You can designate them as an 'Admin' or 'User'.
*   **Edit/Delete**: Use the action buttons next to each user in the table to modify their details or revoke access.

![User Management Table](file:///home/developer/pms/ArthSaarthi/temp_qa_run/user_mgmt_v3_1774610111318.png)

### 1.3 Interest Rate Management
This section allows you to configure interest rates for various schemes. Currently, the system prioritizes **PPF** (Public Provident Fund) rates.

*   **Adding a Rate**: Click **"Add New Rate"**. Select the Scheme (e.g., PPF), enter the Start and End dates, and the Interest Rate percentage.
*   **Known Requirement**: Manual date entry requires character-by-character input to align with the field mask.

![PPF Interest Rate Entry](file:///home/developer/pms/ArthSaarthi/temp_qa_run/interest_rates_v3_1774610482835.png)

### 1.4 System Maintenance & Asset Sync
To ensure your portfolio reflects the latest market prices, use the maintenance tools.

*   **Asset Master Sync**: Navigate to **System Maintenance** and click **"Sync Assets"**. This triggers a background process to fetch the latest metadata and prices for stocks, mutual funds, and bonds from NSE, BSE, and AMFI.

![Asset Sync in Progress](file:///home/developer/pms/ArthSaarthi/temp_qa_run/sys_maint_v3_1774610549976.png)

### 1.5 Grandfathering (FMV 2018 Management)
For Indian Equity investments made before January 31, 2018, the **Grandfathering Rule** applies.

*   **FMV Lookup**: Navigate to **FMV Management**. You can view or 'Fetch' the official Fair Market Value as of Jan 31, 2018, for your holdings. This is critical for accurate Long-Term Capital Gains (LTCG) calculation.

![FMV Management](file:///home/developer/pms/ArthSaarthi/temp_qa_run/fmv_mgmt_v3_1774610582780.png)

### 1.6 Symbol Aliases
Sometimes different data providers use different ticker symbols for the same asset.

*   **Mapping Aliases**: In **Symbol Aliases**, you can map a source ticker (e.g., from a Zerodha export) to the unified system ticker used by ArthSaarthi.

![Symbol Aliases](file:///home/developer/pms/ArthSaarthi/temp_qa_run/symbol_aliases_v3_1774610618482.png)

### 1.7 Profile & Data Security
*   **Backup & Restore**: From the **Profile** page, you can download a full backup of your database as a `.db` file. This can be used to restore your data on a new installation.
*   **Theme Toggle**: Switch between **Light**, **Auto**, and **Dark** themes from the sidebar header.

![Profile & Backup](file:///home/developer/pms/ArthSaarthi/temp_qa_run/profile_backup_v3_1774610701838.png)
![Dark Theme Dashboard](file:///home/developer/pms/ArthSaarthi/temp_qa_run/dashboard_dark_v3_1774610784352.png)
