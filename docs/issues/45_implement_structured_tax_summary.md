---
name: '🚀 Feature Request'
about: 'Generate a structured Financial Year Tax Readiness summary report and comparison'
title: 'feat: Implement Structured Tax Summary Report & Tax Profile Dashboard (FR16.4)'
labels: 'enhancement, feature, epic:tax-readiness'
assignees: ''
---

**Release: v1.4.0 (Tax Readiness & Full Financial Picture)**
**GitHub Issue:** #519

### 1. User Story

**As a** user planning my annual taxes,  
**I want a** consolidated Financial Year Tax Readiness summary report,  
**so that** I can view all gross income, TDS withheld, tax deductions, capital gains, and estimated net tax liability with Old vs New Tax Regime indicators.

---

### 2. Functional Requirements

*   [ ] Build a backend analytics aggregator combining:
    *   Total Gross Income & TDS credits (FR16.1/FR16.2).
    *   Eligible Chapter VI-A Deductions (FR16.3).
    *   Realized & Unrealized Capital Gains (FR6.5).
    *   Dividend and Interest Income (FR6.6).
*   [ ] Calculate tax estimation under both Old Tax Regime (with deductions) and New Tax Regime (Section 115BAC flat slabs + standard deduction).
*   [ ] Display net tax payable / refund status indicator.
*   [ ] Render mandatory legal disclaimer: *"This report is for informational purposes only and does not constitute formal tax or financial advice."*
*   [ ] Export tax summary report as structured PDF and CSV.

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1 (Old vs New Regime Comparison):** Given user's logged income and deductions, the dashboard displays side-by-side estimated tax liability under Old Regime vs New Regime and highlights the lower tax option.
*   [ ] **Scenario 2 (Disclaimer Compliance):** Every generated report (UI, PDF, CSV) includes the non-advisory legal disclaimer prominently.

---

### 4. Dependencies

*   Depends on FR6.5 (Capital Gains), FR6.6 (Dividends), FR16.1/16.2 (Income), and FR16.3 (Deductions).

---

### 5. Additional Context

*   **Requirement ID:** `(FR16.4)`
*   This is part of Release v1.4.0 (Tax Readiness & Full Financial Picture).
