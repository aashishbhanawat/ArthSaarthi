export interface JobInfo {
  id: string;
  name: string;
  trigger: string;
  next_run_time: string | null;
  status: 'ACTIVE' | 'PAUSED' | 'RUNNING' | 'IDLE';
  description?: string;
}

export interface TriggerJobResponse {
  message: string;
  job_id: string;
  status: string;
}

export interface PauseResumeResponse {
  message: string;
  job_id: string;
  status: string;
}

export interface ScheduledJobLogItem {
  id: string;
  job_id: string;
  job_name: string;
  status: 'SUCCESS' | 'FAILED' | 'MISSED';
  started_at: string;
  finished_at: string | null;
  execution_time_seconds: number | null;
  error_message: string | null;
  created_at: string;
}

export interface ScheduledJobLogsPaginated {
  total: number;
  items: ScheduledJobLogItem[];
}

export interface SchedulerSummary {
  is_running: boolean;
  total_jobs: number;
  active_jobs: number;
  paused_jobs: number;
  failed_last_24h: number;
  jobs: JobInfo[];
}
