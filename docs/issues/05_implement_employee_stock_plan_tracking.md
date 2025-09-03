---
name: '🚀 Feature Request'
about: 'Implement tracking for Employee Stock Plans (RSUs/ESPPs)'
title: 'feat: Implement tracking for Employee Stock Plans (RSUs/ESPPs)'
labels: 'enhancement, feature, epic:advanced-assets'
assignees: ''
---

### 1. User Story

**As an** employee receiving stock-based compensation,
**I want to** track my Restricted Stock Units (RSUs) and Employee Stock Purchase Plans (ESPPs), including both Indian and US variants,
**so that** I can monitor the value of my equity compensation alongside my other investments.

---

### 2. Functional Requirements

*   [ ] Users must be able to add a new Employee Stock Plan asset, capturing details like company name, grant ID, grant date, and vesting schedule.
*   [ ] The system must support different currencies, especially INR and USD.
*   [ ] Users must be able to log vesting events as a specific transaction type.
*   [ ] Logging a vesting event should create a corresponding "buy" transaction for the vested shares at the market price on the vesting date.
*   [ ] The system should be able to display both vested (as part of holdings) and unvested shares.

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1:** Given I am on my portfolio page, when I use the "Add New Asset" flow and select "Employee Stock Plan", then I should see a form to enter my RSU/ESPP grant details.
*   [ ] **Scenario 2:** Given I have an RSU grant, when I log a vesting event for 10 shares, then my holdings for that company's stock should increase by 10, and a corresponding transaction should be created.

---

### 4. Dependencies

*   This feature depends on the foundational "Advanced Asset Support" framework.

---

### 5. Additional Context

*   **Requirement ID:** `(FR4.3.5)`
*   This feature is complex due to vesting schedules and tax implications. The MVP should focus on tracking the grants and the creation of stock holdings upon vesting.

