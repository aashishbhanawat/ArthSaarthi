# Functional Requirement Specification: Background Job Scheduler

**Feature ID:** FR-Scheduler-APScheduler  
**GitHub Issue:** [#561](https.github.com/aashishbhanawat/ArthSaarthi/issues/561)  
**Title:** Architectural Background Job Scheduler (APScheduler Integration)  
**Target Release:** v1.5.0  

---

## 1. Sub-component Breakdown & Micro-Phases

### Phase 4.1: APScheduler Integration into FastAPI Lifecycle
* Initialize `AsyncIOScheduler` in FastAPI app lifespan startup event (`backend/app/core/scheduler.py`).
* Configure job stores (Memory / SQLite `SQLAlchemyJobStore`) to support single-instance and multi-worker execution.

### Phase 4.2: Job Management & Monitoring API
* Create REST API endpoints under `/api/v1/admin/scheduler` to inspect active background jobs, next run times, execution status, and manual trigger triggers.
* Implement job execution logging and error capture stored in `scheduled_job_logs` table.

### Phase 4.3: Task Worker Registry
* Create task module `backend/app/tasks/` holding reusable async job worker routines (e.g. `fetch_news_task`, `process_corporate_actions_task`, `refresh_prices_task`).

---

## 2. Technical Specification (Backend & Frontend)

### 2.1 Backend Implementation Details
* **Scheduler Core (`backend/app/core/scheduler.py`):**
  * `AsyncIOScheduler` instance started on server startup and shut down gracefully on server teardown.
  * Task lock management preventing overlapping job execution when previous run is still active.
* **Job Log Capture:**
  * Custom event listener capturing `EVENT_JOB_EXECUTED` and `EVENT_JOB_ERROR` to write audit entries to database.

### 2.2 Frontend Implementation Details
* **Admin Scheduler Dashboard (`src/components/admin/SchedulerDashboard.tsx`):**
  * View list of scheduled jobs (Job ID, Name, Trigger Type, Cron/Interval, Last Run Status, Next Run Time).
  * "Run Now" action button to trigger an asynchronous job immediately.

---

## 3. Comprehensive Test Plan & Edge Cases

### 3.1 Edge Cases & Failure Scenarios
* **Job Exception / Crash:** Unhandled exception inside a scheduled job must be caught, logged to DB, and notified via log alert without crashing the main FastAPI application or stopping the scheduler.
* **Database Lock (SQLite):** Prevent database lock contention during concurrent DB writes between web requests and background job execution.
* **Server Restart:** Scheduled jobs resume state seamlessly on server restart using persistent job store.

### 3.2 Manual Testing Checklist
* [ ] Start backend server, verify scheduler startup log message.
* [ ] Navigate to `/admin/scheduler` in UI.
* [ ] Click "Run Now" on Market News Fetcher task and verify execution log created in DB.
* [ ] Verify next execution timestamp updates correctly.

---

## 4. Automated Testing Strategy

### 4.1 Backend Pytest (`backend/app/tests/core/test_scheduler.py`)
* Test job registration, execution, and error listener callback.
* Test `SQLAlchemyJobStore` initialization with SQLite in-memory and file database.

### 4.2 Frontend Vitest (`src/components/admin/__tests__/SchedulerDashboard.test.tsx`)
* Test job list rendering and "Run Now" API trigger dispatch.

### 4.3 E2E Playwright (`tests/scheduler.spec.ts`)
* Test navigating to Admin -> Scheduler UI and triggering manual job run.

---

## 5. UX & UI Specifications
* Admin Settings -> Background Tasks tab.
* Job status pills: `IDLE`, `RUNNING`, `SUCCESS`, `FAILED`.
* Detailed drawer/modal showing execution logs and stack trace for failed job runs.

---

## 6. Database Schema & Data Security

### 6.1 Database Schema
New table: `scheduled_job_logs`

```sql
CREATE TABLE scheduled_job_logs (
    id VARCHAR PRIMARY KEY,
    job_id VARCHAR(100) NOT NULL,
    job_name VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL, -- SUCCESS, FAILED, RUNNING
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    finished_at TIMESTAMP WITH TIME ZONE NULL,
    execution_time_seconds FLOAT NULL,
    error_message TEXT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_job_logs_id_status ON scheduled_job_logs(job_id, status);
```

### 6.2 Encryption Requirements
* No encrypted columns required for job log metrics.

---

## 7. Required Documentation Updates

* **README.md:** Add section describing background job processing.
* **docs/code_flow_guide.md:** Document APScheduler architecture and adding new tasks to `app/tasks/`.
* **docs/workflow_history.md:** Log implementation details.
* **docs/debugging_guide.md:** Add troubleshooting guide for background job execution failures.
* **docs/project_handoff_summary.md:** Update background processing section.
* **docs/requirements.md:** Update Background Job Scheduler section.

---

## 8. External Data Sources & API Specifications
* Internal application trigger system; triggers tasks fetching external market news, price updates, and corporate actions.

---

## 9. File & API Endpoint Inventory

### Files to Create / Modify
* **Create:** `backend/app/core/scheduler.py`
* **Create:** `backend/app/tasks/__init__.py`
* **Create:** `backend/app/models/scheduled_job_log.py`
* **Create:** `backend/app/api/v1/endpoints/scheduler.py`
* **Create:** `frontend/src/components/admin/SchedulerDashboard.tsx`
* **Modify:** `backend/app/main.py` (lifespan hook)

### API Routes
* `GET /api/v1/scheduler/jobs` - List all scheduled jobs and status
* `POST /api/v1/scheduler/jobs/{job_id}/run` - Trigger job manually
* `GET /api/v1/scheduler/logs` - Fetch execution logs

---

## 10. Mobile-Friendly UI & Responsive Design
* Cards view on mobile screens representing each scheduled task with status indicator and execution button.

---

## 11. Android Compatibility & Python Library Constraints
* **APScheduler Library:** `apscheduler` version 3.x is 100% pure-Python with zero C-extension native binaries. It runs seamlessly inside Chaquopy / Kivy / Android embedded Python environments.
