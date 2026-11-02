from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.scheduled_job_log import ScheduledJobLog


class CRUDScheduledJobLog:
    def create(
        self,
        db: Session,
        *,
        job_id: str,
        job_name: str,
        status: str,
        started_at: datetime,
        finished_at: Optional[datetime] = None,
        execution_time_seconds: Optional[float] = None,
        error_message: Optional[str] = None,
    ) -> ScheduledJobLog:
        db_obj = ScheduledJobLog(
            job_id=job_id,
            job_name=job_name,
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            execution_time_seconds=execution_time_seconds,
            error_message=error_message,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50,
        job_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Tuple[int, List[ScheduledJobLog]]:
        query = db.query(ScheduledJobLog)
        if job_id:
            query = query.filter(ScheduledJobLog.job_id == job_id)
        if status:
            query = query.filter(ScheduledJobLog.status == status)

        total = query.count()
        items = (
            query.order_by(desc(ScheduledJobLog.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
        return total, items

    def count_failures_since(
        self,
        db: Session,
        *,
        since: datetime,
    ) -> int:
        return (
            db.query(func.count(ScheduledJobLog.id))
            .filter(
                ScheduledJobLog.status == "FAILED",
                ScheduledJobLog.started_at >= since,
            )
            .scalar()
            or 0
        )

    def prune_older_than(
        self,
        db: Session,
        *,
        days: int = 30,
    ) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        deleted = (
            db.query(ScheduledJobLog)
            .filter(ScheduledJobLog.created_at < cutoff)
            .delete(synchronize_session=False)
        )
        db.commit()
        return deleted


scheduled_job_log = CRUDScheduledJobLog()
