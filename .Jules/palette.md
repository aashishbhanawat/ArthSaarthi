## 2024-05-18 - Transaction Details Modal Close Button\n**Learning:** Modals can sometimes be missing explicit close buttons or lack ARIA attributes linking the title to the dialog role.\n**Action:** Update modals to include a standard `modal-header` with an `h2` and an explicitly labeled close button using `XMarkIcon`.

## 2024-10-29 - Modal Initial Focus
**Learning:** Newly opened React modals often lack an explicitly focused element, requiring screen reader or keyboard users to tab manually into the form content.
**Action:** Always apply the `autoFocus` property to the primary `<input>` field within newly created or existing React modals to immediately direct keyboard focus following WAI-ARIA practices.
