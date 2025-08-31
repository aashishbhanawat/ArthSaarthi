# Feature Plan: Add New Data Import Parsers (FR7.1.2, FR7.1.3)

**Feature ID:** FR7.1.2, FR7.1.3
**Title:** Add New Data Import Parsers for MF CAS and eNPS
**User Story:** As a user, I want to import my Mutual Fund statements (CAS) and my National Pension System (NPS) statements so that I can automate the tracking of these critical investments.

---

## 1. Objective & Phased Approach

This document outlines the implementation plan for adding new, specific parsers to the existing "Automated Data Import" framework.

The goal is to create two new parsers:
1.  A parser for Consolidated Account Statements (CAS) for Mutual Funds, typically provided by CAMS or Karvy.
2.  A parser for eNPS statements.

This will be a multi-phase project:
*   **Phase 0 (Prerequisite):** Enhance the core system to robustly handle manual MF transactions, including integrating a reliable NAV data source.
*   **Phase 1:** Implement the backend parser for MF CAS statements.
*   **Phase 2:** Implement the backend parser for eNPS statements.

---

## 2. Technical Design & Architecture

This workstream will build upon the existing **Parser Strategy Pattern** located in `backend/app/services/import_parsers/`.

### 2.1. Core Concepts

*   **`BaseParser`:** All new parsers must inherit from the `BaseParser` abstract class and implement its `parse` method.
*   **`ParserFactory`:** The new parsers must be registered in the `ParserFactory` in `parser_factory.py` to make them available to the application via the API.
*   **Isolation:** This task is low-risk as it involves adding new files and does not modify existing database models, API endpoints, or core business logic.

### 2.2. New Dependencies

*   Parsing PDF files will likely require a new Python dependency. A library like `pdfplumber` is recommended as it is modern and effective at extracting text and table data from PDFs. This dependency must be added to `backend/requirements.txt`.

---

## 3. Implementation Plan (Phase 0: Prerequisite - Manual MF Transaction Enhancements)

**Objective:** Ensure the system can correctly handle manual MF transactions before automating the import process. This is a critical prerequisite.

➡️ **For a detailed breakdown of this phase, please see the dedicated feature plan: FR4.3.1 Manual Mutual Fund Transaction Management.**

---
## 4. Implementation Plan (Future Phases)

This feature will be implemented in two distinct phases, one for each parser.

### Phase 1: MF CAS Parser (FR7.1.2)

**Objective:** Implement a parser for Mutual Fund Consolidated Account Statements (CAS).

#### 4.1. New Files to Create

*   **Parser:** `backend/app/services/import_parsers/mf_cas_parser.py`
*   **Unit Test:** `backend/app/tests/services/test_mf_cas_parser.py`
*   **Test Asset:** `backend/app/tests/assets/sample_cas.pdf` (A sample, anonymized CAS PDF file must be obtained and added for testing).

#### 4.2. Implementation Steps

1.  **Add Dependency:** Add `pdfplumber` to `backend/requirements.txt`.
2.  **Analyze CAS Format:** Analyze the structure of a typical CAMS/Karvy CAS PDF to identify how transaction data is presented.
3.  **Implement `MfCasParser`:**
    *   Create the `MfCasParser` class inheriting from `BaseParser`.
    *   Implement the `parse` method. This method will use `pdfplumber` to open the PDF, iterate through its pages, and extract the transaction rows.
    *   The logic must correctly identify and parse fields like Fund Name, ISIN, Transaction Date, Transaction Type (Purchase, Redemption, etc.), Amount, Units, and NAV.
    *   The method must return a list of `ParsedTransaction` Pydantic models.
4.  **Register Parser:** Add the `MfCasParser` to the `ParserFactory` in `parser_factory.py` with a key like `'cams_karvy_cas'`.
5.  **Write Unit Tests:** Create a comprehensive unit test in `test_mf_cas_parser.py` that uses the `sample_cas.pdf` to verify that the parser correctly extracts and transforms the data.

---

### Phase 2: eNPS Parser (FR7.1.3)

**Objective:** Implement a parser for eNPS transaction statements.

#### 4.3. New Files to Create

*   **Parser:** `backend/app/services/import_parsers/enps_parser.py`
*   **Unit Test:** `backend/app/tests/services/test_enps_parser.py`
*   **Test Asset:** `backend/app/tests/assets/sample_enps.pdf` (A sample, anonymized eNPS statement must be obtained and added for testing).

#### 4.4. Implementation Steps

1.  **Analyze eNPS Format:** Analyze the structure of a typical eNPS statement to identify how contribution data is presented.
2.  **Implement `EnpsParser`:**
    *   Create the `EnpsParser` class inheriting from `BaseParser`.
    *   Implement the `parse` method using `pdfplumber` to extract contribution details.
    *   The logic must correctly identify and parse fields like Contribution Date, Amount, and the different fund allocations (Equity, Corporate Debt, Government Bonds).
    *   The method must return a list of `ParsedTransaction` Pydantic models.
3.  **Register Parser:** Add the `EnpsParser` to the `ParserFactory` in `parser_factory.py` with a key like `'enps_statement'`.
4.  **Write Unit Tests:** Create a comprehensive unit test in `test_enps_parser.py` that uses the `sample_enps.pdf` to verify that the parser correctly extracts and transforms the data.

---
