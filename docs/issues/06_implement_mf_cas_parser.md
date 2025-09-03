---
name: '🚀 Feature Request'
about: 'Implement PDF parser for Mutual Fund CAS statements'
title: 'feat: Implement PDF parser for Mutual Fund CAS statements'
labels: 'enhancement, feature, epic:data-import'
assignees: ''
---

### 1. User Story

**As a** user with mutual fund investments,
**I want to** import my Consolidated Account Statement (CAS) PDF,
**so that** I can automatically log all my MF transactions without manual entry.

---

### 2. Functional Requirements

*   [ ] The system must implement a new parser for CAMS/Karvy style CAS PDFs.
*   [ ] The parser must be able to handle password-protected PDFs by prompting the user for the password.
*   [ ] The parser must extract key transaction details: Fund Name, ISIN, Transaction Date, Transaction Type (Purchase, Redemption, etc.), Amount, Units, and NAV.
*   [ ] The new parser must be integrated into the existing Data Import framework and selectable from the UI.

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1:** Given I am on the "Import" page, when I select "MF CAS Statement" and upload a password-protected PDF, then I should be prompted to enter the password.
*   [ ] **Scenario 2:** Given I have provided the correct password for a CAS PDF, when I view the import preview, then all transactions from the PDF should be correctly parsed and displayed.
*   [ ] **Scenario 3:** Given I commit the parsed transactions, when I navigate to my portfolio, then the new MF holdings should be correctly reflected.

---

### 4. Dependencies

*   This feature depends on the completion of manual Mutual Fund transaction support (`FR4.3.1`), which is already done.

---

### 5. Additional Context

*   **Requirement ID:** `(FR7.1.2)`
*   This feature will require adding a new Python dependency for PDF parsing, such as `pdfplumber`.
*   A sample, anonymized CAS PDF will be needed for testing.

