# Palette's Journal

## 2025-05-27 - Password Visibility Toggle
**Learning:** Implemented a password visibility toggle using `@heroicons/react`. The pattern of `relative` container + `absolute` button + `pr-10` on input works seamlessly with the existing Tailwind form styles.
**Action:** Reuse this pattern for other inputs requiring icons (e.g., search bars with clear buttons). Ensure distinct `aria-labels` are used to prevent `getByLabelText` collisions in tests.
