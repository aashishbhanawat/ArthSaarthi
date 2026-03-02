## 2024-05-24 - Accessibility of Icon Buttons in Modals
**Learning:** Icon-only action buttons (Edit, Delete) in detailed transaction view modals (`BondDetailModal`, `HoldingDetailModal`, `PpfHoldingDetailModal`) were missing descriptive text for screen readers, unlike similar patterns found in `TransactionList`.
**Action:** Consistently add `aria-label`s to all icon-only action buttons to ensure they announce their specific intent (e.g., "Edit Transaction", "Delete Transaction") across all components.
