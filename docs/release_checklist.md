# Final Release Checklist

This checklist should be completed for every official release of the ArthSaarthi application to ensure quality, consistency, and stability.

**Release Version:** `vX.Y.Z`
**Release Date:** `YYYY-MM-DD`
**Release Manager:**

---

## Phase 1: Pre-Release Finalization

*This phase ensures the codebase and documentation are stable and verified before tagging.*

- [ ] **Code Freeze:** Confirm that all feature development for this release has been merged into the `main` branch. Only release-critical bug fixes are permitted.
- [ ] **Dependency Check:** Confirm all necessary dependencies are listed in `backend/requirements.txt` and `frontend/package.json`.

### Automated Testing

- [ ] **Backend Unit & Integration Tests:** All tests pass.
  ```bash
  docker-compose run --rm test
  ```
- [ ] **Frontend Unit & Integration Tests:** All tests pass.
  ```bash
  docker-compose run --rm frontend npm test
  ```
- [ ] **End-to-End (E2E) Tests:** The full E2E suite passes against a production-like environment.
  ```bash
  docker-compose -f docker-compose.yml -f docker-compose.e2e.yml up --build --abort-on-container-exit
  ```

### Manual Quality Assurance

- [ ] **Manual Smoke Test:** Perform a final manual walkthrough of all critical user flows in a clean, production-like environment.
  - [ ] Initial Admin Setup & Login
  - [ ] Admin: User Management (Create, Edit, Delete User)
  - [ ] User: Portfolio Management (Create, View, Delete Portfolio)
  - [ ] User: Transaction Management (Add, Edit, Delete Transaction)
  - [ ] User: Dashboard & Analytics view (Summary, History, Allocation)
  - [ ] User: Data Import (Upload, Preview, Commit)

### Documentation

- [ ] **Sync Master Task:** Ensure `task_prompt/pms_master_task.md` accurately reflects the final state of the project's processes.
- [ ] **Review Core Docs:** Review `README.md`, `RELEASE_PLAN.md`, and `handoff_document.md` for accuracy and clarity.
- [ ] **Finalize Logs:** Ensure `docs/workflow_history.md` and `docs/bug_reports.md` are up-to-date with all activities from the release cycle.

---

## Phase 2: Release Execution

*This phase involves tagging the release, which triggers the automated build and deployment pipeline.*

- [ ] **Final Pull:** Ensure your local `main` branch is up-to-date with `origin/main`.
- [ ] **Create Git Tag:** Create an annotated tag following Semantic Versioning.
  ```bash
  git tag -a vX.Y.Z -m "Release version X.Y.Z"
  ```
- [ ] **Push Git Tag:** Push the tag to the remote repository to trigger the release workflow.
  ```bash
  git push origin vX.Y.Z
  ```

---

## Phase 3: Post-Release Verification

*This phase verifies that the automated pipeline executed successfully and all artifacts were published correctly.*

- [ ] **GitHub Actions Workflow:**
  - [ ] Verify the `Create Full Release` workflow was triggered by the new tag.
  - [ ] Confirm all jobs (`build-and-push-docker`, `create-release`, `build-installers`) completed successfully.
- [ ] **GitHub Release Page:**
  - [ ] Check the project's GitHub Releases page for the new `vX.Y.Z` release.
  - [ ] Confirm all native installers (Windows, macOS, Linux) are attached as assets.
  - [ ] Confirm the source code `.zip` and documentation files are attached.
- [ ] **Container Registry:**
  - [ ] Confirm that the `backend` and `frontend` Docker images have been pushed to the container registry with the correct `vX.Y.Z` tag.
- [ ] **Communication:** Announce the new release to all relevant stakeholders.