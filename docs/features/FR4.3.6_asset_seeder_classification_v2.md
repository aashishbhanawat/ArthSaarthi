# FR4.3.6: Asset Seeder Classification V2

**Status: ✅ Done**

## 1. Introduction

This document outlines the need for a second version of the asset classification logic within the `seed-assets` command. While the current seeder has been significantly improved, analysis of the logs shows persistent misclassifications for certain BSE-listed assets. This FR proposes a more advanced, multi-pass approach to resolve these issues.

**Related FRs**: FR4.3.5

## 2. Problem Description

The current classification logic in `_classify_asset` in `backend/app/cli.py` still faces two primary challenges:

1.  **Bonds Incorrectly Classified as STOCK**: Many corporate bonds, especially from finance companies (e.g., KOSAMATTAM, MUTHOOTTU MINI), are misclassified as "STOCK". This is because the current logic has a broad exclusion for names containing "LTD" or "LIMITED", which overrides other strong bond indicators like series numbers (`SR-II`), coupon rates (`9.5%`), or option indicators (`OPT III`).
    *   **Examples from log**: `0KFL16B` (KOSAMATTAM FINANCE Ltd SR-II), `12MMFL18D` (MUTHOOTTU MINI FIN LTD IV), `895PNBPER` (PUNJAB NATIONAL BANK SR-VIII), `9MFL30A` (MUTHOOT FINCORP LTD SR IV), `10KFL22` (KOSAMATTAM FINANCE LTD 10 LOA).

2.  **Stocks Incorrectly Classified as BOND**: The logic for identifying bonds based on keywords is sometimes too general. It incorrectly flags regular stocks as "BOND" if their names contain common bond-related terms (e.g., month names, "ELEC", "CORP").
    *   **Examples from log**: `KUMARWI` (KUMAR WIRE CLOTH MANUFACTURING), `LAKSELEC` (LAKSHMI ELECTRICAL CONTROL SYS), `SPITZE` (MARUTI INTERIOR PRODUCTS LTD), `AURUMPPCM` (AURUM PROPTECH PP OF RS. 30), `MOLDTEKPP` (MOLD TEK PACKAGING PP RS 1.25), `NOVARTIS` (NOVARTIS INDIA LIMITED OFS).

These issues indicate that the current single-pass, rule-based system has reached its limit and requires a more structured approach.

## 3. Proposed Solution

To achieve higher accuracy, we will move from a single-source heuristic model to a **multi-source, authoritative-first seeding strategy**. This involves creating a new, orchestrated seeding process that prioritizes official exchange and depository lists. The heuristic-based classification will be relegated to a final fallback for assets not found in any authoritative source. This section outlines the final, definitive order of operations.

### 3.1. New Multi-Source Seeding Workflow

The `seed-assets` command will be refactored to execute the following phases in a strict, sequential order:

1.  **Phase 1: Seed from Master Debt Lists (Highest Priority)**
    *   **Purpose:** To build a foundational database of all known debt instruments. These are the most authoritative and comprehensive sources for bonds.
    *   **Source 1: NSDL Debt Instruments List.** Process the entire NSDL master list. Any asset with an ISIN found here is definitively classified as a `BOND` and enriched with its metadata (coupon, maturity, etc.).
        *   **Analysis:** This is an Excel file (`.xls`). It is a highly authoritative source.
        *   **Data Mapping:** `ISIN` -> `Asset.isin`, `NAME_OF_THE_INSTRUMENT` -> `Asset.name`, `REDEMPTION` -> `Bond.maturity_date`, `FACE_VALUE` -> `Bond.face_value`, `COUPON_RATE` -> `Bond.coupon_rate`, `FREQUENCY_OF_THE_INTEREST_PAYMENT` -> `Bond.interest_frequency`.

    *   **Source 2: BSE Public Debt Issues.** Process the `Public Bond.xlsx` file. Any new asset found here is also definitively classified as a `BOND` and enriched.
        *   **Analysis:** This is an Excel file containing bonds issued to the public via BSE.
        *   **Data Mapping:** `ISIN` -> `Asset.isin`, `Scrip_ Code` -> `Asset.ticker_symbol`, `Scrip_Long_Name` -> `Asset.name`, `Interest_Rate` -> `Bond.coupon_rate`, `Conversion_Date` -> `Bond.maturity_date`, `Scrip_Face_Value` -> `Bond.face_value`.

2.  **Phase 2: Seed from Daily Exchange Bhavcopy (Classification & Pricing)**
    *   **Purpose:** To capture all actively traded securities and classify them with high confidence using exchange-provided series codes. This phase is critical for both equities and exchange-traded debt.
    *   **Source 3: BSE Equity Bhavcopy (Standardized).** Process the new `BhavCopy_BSE_CM_...` file. Use the `SctySrs` column to definitively classify assets as `STOCK`, `ETF`, `GOVERNMENT_BOND`, or `BOND`.
        *   **Analysis:** A standardized CSV for the BSE Cash Market. It contains all traded instruments, not just equities.
        *   **Classification Logic:** Series `A`, `B`, `T` -> `STOCK`; `E` -> `ETF`; `G` -> `GOVERNMENT_BOND`; `F` -> `BOND`.
        *   **Data Mapping:** `ISIN` -> `Asset.isin`, `TckrSymb` -> `Asset.ticker_symbol`, `FinInstrmNm` -> `Asset.name`, `ClsPric` -> `Asset.current_price`.

    *   **Source 4: NSE Equity Bhavcopy.** Process the daily NSE bhavcopy. Use the series code to classify assets as `STOCK` or `ETF`.

