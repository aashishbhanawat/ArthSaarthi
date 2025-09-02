# Feature Plan: Add New Data Import Parsers (FR7.1.2, FR7.1.3)

**Feature ID:** FR7.1.2, FR7.1.3
**Title:** Add New Data Import Parsers for MF CAS and eNPS
**User Story:** As a user, I want to import my Mutual Fund statements (CAS) and my National Pension System (NPS) statements so that I can automate the tracking of these critical investments.
**Status:** 📝 Planned

---

## 1. Objective & Phased Approach

This document outlines the implementation plan for adding new, specific parsers to the existing "Automated Data Import" framework.

The goal is to create two new parsers:
1.  A parser for Consolidated Account Statements (CAS) for Mutual Funds, typically provided by CAMS or Karvy.
2.  A parser for eNPS statements.

This will be a multi-phase project:
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

## 3. Implementation Plan (Phase 1: MF CAS Parser)

**Objective:** Implement a parser for Mutual Fund Consolidated Account Statements (CAS).

1.  **Add Dependency:** Add `pdfplumber` to `backend/requirements.txt`.
2.  **Analyze CAS Format:** Analyze the structure of a typical CAMS/Karvy CAS PDF to identify how transaction data is presented.
3.  **Implement `MfCasParser`:**
    *   Create `backend/app/services/import_parsers/mf_cas_parser.py`.
    *   Implement the `parse` method using `pdfplumber` to open the PDF, iterate through its pages, and extract the transaction rows.
    *   The logic must correctly identify and parse fields like Fund Name, ISIN, Transaction Date, Transaction Type (Purchase, Redemption, etc.), Amount, Units, and NAV.
    *   The method must return a list of `ParsedTransaction` Pydantic models.
4.  **Register Parser:** Add the `MfCasParser` to the `ParserFactory` in `parser_factory.py` with a key like `'cams_karvy_cas'`.
5.  **Write Unit Tests:** Create `backend/app/tests/services/test_mf_cas_parser.py` and add a comprehensive unit test that uses a sample, anonymized CAS PDF to verify that the parser correctly extracts and transforms the data.

---

## 4. Testing Plan

This feature will be validated through a multi-layered testing strategy.

### 4.1. Backend Unit Tests

*   **`test_mf_cas_parser.py`:**
    *   A dedicated unit test will be created for the `MfCasParser`.
    *   It will use a sample, anonymized CAS PDF file as input.
    *   The test will assert that the `parse` method returns the correct number of transactions.
    *   It will verify the accuracy of key fields (fund name, date, amount, units, NAV) for a sample transaction.
    *   Edge cases like handling password-protected PDFs (expecting a graceful failure) and malformed PDFs will be tested.

### 4.2. Backend Integration Tests

*   **`test_import_sessions.py`:**
    *   An integration test will be added to verify that the `ParserFactory` correctly identifies and uses the new `MfCasParser`.
    *   The test will upload a sample CAS PDF to the `POST /api/v1/import-sessions/` endpoint with the `source_type` set to `'cams_karvy_cas'`.
    *   It will then call the preview endpoint and assert that the returned data is correctly parsed, confirming the end-to-end integration of the new parser.

### 4.3. E2E Tests (Playwright)

*   A new test case will be added to `e2e/tests/data-import.spec.ts`.
*   The test will simulate the full user flow:
    1.  Log in and navigate to the "Import" page.
    2.  Select a portfolio and choose "MF CAS Statement" from the dropdown.
    3.  Upload a sample CAS PDF file.
    4.  Verify that the preview page displays the correctly parsed transactions.
    5.  Commit the transactions and verify that the new holdings appear correctly in the portfolio's holdings table.