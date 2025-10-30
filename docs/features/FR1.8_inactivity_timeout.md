# Feature Plan: Inactivity Timeout (FR1.8)

**Feature ID:** FR1.8
**Status:** 📝 Planned
**Title:** Automatic Logout on User Inactivity
**User Story:** As a security-conscious user, I want the application to automatically log me out after a period of inactivity, so that my financial data is protected if I leave my computer unattended.

---

## 1. Objective

This document outlines the implementation plan for a client-side inactivity timeout feature. The application will monitor user activity (mouse movement, clicks, key presses) and automatically log the user out after 30 minutes of inactivity. To provide a good user experience, a warning modal will be displayed shortly before the final logout.

---

## 2. High-Level User Flow

1.  User is actively using the application.
2.  User leaves the application idle.
3.  After **28 minutes** of inactivity, a modal appears: "You've been idle for a while. You will be logged out in 2 minutes." The modal has a "Stay Logged In" button.
4.  **Scenario A (User is present):** User clicks "Stay Logged In". The modal closes, and the 30-minute inactivity timer is reset.
5.  **Scenario B (User is absent):** User does not interact with the modal. After 2 more minutes (30 minutes total inactivity), the application automatically calls the `logout()` function, clears the session, and redirects to the login page.

---

## 3. UI/UX Design

The session timeout warning will be presented in a modal dialog that is consistent with the application's existing design system.

### 3.1. Mockup: Session Timeout Modal

```text
┌──────────────────────────────────────────────────┐
│ Session Timeout Warning                       [X]│
├──────────────────────────────────────────────────┤
│                                                  │
│  You have been idle for a while. For your        │
│  security, you will be logged out automatically. │
│                                                  │
│  Time remaining: 1:59                            │
│                                                  │
│                                                  │
│                    [ Stay Logged In ]            │
└──────────────────────────────────────────────────┘
```

### 3.2. Component Behavior
*   **Modal:** The modal will use the standard `.modal-overlay` and `.modal-content` classes.
*   **Countdown:** A timer will display the remaining time before automatic logout.
*   **Action Button:** A single, primary action button (`.btn .btn-primary`) labeled "Stay Logged In" will be present. Clicking this button will reset the idle timer and close the modal.

---

## 4. Technical Implementation Plan (Frontend-Centric)

This feature will be implemented entirely on the frontend, avoiding complex backend session management.

### 3.1. Dependency

*   Install the `react-idle-timer` library, a robust and well-tested solution for this use case.
    ```shell
    npm install react-idle-timer
    ```

### 3.2. New Files to Create

*   **Provider:** `frontend/src/context/IdleTimerProvider.tsx`
*   **Modal Component:** `frontend/src/components/modals/SessionTimeoutModal.tsx`

### 3.3. Implementation Steps

1.  **`IdleTimerProvider.tsx`:**
    *   Create a new context provider that will wrap the entire application.
    *   Use the `useIdleTimer` hook from the library.
    *   Configure the main `timeout` to 28 minutes and a `promptTimeout` of 2 minutes.
    *   The hook's `onPrompt` event will trigger the display of the `SessionTimeoutModal`.
    *   The hook's `onIdle` event (which fires after the `promptTimeout` expires) will call the `logout()` function from our existing `AuthContext`.

2.  **`SessionTimeoutModal.tsx`:**
    *   A simple modal component that displays the warning message and a countdown.
    *   It will have a single "Stay Logged In" button.

3.  **Integration:**
    *   Wrap the main `<App />` component in `main.tsx` with the new `<IdleTimerProvider>`.
    *   The `IdleTimerProvider` will manage the visibility of the `SessionTimeoutModal`.

### 3.4. Configuration

*   The timeout durations (e.g., 28 minutes, 2 minutes) should be configurable via environment variables (`VITE_IDLE_TIMEOUT_MS`, `VITE_IDLE_PROMPT_MS`) to allow for easy adjustment and, critically, for fast E2E testing.

---

## 5. Testing Plan

*   **Unit Tests:**
    *   Use Jest's fake timers (`jest.useFakeTimers()` and `jest.advanceTimersByTime()`) to test the `IdleTimerProvider`.
    *   Verify that `onPrompt` is called at the correct time (e.g., 28 minutes).
    *   Verify that `onIdle` is called at the correct time (e.g., 30 minutes).
*   **E2E Test:**
    *   Create a new test file `e2e/tests/inactivity-timeout.spec.ts`.
    *   Set the environment variables to very short durations (e.g., `VITE_IDLE_TIMEOUT_MS=3000`, `VITE_IDLE_PROMPT_MS=2000`).
    *   The test will log in, wait for 3 seconds, assert the warning modal is visible, wait another 2 seconds, and assert that the user has been redirected to the login page.

---
