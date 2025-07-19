feat(ui): Implement consistent design system and refactor all pages

This major update introduces a comprehensive, professional design system using Tailwind CSS and refactors the entire application to use it. This resolves numerous UI inconsistencies, layout bugs, and improves code maintainability and developer experience.

Key Changes:
*   Established a global stylesheet (`index.css`) with reusable component classes (`.card`, `.btn`, `.modal-*`, `.form-*`).
*   Replaced the previous application layout with a robust CSS Grid structure to prevent layout-breaking bugs.
*   Refactored all pages and components to use the new design system, including:
    *   Login & Admin Setup
    *   Dashboard
    *   User Management
    *   Portfolio List & Detail pages
*   Replaced all unstyled modals and browser `window.confirm` dialogs with consistently styled modal components.
*   Added the necessary Tailwind CSS configuration (`tailwind.config.js`, `postcss.config.js`) and npm dependencies to the frontend build process.

Bug Fixes:
*   This commit resolves all UI-related bugs documented from 20250719-02 to 20250719-16.
*   Fixes application crashes related to expired tokens by implementing a global Axios interceptor for 403 errors.
*   Fixes numerous other functional bugs discovered during the refactoring process, such as incorrect API paths, faulty React hooks, and component crashes.

This commit marks the completion of the initial UI stabilization and refactoring effort.