### **Comprehensive Prompt for ArthSaarthi Full-Stack QA & User Guide Generation**

**Objective:**
Perform an exhaustive QA run on the ArthSaarthi application hosted at `https://librephotos.aashish.ai.in/`. The goal is to act as a real user, testing *every* feature (positive and negative scenarios) with real-world data, verifying all analytics calculations, and concurrently generating a detailed, screenshot-rich User Guide based on these actions.

---

### **Execution Steps & Testing Scenarios:**

#### **1. Initial Setup & Administration**
*   **Action:** Navigate to the setup page (`/setup` or root if redirected) and create the initial admin account. (Since the app is running in server mode, this step is expected).
*   **Admin Features Exploration (Server Mode):** Navigate to User Management to test creating a secondary test user, modifying roles, and deleting a user. 
*   Check the Interest Rates page, and test the System Maintenance/Asset Seeding functions.
    *   *Screenshot:* Setup page, User Management dashboard, Asset Seeding UI.

#### **2. Diverse Asset & Transaction Testing (Real Data)**
*   **Requirement:** Use **real historical dates and prices** for all asset entries to properly test benchmark and XIRR calculations.
*   **Stocks (Diversification focus):**
    *   *Indian Stocks (FIFO applied by default):*
        *   `RELIANCE` (Large Cap, Energy)
        *   `HDFCBANK` (Large Cap, Banking)
        *   `INFY` (Large Cap, IT)
        *   `TATAMOTORS` (Large Cap, Auto)
        *   `DRREDDY` (Mid Cap, Pharma)
        *   `HAPPISTMND` (Small Cap, IT)
    *   *Global Stocks (Specific Lot / FIFO testing):*
        *   `AAPL` (Apple Inc., Tech)
        *   `GOOGL` (Alphabet Inc., Tech)
        *   `MSFT` (Microsoft Corp., Tech)
*   **Transaction Types to Execute:** 
    *   Multiple BUYs across different dates (to setup tax lots).
    *   Partial SELLs. **CRITICAL DETAIL:** Test standard FIFO behavior on Indian Stocks. Utilize the **Specific Lot Selection** feature explicitly when selling Global Stocks or RSU/ESPP awards.
    *   Corporate Actions: Add a Bonus issue, a Stock Split, and a Cash Dividend transaction.
*   **Other Asset Classes:**
    *   **Mutual Funds:** 
        *   *Equity MF:* Enter Lumpsum and monthly SIP transactions (e.g., Nifty 50 Index fund) to test Equity taxation (10%/12.5% LTCG, 15%/20% STCG).
        *   *Debt MF:* Enter Lumpsum and SIP transactions (e.g., Liquid/Overnight fund) to test Debt taxation rules (Short Term vs Long Term based on holding period and indexation rules if applicable).
        *   *Action:* Test Redemption for both to generate capital gains reports.
    *   **Fixed Income:** Create an FD, an RD, and a PPF account with historical start dates.
    *   **Employee Plans:** Add RSU and ESPP awards (vested and unvested).
    *   *Screenshot:* "Add Transaction" modals for each type, Portfolio "Holdings" view, Asset Drill-down view.

#### **3. Advanced Features & Edge Cases (Negative Testing)**
*   **Generic CSV Import:** 
    *   **Action:** In your current environment, create a file named `sample_generic_import.csv` with the following content:
        ```csv
        Date,Ticker,Type,Quantity,Price,Fees,Broker
        2023-01-10,RELIANCE,Buy,10,2500,25.5,Zerodha
        2023-02-15,HDFCBANK,Buy,20,1600,15.2,Upstox
        2023-03-20,INFY,Buy,15,1400,12.0,Groww
        2023-04-25,RELIANCE,Sell,5,2600,26.0,Zerodha
        2023-05-30,TATAMOTORS,Buy,50,450,11.5,Zerodha
        2023-06-15,UNKNOWN_TICKER,Buy,10,100,5,Groww
        ```
    *   Navigate to the Import page, select "Custom CSV", upload this file, and intentionally trigger the "Transactions Requiring Mapping" flow for `UNKNOWN_TICKER`.
    *   Map `UNKNOWN_TICKER` to a valid system asset (e.g., ITC) and verify it moves to "New Transactions".
    *   Commit the transactions and verify they appear in the transaction list.
    *   *Screenshot:* Data mapping screen, Ticker Alias modal, and success message.
