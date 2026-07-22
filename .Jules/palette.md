## 2024-03-24 - Empty state in Watchlist Selector
**Learning:** For inline or sidebar menu components (like `ul` element menus), providing a simple `<li>` empty state message provides much better UX than silently rendering an empty container, but shouldn't use the full-page empty state Heroicon layout.
**Action:** When working with inline lists, add a simple text `<li>` element when the underlying data is empty.
## $(date +%Y-%m-%d) - Improve empty states for transaction lists
**Learning:** Simple text empty states feel unpolished and don't provide a good visual cue for users when there is no data.
**Action:** Replaced plain text empty states in `TransactionHistoryTable` and `TransactionList` with a standard empty state component using a Heroicon (`ListBulletIcon`), a heading, and helpful guidance text, matching the pattern established in the `WatchlistTable` component.
