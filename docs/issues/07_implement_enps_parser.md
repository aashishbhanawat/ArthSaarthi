---
name: '🚀 Feature Request'
about: 'Implement PDF parser for eNPS statements'
title: 'feat: Implement PDF parser for eNPS statements'
labels: 'enhancement, feature, epic:data-import'
assignees: ''
---

### 1. User Story

**As a** user with NPS investments,
**I want to** import my eNPS transaction statement PDF,
**so that** I can automatically log my contributions without manual entry.

---

### 2. Functional Requirements

*   [ ] The system must implement a new parser for eNPS transaction statements.
*   [ ] The parser must be able to handle password-protected PDFs by prompting the user for the password.
*   [ ] The parser must extract key transaction details: Contribution Date, Amount, and fund allocation details.
*   [ ] The new parser must be integrated into the existing Data Import framework and selectable from the UI.

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1:** Given I am on the "Import" page, when I select "eNPS Statement" and upload a password-protected PDF, then I should be prompted to enter the password.
*   [ ] **Scenario 2:** Given I have provided the correct password for an eNPS PDF, when I view the import preview, then all contributions from the PDF should be correctly parsed and displayed.
*   [ ] **Scenario 3:** Given I commit the parsed transactions, when I navigate to my portfolio, then the `current_balance` of the corresponding NPS asset should be updated.

---

### 4. Dependencies

*   This feature depends on the completion of manual NPS asset tracking (`FR4.3.4`).

---

### 5. Additional Context

*   **Requirement ID:** `(FR7.1.3)`
*   A sample, anonymized eNPS statement will be needed for testing.

