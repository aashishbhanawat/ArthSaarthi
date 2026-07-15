## 2024-03-24 - Empty state in Watchlist Selector
**Learning:** For inline or sidebar menu components (like `ul` element menus), providing a simple `<li>` empty state message provides much better UX than silently rendering an empty container, but shouldn't use the full-page empty state Heroicon layout.
**Action:** When working with inline lists, add a simple text `<li>` element when the underlying data is empty.
