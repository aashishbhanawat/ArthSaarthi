# Guide for AI Assistants

This guide provides instructions for setting up a local development and testing environment that is self-contained and does not require Docker.

## Unified Local Test Runner

The `run_local_tests.sh` script is the single, unified way to run all types of tests and checks for this project. It is designed to be run in a non-Dockerized environment and can be configured to target different databases and test suites.

### Usage

```bash
./run_local_tests.sh [TEST_SUITE] [--db DB_TYPE]
```

### Test Suites

You can specify which suite of tests to run:

- `all`: (Default) Runs linting, all unit tests, and all e2e tests.
- `lint`: Runs backend (ruff) and frontend (eslint) linters.
- `backend`: Runs backend (pytest) unit and integration tests.
- `frontend`: Runs frontend (jest) unit tests.
- `e2e`: Runs end-to-end (playwright) tests.
  - `migrations`: Tests the full Alembic migration cycle (upgrade/downgrade).

### Database Backends

The script can run tests against two different database backends, specified with the `--db` flag:

- `--db sqlite`: (Default) Uses a temporary file-based SQLite database. This is the recommended option for most sandboxed development and testing, as it has no external dependencies.
- `--db postgres`: Uses a local PostgreSQL server and a local Redis server.

### Prerequisites for PostgreSQL

If you intend to run tests with the PostgreSQL backend (`--db postgres`), you must ensure the following services are installed and running **before** executing the script:
- PostgreSQL server
- Redis server

The script will handle the creation and teardown of the test database, but the services themselves must be active.

### Examples

**Run all checks with SQLite:**
```bash
./run_local_tests.sh all --db sqlite
```
*(Note: `all` and `--db sqlite` are defaults, so `./run_local_tests.sh` is equivalent)*

**Run only E2E tests with PostgreSQL:**
```bash
./run_local_tests.sh e2e --db postgres
```

**Run only backend unit tests (defaults to SQLite):**
```bash
./run_local_tests.sh backend
```

This script is the definitive way to run tests in a non-Dockerized environment. Please refer to the script's help message (`./run_local_tests.sh --help`) for more details.
