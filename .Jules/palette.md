## 2024-03-24 - Empty state in Watchlist Selector
**Learning:** For inline or sidebar menu components (like `ul` element menus), providing a simple `<li>` empty state message provides much better UX than silently rendering an empty container, but shouldn't use the full-page empty state Heroicon layout.
**Action:** When working with inline lists, add a simple text `<li>` element when the underlying data is empty.
## $(date +%Y-%m-%d) - Improve empty states for transaction lists
**Learning:** Simple text empty states feel unpolished and don't provide a good visual cue for users when there is no data.
**Action:** Replaced plain text empty states in `TransactionHistoryTable` and `TransactionList` with a standard empty state component using a Heroicon (`ListBulletIcon`), a heading, and helpful guidance text, matching the pattern established in the `WatchlistTable` component.

## $(date +%Y-%m-%d) - Adding aria-hidden to decorative icons
**Learning:** Decorative SVG icons (like Heroicons used inside buttons that already have `aria-label`s or adjacent text) were being redundantly parsed or announced by screen readers because they lacked `aria-hidden="true"`.
**Action:** When adding or updating icon-only buttons or icons next to text, explicitly add `aria-hidden="true"` to the SVG component if the parent element already provides an accessible name (e.g., via `aria-label`).
## 2025-02-20 - Contextual ARIA labels for icon-only action buttons in lists/tables
**Learning:** Icon-only action buttons (like Edit/Delete) inside data tables or lists often rely only on generic `title` attributes (e.g., `title="Edit"`). This is insufficient for accessibility, as screen reader users tabbing through the page will hear "Edit button", "Edit button" repeatedly without knowing *which* item they are acting upon.
**Action:** When adding or auditing icon-only buttons in mapped arrays (like table rows), always explicitly add an `aria-label` that interpolates row-specific context (e.g., `aria-label={\`Edit alias for ${alias.alias_symbol}\`}`).
## 2026-08-24 - Replace raw HTML entities with SVG icons
**Learning:** Raw text characters like '×' for dismiss buttons are often misread by screen readers (e.g., as 'times').
**Action:** Always use semantic SVG components (like Heroicons' XMarkIcon) along with appropriate aria-labels and aria-hidden attributes for UI icon buttons.
## 2024-11-20 - Ensure standard icons for modal close buttons
**Learning:** Some custom modals used a plain text "✕" for their close button which lacks screen reader context. Standard Heroicons (`XMarkIcon`) with `aria-label="Close"` are generally used elsewhere in the codebase.
**Action:** Always replace plain text close symbols with semantic `XMarkIcon` from `@heroicons` and add an `aria-label="Close"` to improve accessibility consistency.
