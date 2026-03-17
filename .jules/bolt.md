# Performance Architecture Journal

## High-Level Findings
The application currently exhibits several systemic performance patterns:
- **Database Fatigue**: N+1 query patterns are prevalent in cross-aggregate reporting functions (e.g., goals referencing multiple portfolios) and daily historical simulation logic. Batch insertion (`db.add_all()`) is frequently bypassed in favor of sequential `db.add()` calls inside loops.
- **Frontend List Inefficiency**: Large data tables (like Holdings and Transactions) render all rows simultaneously, lacking virtualization (e.g., `react-window`), which can cause severe Total Blocking Time (TBT) regression on low-end devices.
- **Redundant Work**: History generation scripts recalculate complex state (like PPF interest) on every day of the simulation rather than caching intermediate states.

## Summary of Identified Issues
| Impact | Type | Location | Description |
|---|---|---|---|
| High | Database Fatigue | `backend/app/crud/crud_goal.py` | N+1 Query in `get_goal_with_analytics` for portfolio holdings. |
| High | Algorithmic Waste | `backend/app/crud/crud_dashboard.py` | Redundant daily recalculation of PPF interest in `_get_portfolio_history`. |
| Medium | Database Fatigue | `backend/app/crud/crud_holding.py` | Sequential `db.add()` in loops during asset enrichment instead of batch `db.add_all()`. |
| Medium | List Inefficiency | `frontend/src/components/Portfolio/HoldingsTable.tsx` | Missing virtualization for potentially long holdings lists. |
