# FR4.3.6: Asset Seeder Classification V2

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

To achieve higher accuracy, a more sophisticated, multi-pass classification strategy is required. This approach will involve layering rules from most specific to most general, ensuring that high-confidence patterns are matched first.

### 3.1. Multi-Pass Classification Logic

The `_classify_asset` function should be refactored to execute rules in the following order:

1.  **Pass 1: High-Confidence Stock Indicators**: First, check for definitive stock keywords that are rarely, if ever, found in bond names. This prevents stocks from being misclassified as bonds.
    *   **Keywords**: `LIMITED RE`, `RIGHTS ENT`, `OFS` (Offer For Sale), `PP` (Partly Paid, when not part of a bond-like pattern), `WARRANTS`.
    *   If a match is found, classify as **STOCK** and exit.

2.  **Pass 2: High-Confidence Bond Indicators (NSE & BSE)**: Check for patterns that are almost exclusively used for bonds.
    *   **NSE Series**: `N1`-`N9`, `NB`-`NZ`, `IV`, `GV`, `TB`, `GB`.
    *   **SGBs**: Tickers starting with `SGB`.
    *   **BSE Patterns**: Names containing explicit terms like `NCD`, `DEBENTURE`, `PERP`, `STATE`, `ELEC BOARD`, `POWER CORPORATION`.
    *   If a match is found, classify as **BOND** and exit.

3.  **Pass 3: Name-Based Heuristics for BSE Bonds**: For remaining BSE assets, apply a more nuanced check that combines patterns. This is where the majority of the improvement will occur.
    *   **Rule A (Finance Bonds)**: If the name contains "FINANCE", "FINCORP", or "FIN" **AND** also contains a series indicator (`SR-`, `SR `), a coupon rate (`%`, or a number pattern), or a maturity date (month/year), classify as **BOND**. This will correctly classify the "KOSAMATTAM" and "MUTHOOTTU" series without incorrectly flagging finance company stocks.
    *   **Rule B (General Corporate Bonds)**: If the name contains a month name (`JAN`, `FEB`, etc.) or a year, **AND** it does **NOT** contain common stock-only terms like `INDUSTRIES`, `MANUFACTURING`, `TECHNOLOGIES`, `SYSTEMS`, `PROJECTS`, etc., classify as **BOND**. This is a refinement of the current logic, adding more exclusions to reduce false positives.

4.  **Pass 4: Default Classification**: If none of the above rules match, the asset is classified as **STOCK** by default.

### 3.2. Implementation Details

*   **File to Modify**: `backend/app/cli.py`
*   **Function to Refactor**: `_classify_asset`
*   The implementation will require creating more detailed keyword lists for both inclusion and exclusion to make the heuristics in Pass 3 effective.

## 4. Task Prioritization

This FR is designated as a follow-up task. The current asset seeding is functional enough for ongoing development. This refactoring should be scheduled after the completion of `FR4.3.5_bond_tracking_v2.md` to avoid further delays on the main feature track.
