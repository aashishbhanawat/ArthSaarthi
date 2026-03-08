# FR_startup_resilience - Requirement

## Context
The application performs a heavy asset seeding process on the first startup. This process involves downloading multiple files from external sources (NSE, BSE, NSDL) and processing ~40,000 records.

## Requirement
- The Docker deployment must allow sufficient time for the backend to complete its initialization (migrations, seeding) before marking it as unhealthy.
- The `start_period` for the backend health check must be long enough to accommodate slow network connections or large data processing.

## References
- [requirements.md](file:///media/data/AppData/CodeServer/pms4/ArthSaarthi/docs/requirements.md) (NFR6: Deployment)
- GitHub Issue: #330