*   **Negative/Edge Cases:**
    *   Attempt to save transactions with negative quantities or zero prices.
    *   Attempt to enter sell transactions exceeding current holdings.
    *   Verify Session Timeout behavior (simulate inactivity if possible).
    *   Verify that "Privacy Mode" effectively obscures all monetary values system-wide.

#### **4. Portfolios, Goals, and Watchlists**
*   **Portfolios & Drill-Downs:**
    *   Create multiple portfolios (e.g., "Retirement", "Trading").
    *   **Holding Drill-Down (CRITICAL):** For each portfolio, click on individual holdings to open the detailed asset drill-down view.
    *   Navigate through **all available tabs** within the drill-down (e.g., Summary, Transactions, Performance).
*   **Goal Planning:** Navigate to Goals, create a specific financial goal (e.g., "House Downpayment" target 50L by 2030), and link existing assets/portfolios to it. Observe the projection charts.
    *   *Screenshot:* Goal creation, Goal Dashboard, Asset Drill-down tabs.
*   **Watchlists:** Navigate to Watchlists and add 3-4 assets not currently owned.
    *   *Screenshot:* Watchlist view.

#### **5. Exhaustive UI Navigation & Reports Verification**
*   **Navigation Check:** Click through *every* item in the main navigation menu and sidebar. Ensure no generic 404s or broken links exist across Dashboard, Portfolios, Transactions, Goals, Watchlists, Import, Profile, and Admin sections.
*   **Dashboard & Benchmarking:**    *   Verify the aggregated "Total Value" matches the sum of individual portfolios.
    *   Verify the Asset Allocation pie charts and Geography/Sector diversification charts.
    *   **Benchmarks:** Toggle through *all* available benchmark types (Nifty 50, Hybrid, Risk-Free, etc.) on the comparison charts.
    *   *Screenshot:* Dashboard views, Benchmark comparison charts.
*   **Capital Gains & Taxation Reporting:**
    *   Navigate to the Capital Gains report.
    *   **Verify Scenarios:** Ensure the report correctly identifies:
        *   Short-Term Capital Gains (STCG).
        *   Long-Term Capital Gains (LTCG).
        *   **Grandfathering Rules:** Specifically check if pre-2018 acquisitions accurately apply grandfathering logic on the FMV.
    *   Export the data in ITR format if available.
    *   *Screenshot:* Capital Gains report UI, Tax Lot selection during a sell transaction.
*   **Transaction History:** Review the dedicated Transaction History page, applying filters for dates, types, and specific assets.

#### **6. User Guide, Videos & Audio Scripts**
*   **Demo Videos (CRITICAL):** The browser subagent you use intrinsically supports video recording. You **must** utilize the `RecordingName` parameter in the `browser_subagent` tool for every major workflow (e.g., `RecordingName: "adding_reliance_stock_flow"` or `RecordingName: "capital_gains_report_demo"`). This will automatically save WebP videos of your actions to your artifacts directory for use in a demo video.
*   **Voiceover Scripts:** For every `RecordingName` you generate, you must also write a corresponding "Voiceover Script" in your final documentation. This script should explain exactly what is happening on screen so an external text-to-speech tool can sync audio to the video. 
*   Concurrently compile a detailed `USER_GUIDE.md` document.
*   Structure the guide logically (e.g., Introduction, Getting Started, Adding Assets, Understanding Analytics).
*   Embed the `[Screenshot: <Scenario Description>]` or `[Video: <RecordingName>.webp]` placeholders exactly where the media should be placed. At the bottom of each section, include the `[Voiceover Script: ...]` block for that specific video.

### **Final Deliverables from this Run:**
1.  A fully populated test account on `https://librephotos.aashish.ai.in/`.
2.  A detailed log confirming the mathematical accuracy of XIRR, STCG, LTCG (with grandfathering), and dashboard aggregations based on the real data entered.
3.  WebP video recordings of all major workflows.
4.  A comprehensive `USER_GUIDE.md` markdown file with embedded media placeholders and corresponding Voiceover Scripts mapping to the actions taken.
