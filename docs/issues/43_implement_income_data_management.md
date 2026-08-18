---
name: '🚀 Feature Request'
about: 'Log and track income sources, entries, and Tax Deducted at Source (TDS)'
title: 'feat: Implement Income Source & Entry Data Management with TDS Tracking (FR16.1 & FR16.2)'
labels: 'enhancement, feature, epic:tax-readiness'
assignees: ''
---

**Release: v1.4.0 (Tax Readiness & Full Financial Picture)**
**GitHub Issue:** #517

### 1. User Story

**As a** user tracking my financial health,  
**I want to** log all my income sources and individual income entries along with Tax Deducted at Source (TDS),  
**so that** I can maintain a full record of my annual gross earnings and tax credits.

---

### 2. Functional Requirements

*   [ ] Support user-defined income sources (e.g. Salary, Freelance Work, Rental Income, Interest, Dividends, Business/Professional).
*   [ ] Allow logging of individual income entries with gross amount, date received, payer name, income category, and TDS deducted.
*   [ ] Automatically calculate cumulative gross income and total TDS deducted per Financial Year (e.g., FY 2025-26).
*   [ ] Provide CRUD API endpoints for income sources (`/api/v1/income/sources`) and income entries (`/api/v1/income/entries`).
*   [ ] Build an interactive UI tab/page under Tax & Income management for user data entry and visualization.

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1 (Income Entry with TDS):** When a user logs a monthly salary of ₹1,50,000 with ₹15,000 TDS, the system saves the entry, updates FY gross income (+₹1.5L) and FY TDS credits (+₹15k).
*   [ ] **Scenario 2 (Multi-Source Filtering):** Users can filter income logs by Financial Year and Income Source category.
*   [ ] **Scenario 3 (Validation & Security):** Enforce strict tenant isolation (IDOR protection) ensuring users can only manage their own income entries.

---

### 4. Dependencies

*   Extends core User profile and authentication foundations (FR1).

---

### 5. Additional Context

*   **Requirement ID:** `(FR16.1 & FR16.2)`
*   This is part of Release v1.4.0 (Tax Readiness & Full Financial Picture).
