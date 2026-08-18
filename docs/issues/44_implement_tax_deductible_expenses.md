---
name: '🚀 Feature Request'
about: 'Log tax-deductible expenses and track statutory section limits'
title: 'feat: Implement Tax-Deductible Expense & Investment Logging (FR16.3)'
labels: 'enhancement, feature, epic:tax-readiness'
assignees: ''
---

**Release: v1.4.0 (Tax Readiness & Full Financial Picture)**
**GitHub Issue:** #518

### 1. User Story

**As a** taxpayer,  
**I want to** log tax-deductible expenses and eligible investments under Chapter VI-A,  
**so that** I can track section limits (such as Section 80C, 80D, 80CCD) and maximize tax savings.

---

### 2. Functional Requirements

*   [ ] Support statutory tax deduction categories:
    *   **Section 80C:** PPF, EPF, ELSS, Life Insurance, School Tuition Fee, Home Loan Principal (Max ₹1.5L).
    *   **Section 80D:** Health Insurance Premiums & Preventive Health Checkups (Self/Family ₹25k/₹50k, Parents ₹25k/₹50k).
    *   **Section 80CCD(1B):** Additional NPS contribution (Max ₹50,000).
    *   **Section 80TTA / 80TTB:** Savings account interest deduction (₹10k for non-seniors / ₹50k for seniors).
    *   **Custom Category:** Other Chapter VI-A deductions (80E, 80G, 80GG).
*   [ ] Allow logging deduction entries with financial year, category, section, amount, proof notes, and date.
*   [ ] Display statutory limit utilization progress bars (e.g., 80C: ₹1,20,000 / ₹1,50,000 used).
*   [ ] Provide CRUD API endpoints (`/api/v1/tax/deductions`).

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1 (Deduction Ceiling Capping):** Given ₹1,80,000 total 80C entries logged, the UI displays total investments as ₹1.8L while capping eligible tax deduction at statutory limit ₹1.5L.
*   [ ] **Scenario 2 (Auto-linking PPF/ELSS):** System optionally allows tagging existing PPF contributions or ELSS buys as 80C investments.

---

### 4. Dependencies

*   Interoperates with PPF tracking (FR4.3.4) and Mutual Funds transactions (FR4.3.1).

---

### 5. Additional Context

*   **Requirement ID:** `(FR16.3)`
*   This is part of Release v1.4.0 (Tax Readiness & Full Financial Picture).
