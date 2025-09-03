---
name: '🚀 Feature Request'
about: 'Implement due date reminders for FDs, NPS, etc.'
title: 'feat: Implement due date reminders for FDs, NPS, etc.'
labels: 'enhancement, feature, epic:notifications'
assignees: ''
---

### 1. User Story

**As a** user with long-term investments like FDs or NPS,
**I want to** receive reminders for upcoming maturity or contribution due dates,
**so that** I don't miss important deadlines and can take timely action.

---

### 2. Functional Requirements

*   [ ] Implement a background job that scans daily for assets with upcoming due dates (e.g., FD maturity).
*   [ ] The system should trigger a notification a configurable number of days before the due date (e.g., 7 days prior).
*   [ ] The notification message must clearly state the asset, the due date, and the event (e.g., "Your HDFC Bank FD matures on YYYY-MM-DD").
*   [ ] The system must ensure that a reminder for a specific event is sent only once to avoid spamming the user.

---

### 3. Acceptance Criteria

*   [ ] **Scenario 1:** Given I have a Fixed Deposit that matures in exactly 7 days, when the daily background job runs, then I should receive a notification via my configured channel.
*   [ ] **Scenario 2:** Given the reminder in Scenario 1 was sent today, when the background job runs tomorrow (6 days before maturity), then I should not receive another notification for the same event.

---

### 4. Dependencies

*   This feature depends on a notification delivery channel being implemented (`FR9.3`, Issue #30).
*   It depends on the implementation of assets that have due dates, such as Fixed Deposits (`FR4.3.1`).

---

### 5. Additional Context

*   **Requirement ID:** `(FR9.2)`
*   A mechanism to track sent reminders (e.g., a `reminder_sent` flag in the database) will be necessary to meet the acceptance criteria.

