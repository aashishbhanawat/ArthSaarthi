# Antigravity Operational Playbook

## 1. Model Routing Strategy (Crucial for API Limits)
To prevent `429` (Rate Limit) and `503` (Capacity) server exhaustion, tasks MUST be routed to the appropriate LLM tier:
* **Claude Opus (Heavy Compute):** Use ONLY for architecture, system design, writing detailed Functional Requirements (FRs), complex logic, and deep-rooted bug triage.
* **Gemini 3.1 Pro (Standard Compute):** Use for standard feature implementation, non-complex logic, reviewing Jules's PRs, and complex bug fixes.
* **Gemini Flash (Lightweight Compute):** Use for basic tasks, running test suites, creating Git issues/PRs, writing commits, and simple bug fixes. *(If Flash struggles, temporarily upgrade to Gemini 3.1 Pro).*

## 2. Standard Development Workflow
### New Features
1. **Create Issue:** Use `gh` CLI to create a GitHub issue.
2. **Create Branch:** Create a new branch for the feature/bug. no fix or commit should be done directly on main branch.
3. **Write FR:** Write a detailed Functional Requirement referencing `docs/requirements.md`.
4. **Plan:** Propose backend/frontend/database changes. Ask for user confirmation.
5. **Code:** Generate code modularly (strictly one file at a time).
6. **Test:** Run relevant tests manually (see Docker Commands).
7. **Document & Commit:** Complete the documentation checklist and commit.

### Bug Fixes
1. **Create Issue:** File a Git issue with the bug details.
2. **Create Branch:** Create a new branch for the feature/bug. no fix or commit should be done directly on main branch.
3. **Triage:** Search `docs/bug_report_temp.md` for existing issues. 
4. **Fix & Test:** Analyze the full stack trace snippet provided by the user. Do not guess. Fix and verify.

## 3. Docker Command Cheat Sheet
*Execute these commands exactly as written from the project root.*

**Database Migrations (Safe Upgrade Pattern)**
```bash
docker compose -f docker-compose.yml -f docker-compose.test.yml down -v
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm test alembic upgrade head
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm test alembic downgrade base
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm test alembic upgrade head

```

**Linting & Security Checks**

```bash
# Python/Backend
docker compose run --rm backend sh -c "pip install -r requirements-dev.in && ruff check . --fix"
docker compose run --rm backend sh -c "pip install bandit safety && bandit -r app -x app/tests && safety check"

# JS/Frontend
docker compose run --rm frontend npx eslint .
docker compose run --rm frontend npm audit
docker compose run --rm frontend npm audit --audit-level=high

```

**Test Suites**

```bash
# Backend
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm test
docker compose -f docker-compose.yml -f docker-compose.test.sqlite.yml run --rm test-sqlite
docker compose -f docker-compose.yml -f docker-compose.test.desktop.yml run --build --rm test-desktop
# Specific Backend File Example:
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm --build test pytest app/tests/api/v1/test_ppf_holdings.py

# Frontend
docker compose run --rm frontend npm test

# E2E Tests (Full reset cycle)
docker compose -f docker-compose.yml -f docker-compose.e2e.yml down -v --remove-orphans
docker compose -f docker-compose.yml -f docker-compose.e2e.yml up --build --abort-on-container-exit
docker compose -f docker-compose.yml -f docker-compose.e2e.yml down -v --remove-orphans
# Specific E2E File Example:
docker compose -f docker-compose.yml -f docker-compose.e2e.yml run --build --rm test-e2e npx playwright test tests/ppf-modal-verification.spec.ts

```

## 4. Pre-Commit & Documentation Checklist

*Do not execute a commit until these documents are evaluated and updated.*

**Commit Format:** `<type>(<scope>): <subject>` (Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`)

**Mandatory Updates:**

* [ ] **`docs/workflow_history.md`**: Add a detailed entry for the completed task.
* [ ] **`docs/bug_reports.md`**: Consolidate any temporary bugs.
* [ ] **`docs/project_handoff_summary.md`**: **CRITICAL.** Update this with the completed feature so future AI chat sessions retain the project's current state.

