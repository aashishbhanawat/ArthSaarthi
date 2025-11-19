# Feature Plan: Inactivity Timeout (FR1.8)

**Feature ID:** FR1.8
**Status:** ✅ Implemented
**Title:** Automatic Logout on User Inactivity
**User Story:** As a security-conscious user, I want the application to automatically log me out after a period of inactivity, so that my financial data is protected if I leave my computer unattended.

---

## 1. Objective

This document outlines the implementation plan for a client-side inactivity timeout feature. The application will monitor user activity (mouse movement, clicks, key presses) and automatically log the user out after a configurable period of inactivity. To provide a good user experience, a warning modal will be displayed shortly before the final logout.

---

## 2. High-Level User Flow

1.  User is actively using the application.
2.  User leaves the application idle.
3.  After a configured duration of inactivity (defaulting to 30 minutes), a modal appears: "You've been idle for a while. You will be logged out in 2 minutes." The modal has a "Stay Logged In" button.
4.  **Scenario A (User is present):** User clicks "Stay Logged In". The modal closes, and the inactivity timer is reset.
5.  **Scenario B (User is absent):** User does not interact with the modal. After 2 more minutes, the application automatically calls the `logout()` function, clears the session, and redirects to the login page.

---

## 3. UI/UX Design

The session timeout warning will be presented in a modal dialog that is consistent with the application's existing design system.

### 3.1. Mockup: Session Timeout Modal

```text
┌──────────────────────────────────────────────────┐
│ Session Timeout                                  │
├──────────────────────────────────────────────────┤
│                                                  │
│  You will be logged out in 120 seconds due to    │
│  inactivity.                                     │
│                                                  │
│                                                  │
│      [ Stay Logged In ] [ Logout ]               │
└──────────────────────────────────────────────────┘
```

### 3.2. Component Behavior
*   **Modal:** The modal will use the standard `.modal-overlay` and `.modal-content` classes.
*   **Countdown:** A timer will display the remaining time before automatic logout.
*   **Action Button:** A "Stay Logged In" button will be present. Clicking this button will reset the idle timer and close the modal. A "Logout" button is also provided for immediate logout.

---

## 4. Technical Implementation Plan (Frontend-Centric)

This feature was implemented entirely on the frontend, avoiding complex backend session management.

### 3.1. New Files Created

*   **Hook:** `frontend/src/hooks/useIdleTimer.ts`
*   **Modal Component:** `frontend/src/components/modals/SessionTimeoutModal.tsx`

### 3.2. Implementation Steps

1.  **`useIdleTimer.ts`:**
    *   A custom hook was created to manage the inactivity timer.
    *   It listens for user activity events such as mouse movements, key presses, and clicks to reset the timer.
    *   When the timer expires, it triggers a callback to show the warning modal.

2.  **`SessionTimeoutModal.tsx`:**
    *   A modal component that displays the warning message and a countdown.
    *   It has a "Stay Logged In" button to reset the timer and a "Logout" button to log out immediately.

3.  **Integration:**
    *   The `useIdleTimer` hook and `SessionTimeoutModal` were integrated into the `AuthProvider` in `frontend/src/context/AuthContext.tsx`.

### 3.3. Configuration

*   The inactivity timeout duration is configurable via the `VITE_INACTIVITY_TIMEOUT_MINUTES` environment variable.
*   The inactivity timeout and modal countdown are also configurable for E2E tests via `sessionStorage` overrides (`e2e_inactivity_timeout` and `e2e_modal_countdown_seconds`).

---

## 5. Testing Plan

*   **Unit Tests:**
    *   `frontend/src/__tests__/hooks/useIdleTimer.test.ts`: Tests for the `useIdleTimer` hook using Jest's fake timers.
    *   `frontend/src/__tests__/components/modals/SessionTimeoutModal.test.tsx`: Tests for the `SessionTimeoutModal` component.
*   **E2E Test:**
    *   `e2e/tests/inactivity-timeout.spec.ts`: An E2E test that verifies the complete inactivity timeout flow, using `sessionStorage` overrides to test the feature with short timeouts.

---
