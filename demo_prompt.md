### **ArthSaarthi Full-Stack QA, User Guide & Demo Video Generation Prompt**

**Objective:**
Perform an exhaustive QA run on the ArthSaarthi application hosted at `https://librephotos.aashish.ai.in/`. 
To prevent context window bloat and ensure high-quality outputs, this task is strictly divided into **Sub-Tasks (Phases)**. 

**CRITICAL RULE:** You MUST pause and wait for the user to type "Continue" before moving from one phase to the next. Do NOT attempt to execute all phases at once. You must not work continuously for hours.

**Outputs Required (to be saved in `temp_qa_run/` directory):**
1. `USER_GUIDE.md`: A detailed, step-by-step User Guide/Manual with screenshots.
2. `DEMO_VIDEO_SCRIPT.md`: A demo video script with voiceover text and timestamps (for YouTube).
3. All captured WebP videos and screenshots.
*Note: The User Guide and Demo Video script should be completely independent of each other. Both should detail how to use the app extensively. You may refer to the existing user guide for context.*

---

### **Phase 1: Setup & Login**
**Action:** Access the application, setup the initial account, and log in. Execute ONE BY ONE:
1.  **Initial Setup:** Navigate to the application URL. Complete the first-time setup form to create the administrator account. Capture the setup screen.
2.  **Login:** Log in with the newly created credentials. Capture the login page and the initial empty dashboard state.
*   **Tasks for Agent:**
    - Capture screenshots and WebP videos for EVERY action using `RecordingName`.
    - Write the draft content for the User Guide and Demo Script for Phase 1.
    - **PAUSE AND WAIT FOR USER INSTRUCTION.**

---

### **Phase 2: Portfolios, Assets & Transactions**
**Action:** Create portfolios and log transactions using real historical data. Execute these actions ONE BY ONE:
1.  **Portfolio Management:** Navigate to Portfolios. Click 'Create Portfolio', name it, and save. Capture the process.
2.  **Indian Equity Transactions:** Click 'Add Transaction' -> Select 'Stock'. Add historical BUY/SELL transactions for: RELIANCE (Large Cap, Energy), HDFCBANK (Large Cap, Banking), INFY (Large Cap, IT), TATAMOTORS (Large Cap, Auto), DRREDDY (Pharma), HAPPISTMND (Small Cap, IT). Capture the UI for each type of transaction.
3.  **Mutual Funds:** Add 'Lumpsum' transactions for an Equity Index Fund (e.g., Nifty 50) and a Debt Fund (e.g., Liquid Fund).
4.  **Fixed Income (FD/RD/PPF/Bonds):** Detail step-by-step how to add each type:
    - Add a Fixed Deposit (FD).
    - Add a Recurring Deposit (RD).
    - Add a Public Provident Fund (PPF) contribution.
    - Add a Bond transaction.
5.  **ESPP/RSU (Global Assets):** Click 'Add ESPP/RSU Award'. Use Foreign assets (e.g., AAPL, GOOGL, MSFT) to demonstrate logging ESPP and RSU transactions (include a "Sell to Cover" scenario).
6.  **Edit/Delete Transactions:** Edit one of the existing transactions and save. Then, delete a sample transaction to show how deletion works.
*   **Tasks for Agent:**
    - Capture screenshots and WebP videos for EVERY action using `RecordingName`.
    - Write the draft content for the User Guide and Demo Script for Phase 2.
    - **PAUSE AND WAIT FOR USER INSTRUCTION.**

---

### **Phase 3: Dashboards, Analytics & Drill-Downs**
**Action:** Explore the analytical features based on the data entered in Phase 2. Execute ONE BY ONE:
1.  **Dashboard Overview:** Navigate to the main Dashboard. Capture the Portfolio History chart, Asset Allocation pie charts, and Top Movers. Explain how they aggregate data.
2.  **Portfolio Advanced Analytics:** Navigate to the specific portfolio page. Capture and explain the Advanced Analytics (XIRR, Sharpe Ratio) and Diversification Analysis (Sector, Market Cap, Geography).
3.  **Benchmark Comparison:** Scroll to the Benchmark widget. Toggle and capture different benchmarks: standard (Nifty 50), Hybrid indices, and Risk-Free. Explain how it compares alpha.
4.  **Holding Drill-Down:** On the holdings table, click into an Equity holding, then click into a Debt holding. Capture the modal showing specific constituent transactions (tax lots) and remaining quantities.
5.  **Transaction History:** Navigate to the main 'Transactions' tab. Apply a date filter and an asset type filter. Capture the results and explain the filtering capabilities.
*   **Tasks for Agent:**
    - Capture screenshots and videos for EVERY action.
    - Write the draft content for the User Guide and Demo Script for Phase 3.
    - **PAUSE AND WAIT FOR USER INSTRUCTION.**

