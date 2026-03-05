## 2025-01-30 - Modal and Icon Button Accessibility
**Learning:** Found multiple instances of icon-only buttons (Edit, Delete, Close) lacking `aria-label` or using inaccessible text replacements like `&times;`. Modals specifically rely on `&times;` which is confusing for screen readers.
**Action:** When working on modals or tables with action buttons, always check for `aria-label`. Replace `&times;` with `XMarkIcon` for better visual and accessibility consistency.
