---
name: '🚀 Feature Request'
about: 'Enhance import engine to support Excel, HTML, TXT, and DBF file formats'
title: 'feat: Enhance import engine to support Excel, HTML, TXT, and DBF file formats'
labels: 'enhancement, feature, epic:data-import'
assignees: ''
---

### 1. User Story

**As a** user who receives brokerage statements in various formats,
**I want to** be able to import Excel, HTML, TXT, and DBF files directly,
**so that** I don't have to manually convert them to CSV before importing.

---

### 2. Functional Requirements

*   [ ] The `ParserFactory` must be enhanced to recognize and route different file extensions (`.xlsx`, `.xls`, `.html`, `.txt`, `.dbf`).
*   [ ] Implement a new parser to handle Excel files (`.xlsx`, `.xls`), likely using a library like `openpyxl` or `pandas`.
*   [ ] Implement a new parser to handle HTML files, specifically extracting data from `<table>` elements.
*   [ ] Implement a flexible parser for TXT files that can handle both delimited and fixed-width formats.
*   [ ] Implement a parser for DBF files, which are sometimes used by older trading software.

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1:** Given I upload an Excel file with transaction data, when I view the import preview, then the data from the first sheet should be correctly parsed and displayed.
*   [ ] **Scenario 2:** Given I upload an HTML file containing a single `<table>` with transaction data, when I view the import preview, then the table data should be correctly parsed and displayed.

---

### 4. Dependencies

*   This feature depends on the core data import framework (`FR7.1.1`).

---

### 5. Additional Context

*   **Requirement ID:** `(FR7.2)`
*   This feature will require adding new Python dependencies to `requirements.txt` for handling these formats (e.g., `openpyxl`, `lxml`, `dbf`).