---

### **Phase 4: Capital Gains & Reporting**
**Action:** Generate tax and income reports. Execute ONE BY ONE:
1.  **Capital Gains Page:** Navigate to Analytics -> Capital Gains. Select FY 2025-26. Capture the summary. Explain the Short Term (STCG) and Long Term (LTCG) tabs.
2.  **Schedule FA:** Click the Schedule FA tab. Explain how it generates foreign asset reporting (capturing your AAPL/GOOGL data).
3.  **Dividend Report:** Click the Dividend Report tab. Explain how it categorizes dividends into quarterly advance tax buckets.
*   **Tasks for Agent:**
    - Capture screenshots and videos for EVERY action.
    - Write the draft content for the User Guide and Demo Script for Phase 4.
    - **PAUSE AND WAIT FOR USER INSTRUCTION.**

---

### **Phase 5: Import, Watchlist & Goals**
**Action:** Test and document peripheral features. Execute ONE BY ONE:
1.  **Data Import:** Navigate to Import. Select Generic CSV. Upload the existing `sample_generic_import.csv` file located in the project directory. 
2.  **Staging & Mapping:** Capture the staging preview. Show exactly how to handle an `UNKNOWN_TICKER_TEST` by clicking map, assigning it to a valid asset (e.g., ITC), and then committing the valid transactions to the database.
3.  **Watchlist:** Navigate to Watchlists. Create a new watchlist. Search for and add 3 assets you don't currently own. Capture the UI.
4.  **Goals:** Navigate to Goals. Create a financial goal (e.g., "Retirement"). Link your newly created portfolio to this goal. Capture the progress visualization.
*   **Tasks for Agent:**
    - Capture screenshots and videos for EVERY action.
    - Write the draft content for the User Guide and Demo Script for Phase 5.
    - **PAUSE AND WAIT FOR USER INSTRUCTION.**

---

### **Phase 6: Administration & Settings**
**Action:** Navigate through the application settings and capture media. Execute ONE BY ONE:
1.  **User Management:** Navigate to Admin -> User Management. Explain server-mode user creation/editing/deletion. Explicitly detail how users cannot access each other's data (data isolation), and note this feature is not supported in desktop mode.
2.  **Interest Rate Management:** Navigate to Admin -> Interest Rates. Explain how to configure and manage interest rates.
3.  **System Maintenance:** Navigate to Admin -> System Maintenance. Explain how Asset Seeding works and click the button to trigger it.
4.  **Symbol Aliases:** Navigate to Admin -> Symbol Aliases. Explain how mapping works and how to edit/manage existing symbol aliases.
5.  **FMV 2018 Management:** Navigate to Admin -> FMV 2018. Explain how to manage the Fair Market Value for 2018 (Grandfathering rules).
6.  **Profile & Settings:** Navigate to your Profile. Explain how to change the user password. Then, demonstrate performing a data Backup and a Restore.
7.  **UI Toggles:** Toggle the Dark Theme on and off. Then, toggle the global "Privacy Mode" (eye icon) and explain how it obscures monetary values across all pages.
*   **Tasks for Agent:**
    - Capture screenshots and videos for EVERY action.
    - Write the draft content for the User Guide and Demo Script for Phase 6.
    - **PAUSE AND WAIT FOR USER INSTRUCTION.**

---

### **Phase 7: Final Compilation & Export**
**Action:** Consolidate all drafted content.
*   **Demo Videos (CRITICAL):** You **must** utilize the `RecordingName` parameter in the `browser_subagent` tool for every major workflow to save WebP videos.
*   **Tasks for Agent:**
    - Create the directory `temp_qa_run` if it does not exist.
    - Compile all User Guide sections into `temp_qa_run/USER_GUIDE.md`. Ensure it is detailed, step-by-step, independent of the video script, and references the captured screenshots.
    - Compile all Demo Video Scripts into `temp_qa_run/DEMO_VIDEO_SCRIPT.md`. Ensure it is independent, structured for YouTube, and includes voiceover text paired with visual cues/timestamps mapping to the actions taken.
    - Copy/move all captured screenshots and `.webp` videos into the `temp_qa_run/` directory.
    - Confirm total task completion to the user.

---

### **Summary of Expectations for Final Deliverables (`temp_qa_run/`):**
1. `USER_GUIDE.md`: Step-by-step app manual covering all 20 required areas.
2. `DEMO_VIDEO_SCRIPT.md`: Video timeline, actions to be seen on screen, and the exact voiceover script.
3. All associated image and video artifact files generated by the testing agent.