3.  **Phase 3: Seed from Specialized Daily Debt Lists**
    *   **Purpose:** To capture any newly listed debt instruments that might not have appeared in the master lists or bhavcopy yet.
    *   **Source 5: NSE Daily Debt Listing.** Process the `New_debt_listing.xlsx`. Use the `ISSUE_TYPE` column to definitively classify new assets as `BOND`, `GOVERNMENT_BOND`, or `TBILL`.
        *   **Analysis:** A delimited text file listing newly listed debt on NSE.
        *   **Classification Logic:** `NCD`, `CP` -> `CORPORATE_BOND`; `GS`, `SB` -> `GOVERNMENT_BOND`; `Tbills` -> `TBILL`.
        *   **Data Mapping:** `ISIN_CODE` -> `Asset.isin`, `ISSUE_DESC` -> `Asset.name`, `COUPON_RATE` -> `Bond.coupon_rate`, `MAT_DT` -> `Bond.maturity_date`.

    *   **Source 6: BSE Debt Bhavcopy (Legacy Zip).** Process the three CSVs inside the `DEBTBHAVCOPY...zip`. This is a good source for retail and wholesale debt, providing another layer of confirmation.
        *   **Analysis:** A zip archive containing multiple CSVs for different debt market segments.
        *   **Classification Logic:** Assets in `fgroup*.csv` and `icdm*.csv` are `BOND` (Corporate). Assets in `wdm*.csv` are `GOVERNMENT_BOND` or `TBILL`.

4.  **Phase 4: Seed Market Indices**
    *   **Purpose:** To populate the database with trackable market indices. This is a separate asset class and does not conflict with the others.
    *   **Source 7: BSE Index Summary.** Process the `INDEXSummary_...csv` file. All items found here are classified as `INDEX`.
        *   **Analysis:** A CSV file containing end-of-day values for all BSE indices.
        *   **Data Mapping:** `IndexID` -> `Asset.ticker_symbol`, `IndexName` -> `Asset.name`, `ClosePrice` -> `Asset.current_price`.

5.  **Phase 5: Fallback to General-Purpose Master File (Lowest Priority)**
    *   **Purpose:** To catch any remaining assets not found in any of the authoritative sources.
    *   **Source 8: ICICI Direct Security Master.** Process the original, general-purpose master file.
    *   **De-duplication:** If an asset from this file (by ISIN or ticker) already exists in our database from the previous phases, it is **skipped**. This prevents the less reliable source from misclassifying an asset we already have high confidence in.
    *   **Heuristic Classification:** For any truly new assets found only in this file, we will apply a multi-pass heuristic classification logic.

### 3.2. Heuristic Classification Logic (for Fallback Use Only)

The `_classify_asset` function will be refactored to execute the following rules for assets processed in Phase 5.

1.  **Pass 1: High-Confidence Stock Indicators**: Check for definitive stock keywords (`LIMITED RE`, `RIGHTS ENT`, `OFS`, `PP`, `WARRANTS`). If a match is found, classify as **STOCK** and exit.

2.  **Pass 2: High-Confidence Bond Indicators**: Check for patterns that are almost exclusively used for bonds (NSE Series `N1-N9`, `NB-NZ`, etc.; SGB patterns; BSE patterns like `NCD`, `DEBENTURE`). If a match is found, classify as **BOND** and exit.

3.  **Pass 3: Name-Based Heuristics for BSE Bonds**: For remaining BSE assets, apply a more nuanced check.
    *   **Rule A (Finance Bonds)**: If the name contains "FINANCE", "FINCORP", or "FIN" **AND** also contains a series indicator (`SR-`, `SR `), a coupon rate (`%`, or a number pattern), or a maturity date (month/year), classify as **BOND**. This will correctly classify the "KOSAMATTAM" and "MUTHOOTTU" series without incorrectly flagging finance company stocks.
    *   **Rule B (General Corporate Bonds)**: If the name contains a month name (`JAN`, `FEB`, etc.) or a year, **AND** it does **NOT** contain common stock-only terms like `INDUSTRIES`, `MANUFACTURING`, `TECHNOLOGIES`, `SYSTEMS`, `PROJECTS`, etc., classify as **BOND**. This is a refinement of the current logic, adding more exclusions to reduce false positives.

4.  **Pass 4: Default Classification**: If none of the above heuristic rules match, the asset is classified as **STOCK** by default.

### 3.2. Implementation Details

*   **File to Modify**: `backend/app/cli.py`.
*   **Function to Refactor**: `_classify_asset`. The function signature and return value must be updated. It should return a tuple of `(asset_type, bond_type)`, where `bond_type` is populated if the asset is a bond (e.g., `SGB`, `TBILL`, `CORPORATE`) and `None` otherwise.
*   The implementation will require creating more detailed keyword lists for both inclusion and exclusion to make the heuristics in Pass 3 effective.

## 4. Task Prioritization

This FR is designated as a follow-up task. The current asset seeding is functional enough for ongoing development. This refactoring should be scheduled after the completion of `FR4.3.5_bond_tracking_v2.md` to avoid further delays on the main feature track.
