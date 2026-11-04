from typing import Any, Callable, Coroutine, Dict, NamedTuple

from apscheduler.triggers.base import BaseTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.tasks.snapshot_task import run_daily_snapshot_job


class TaskDefinition(NamedTuple):
    job_id: str
    name: str
    description: str
    func: Callable[[], Coroutine[Any, Any, Any]]
    trigger: BaseTrigger


def get_task_registry() -> Dict[str, TaskDefinition]:
    """
    Returns the dictionary of all registered background jobs.
    In Desktop/Android mode, snapshots run every 6 hours to accommodate
    irregular app open cycles; in server/docker mode, snapshots run daily at 00:05.
    """
    if settings.DEPLOYMENT_MODE in ("desktop", "android"):
        snapshot_trigger = IntervalTrigger(hours=6)
    else:
        snapshot_trigger = CronTrigger(hour=0, minute=5)

    tasks: Dict[str, TaskDefinition] = {
        "daily_portfolio_snapshot": TaskDefinition(
            job_id="daily_portfolio_snapshot",
            name="Daily Portfolio Valuation Snapshot",
            description=(
                "Calculates and persists daily consolidated portfolio valuation "
                "and asset allocation snapshots."
            ),
            func=run_daily_snapshot_job,
            trigger=snapshot_trigger,
        ),
    }

    return tasks
