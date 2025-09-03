# Feature Plan: Privacy Mode (FR3.4)

**Feature ID:** FR3.4
**Title:** Privacy Mode
**User Story:** As a user, I want to be able to quickly hide all monetary values in the application with a single click, so that I can show my portfolio structure to others without revealing sensitive financial details.
**Status:** ✅ Implemented

---

## 1. Objective

To implement a global "Privacy Mode" toggle that obscures all monetary amounts throughout the frontend application. This is a client-side feature that enhances user privacy.

---

## 2. UI/UX Design

*   **Toggle:** An "eye" icon will be placed in the top navigation bar, next to the search bar.
*   **State:** The icon will have two states: a regular eye (visible) and a slashed eye (hidden).
*   **Interaction:** Clicking the icon will toggle Privacy Mode on or off. The state will be persisted across sessions using `localStorage`.
*   **Obscured Text:** When active, all monetary values (e.g., `₹1,23,456.78`) will be replaced with a generic placeholder (e.g., `₹**,***.**`). Non-monetary numbers (like quantity) will remain visible.

---

## 3. Frontend Implementation Plan

### 3.1. Global State Management

1.  **Create `PrivacyContext.tsx`:** A new React Context will be created to manage the global state of Privacy Mode.
    *   It will provide a boolean `isPrivacyMode` and a function `togglePrivacyMode`.
    *   It will use `localStorage` to persist the user's preference.
2.  **Wrap Application:** The `App.tsx` component will be wrapped with the new `PrivacyProvider`.

### 3.2. UI Components

1.  **Update `TopBar.tsx` (or equivalent):**
    *   Add the eye icon button.
    *   Use the `usePrivacy` hook to get the current state and the toggle function.
    *   Conditionally render the correct icon based on the `isPrivacyMode` state.

### 3.3. Data Formatting

1.  **Update `formatting.ts`:**
    *   The `formatCurrency` utility function will be refactored.
    *   It will now use the `usePrivacy` hook to check the `isPrivacyMode` state.
    *   If privacy mode is active, it will return the placeholder string (`₹**,***.**`). Otherwise, it will return the formatted currency value as it does now.

*   **Benefit:** By centralizing the logic in the `formatCurrency` utility, all components that use this function will automatically become privacy-aware without needing individual changes.

---

## 4. Testing Plan

### 4.1. Unit/Component Tests (Jest & RTL)

*   **`PrivacyContext.tsx`:**
    *   Test that the initial state is correctly read from `localStorage`.
    *   Test that `togglePrivacyMode` correctly updates the state and `localStorage`.
*   **`formatting.ts` (`formatCurrency` function):**
    *   Mock the `usePrivacy` hook.
    *   Assert that it returns a real currency string when privacy mode is off.
    *   Assert that it returns the obscured placeholder string (`₹**,***.**`) when privacy mode is on.
*   **Toggle Button Component:**
    *   Assert that the correct icon (`EyeIcon` vs. `EyeSlashIcon`) is rendered based on the context's state.
    *   Assert that clicking the button calls the `togglePrivacyMode` function.

### 4.2. End-to-End Test (Playwright)

A new E2E test will be created to validate the full user flow.
1.  Log in and navigate to the Dashboard.
2.  Verify that monetary values are initially visible.
3.  Click the privacy toggle button.
4.  Verify that all monetary values are now obscured with the placeholder, but non-monetary values (like quantity) are still visible.
5.  Reload the page and verify that the obscured state persists.
6.  Click the toggle again and verify that the values become visible.
