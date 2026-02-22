## 2024-05-22 - Toast Stacking and Accessibility
**Learning:** The existing `Toast` component was using `fixed` positioning, which caused multiple toasts to overlap perfectly instead of stacking.
**Action:** When creating notification lists, ensure the container handles positioning (e.g., `fixed top-right`) and individual items are `relative` or `static` block elements to allow natural stacking. Also, verify `role="alert"`/`status` and `aria-live` for screen readers.

## 2024-05-22 - Playwright Verification with HashRouter and Auth
**Learning:** The app uses `HashRouter` and has a strict auth check on load that fails if the backend is down.
**Action:** To verify frontend components in isolation without backend:
1. Navigate using hash routes (e.g., `/#/my-route`).
2. Clear `localStorage` to prevent auto-login attempts that trigger errors.
3. Use `text=` locators carefully when elements contain icons/buttons (like "×").

## 2024-05-22 - PR Superseded
**Learning:** PR #253 introduced comprehensive Toast improvements, superseding this PR.
**Action:** Close this PR. The stacking fix (removing `fixed`, adding `mb-3 w-80`) may be reused in a future PR on top of #253.
