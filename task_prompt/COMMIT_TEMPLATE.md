# Commit Message Template

## 1. Commit Message

**Format:** `type(scope): subject`

*   **type:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
*   **scope:** A noun describing the section of the codebase (e.g., `portfolio`, `auth`, `backend`, `frontend`, `e2e`, `docs`, `ci`)
*   **subject:** A short, imperative-tense summary of the change.

```
<type>(<scope>): <subject>

[Optional: A more detailed explanation of the changes. Explain the 'what' and 'why', not the 'how'.]

[Optional: Closes FR-ID, Fixes BUG-ID]
```

---

## 2. Pre-Commit Checklist

*This checklist must be completed and verified before the commit is finalized.*

### Code & Testing
- [ ] All code changes are directly related to the feature or fix described.
- [ ] All new functions and classes have docstrings.
- [ ] All linters (`ruff`, `eslint`) pass successfully.
- [ ] All backend unit & integration tests pass.
- [ ] All frontend unit & integration tests pass.
- [ ] All E2E tests pass.
- [ ] New features are covered by new tests.

---

### Documentation Evaluation

*At a minimum, `workflow_history.md` and `bug_reports.md` must be updated for any feature or fix.*

- [ ] **`docs/workflow_history.md`**: A new, detailed entry has been added for this task. (Mandatory)
- [ ] **`docs/bug_reports.md`**: All temporary bug reports have been consolidated into the main log. (Mandatory)
- [ ] **`docs/features/`**: The relevant feature plan has been updated (e.g., status changed to "Done", technical design updated).
- [ ] **`docs/product_backlog.md`**: The status of the feature in the roadmap has been updated.
- [ ] **`docs/project_handoff_summary.md`**: The summary has been updated with the completed feature for context transfer.
- [ ] **`README.md`**: The main feature list has been updated.
- [ ] **`docs/troubleshooting.md`**: Evaluated. Updated if the changes resolve a common issue or could introduce a new one.
- [ ] **`docs/code_flow_guide.md`**: Evaluated. Updated if the changes introduce a new architectural pattern or data flow.
- [ ] **`docs/LEARNING_LOG.md`**: Evaluated. Updated if a significant new process improvement or technical lesson was learned.
- [ ] **`docs/DISCLAIMER.md`**: Evaluated. Updated if a new third-party data source or library with disclosure requirements was added.
- [ ] **`clean.sh`**: Evaluated. Updated if new temporary files or directories were introduced that need to be cleaned.
- [ ] **Other Documentation**: All other guides (e.g., `installation_guide.md`, `developer_guide.md`) have been evaluated and updated if impacted by the changes.