### Summary

This PR resolves the critical desktop build failure that was occurring on all platforms (Windows, macOS, Linux).

The root cause was a TypeScript type mismatch in `TransactionFormModal.tsx`. The `apiError` state expected a `string | null`, but the backend was returning an array of validation error objects (`{ msg: string }[]`), causing the build to fail with a `TS2345` error.

### Changes

-   Modified the `onError` callback within the `onSubmit` function in `frontend/src/components/Portfolio/TransactionFormModal.tsx`.
-   The logic now checks if the error response (`detail` or the result of `getErrorMessage`) is an array.
-   If it is an array, it maps over the items to extract the `msg` property and joins them into a single, comma-separated string.
-   This normalized string is then passed to `setApiError`, satisfying the component's state type and fixing the build.

This ensures the UI can gracefully display multiple validation errors from the backend without crashing the build process.
