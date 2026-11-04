import apiClient from './api';
import {
  JobInfo,
  PauseResumeResponse,
  ScheduledJobLogsPaginated,
  SchedulerSummary,
  TriggerJobResponse,
} from '../types/scheduler';

export const getSchedulerSummary = async (): Promise<SchedulerSummary> => {
  const response = await apiClient.get<SchedulerSummary>('/api/v1/admin/scheduler/summary');
  return response.data;
};

export const getScheduledJobs = async (): Promise<JobInfo[]> => {
  const response = await apiClient.get<JobInfo[]>('/api/v1/admin/scheduler/jobs');
  return response.data;
};

export const triggerJobNow = async (jobId: string): Promise<TriggerJobResponse> => {
  const response = await apiClient.post<TriggerJobResponse>(
    `/api/v1/admin/scheduler/jobs/${encodeURIComponent(jobId)}/run`
  );
  return response.data;
};

export const pauseScheduledJob = async (jobId: string): Promise<PauseResumeResponse> => {
  const response = await apiClient.post<PauseResumeResponse>(
    `/api/v1/admin/scheduler/jobs/${encodeURIComponent(jobId)}/pause`
  );
  return response.data;
};

export const resumeScheduledJob = async (jobId: string): Promise<PauseResumeResponse> => {
  const response = await apiClient.post<PauseResumeResponse>(
    `/api/v1/admin/scheduler/jobs/${encodeURIComponent(jobId)}/resume`
  );
  return response.data;
};

export const getScheduledJobLogs = async (
  skip = 0,
  limit = 50,
  jobId?: string,
  status?: string
): Promise<ScheduledJobLogsPaginated> => {
  const params = new URLSearchParams();
  params.append('skip', skip.toString());
  params.append('limit', limit.toString());
  if (jobId) params.append('job_id', jobId);
  if (status) params.append('status', status);

  const response = await apiClient.get<ScheduledJobLogsPaginated>(
    `/api/v1/admin/scheduler/logs?${params.toString()}`
  );
  return response.data;
};

export const pruneScheduledJobLogs = async (days = 30): Promise<{ message: string; deleted_count: number }> => {
  const response = await apiClient.delete<{ message: string; deleted_count: number }>(
    `/api/v1/admin/scheduler/logs?days=${days}`
  );
  return response.data;
};
