# Reference: Data Sources & Classification Logic

This document serves as a comprehensive reference for all external data sources used by the `seed-assets` command and the classification logic applied to them. It is the single source of truth for how assets are identified and categorized within the ArthSaarthi application.

## Seeding Workflow

The asset seeder operates on a **multi-source, authoritative-first** strategy. It processes data sources in a strict, sequential order of phases. Once an asset is identified and created from a high-priority source, it is skipped in subsequent, lower-priority phases.

1.  **Phase 1: Master Debt Lists** (Highest Priority)
2.  **Phase 2: Daily Exchange Bhavcopy**
3.  **Phase 3: Specialized Daily Debt Lists**
4.  **Phase 4: Market Indices**
5.  **Phase 5: Fallback General Master File** (Lowest Priority)

---

## Data Source Analysis

### Phase 1: Master Debt Lists

**Purpose:** To build a foundational database of all known debt instruments.

#### Source 1: NSDL Debt Instruments List
*   **URL:** `https://nsdl.co.in/download/debt_instruments/listed_isns.xls`
*   **Type:** Excel (`.xls`)
*   **Classification:** All assets in this file are definitively classified as **BOND**.
*   **Data Mapping:**
    *   `ISIN` -> `Asset.isin`
    *   `NAME_OF_THE_INSTRUMENT` -> `Asset.name`
    *   `REDEMPTION` -> `Bond.maturity_date`
    *   `FACE_VALUE` -> `Bond.face_value`
    *   `COUPON_RATE` -> `Bond.coupon_rate`
    *   `FREQUENCY_OF_THE_INTEREST_PAYMENT` -> `Bond.interest_frequency`

#### Source 2: BSE Public Debt Issues
*   **URL:** `https://www.bseindia.com/downloads1/bonds_data.zip` (contains `Public Bond.xlsx`)
*   **Type:** Excel (`.xlsx`)
*   **Classification:** All assets in this file are definitively classified as **BOND**.
*   **Data Mapping:**
    *   `ISIN` -> `Asset.isin`
    *   `Scrip_ Code` -> `Asset.ticker_symbol`
    *   `Scrip_Long_Name` -> `Asset.name`
    *   `Interest_Rate` -> `Bond.coupon_rate`
    *   `Conversion_Date` -> `Bond.maturity_date`
    *   `Scrip_Face_Value` -> `Bond.face_value`

### Phase 2: Daily Exchange Bhavcopy

**Purpose:** To capture all actively traded securities and classify them with high confidence using exchange-provided series codes.

#### Source 3: BSE Equity Bhavcopy (Standardized)
*   **URL:** `https://www.bseindia.com/markets/MarketInfo/BhavCopy.aspx` (e.g., `BhavCopy_BSE_CM_...`)
*   **Type:** CSV
*   **Classification Logic:** Based on `SctySrs` column:
    *   `A`, `B`, `T`, etc. -> **STOCK**
    *   `E` -> **ETF**
    *   `G` -> **GOVERNMENT_BOND**
    *   `F` -> **BOND** (Corporate)
*   **Data Mapping:** `ISIN` -> `Asset.isin`, `TckrSymb` -> `Asset.ticker_symbol`, `FinInstrmNm` -> `Asset.name`, `ClsPric` -> `Asset.current_price`.

#### Source 4: NSE Equity Bhavcopy
*   **URL:** `https://nsearchives.nseindia.com/content/historical/EQUITIES/...`
*   **Type:** CSV
*   **Classification Logic:** Based on `SERIES` column:
    *   `EQ` -> **STOCK**
    *   `BE` -> **ETF**

### Phase 3: Specialized Daily Debt Lists

**Purpose:** To capture any newly listed debt instruments.

#### Source 5: NSE Daily Debt Listing
*   **URL:** `https://nsearchives.nseindia.com/content/debt/New_debt_listing.xlsx`
*   **Type:** Delimited Text
*   **Classification Logic:** Based on `ISSUE_TYPE` column:
    *   `NCD`, `CP` -> **CORPORATE_BOND**
    *   `GS`, `SB` -> **GOVERNMENT_BOND**
    *   `Tbills` -> **TBILL**
*   **Data Mapping:** `ISIN_CODE` -> `Asset.isin`, `ISSUE_DESC` -> `Asset.name`, `COUPON_RATE` -> `Bond.coupon_rate`, `MAT_DT` -> `Bond.maturity_date`.

#### Source 6: BSE Debt Bhavcopy (Legacy Zip)
*   **URL:** `https://www.bseindia.com/markets/debt/BhavCopy_Debt.aspx` (e.g., `DEBTBHAVCOPY...zip`)
*   **Type:** Zip archive containing multiple CSVs.
*   **Classification Logic:**
    *   Assets in `fgroup*.csv` and `icdm*.csv` are **BOND** (Corporate).
    *   Assets in `wdm*.csv` are **GOVERNMENT_BOND** or **TBILL**.

### Phase 4: Market Indices

#### Source 7: BSE Index Summary
*   **URL:** `https://www.bseindia.com/markets/MarketInfo/BhavCopy.aspx` (e.g., `INDEXSummary_...csv`)
*   **Type:** CSV
*   **Classification:** All items in this file are classified as **INDEX**.
*   **Data Mapping:** `IndexID` -> `Asset.ticker_symbol`, `IndexName` -> `Asset.name`, `ClosePrice` -> `Asset.current_price`.

### Phase 5: Fallback General-Purpose Master File

#### Source 8: ICICI Direct Security Master
*   **URL:** `https://www.icicidirect.com/mailimages/NewSecurityMaster.zip`
*   **Type:** Delimited Text
*   **Classification:** This source is only used for assets not found in any of the above sources. A multi-pass heuristic classification logic is applied based on keywords in the asset's name.