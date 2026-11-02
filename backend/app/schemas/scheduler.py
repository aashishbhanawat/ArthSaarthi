import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class JobInfo(BaseModel):
    id: str
    name: str
    trigger: str
    next_run_time: Optional[datetime] = None
    status: str  # ACTIVE, PAUSED, RUNNING
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TriggerJobResponse(BaseModel):
    message: str
    job_id: str
    status: str


class PauseResumeResponse(BaseModel):
    message: str
    job_id: str
    status: str


class ScheduledJobLogResponse(BaseModel):
    id: uuid.UUID
    job_id: str
    job_name: str
    status: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    execution_time_seconds: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScheduledJobLogsPaginated(BaseModel):
    total: int
    items: List[ScheduledJobLogResponse]


class SchedulerSummary(BaseModel):
    is_running: bool
    total_jobs: int
    active_jobs: int
    paused_jobs: int
    failed_last_24h: int
    jobs: List[JobInfo]
