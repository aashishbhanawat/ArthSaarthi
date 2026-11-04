import React, { useEffect, useState } from 'react';
import {
  getSchedulerSummary,
  getScheduledJobLogs,
  pauseScheduledJob,
  pruneScheduledJobLogs,
  resumeScheduledJob,
  triggerJobNow,
} from '../../services/schedulerApi';
import { JobInfo, ScheduledJobLogItem, SchedulerSummary } from '../../types/scheduler';

export const SchedulerDashboard: React.FC = () => {
  const [summary, setSummary] = useState<SchedulerSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({});
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  // Activity history modal/drawer state
  const [showLogsModal, setShowLogsModal] = useState<boolean>(false);
  const [logs, setLogs] = useState<ScheduledJobLogItem[]>([]);
  const [logsLoading, setLogsLoading] = useState<boolean>(false);
  const [pruning, setPruning] = useState<boolean>(false);

  const fetchSummary = async () => {
    try {
      setLoading(true);
      const data = await getSchedulerSummary();
      setSummary(data);
    } catch (err: unknown) {
      console.error('Failed to fetch task summary:', err);
      const errMsg =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : (err as Error).message;
      setMessage({ text: `Failed to load task data: ${errMsg}`, type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const fetchLogs = async () => {
    try {
      setLogsLoading(true);
      const res = await getScheduledJobLogs(0, 50);
      setLogs(res.items);
    } catch (err: unknown) {
      console.error('Failed to fetch activity logs:', err);
    } finally {
      setLogsLoading(false);
    }
  };

  const handleOpenLogs = async () => {
    setShowLogsModal(true);
    await fetchLogs();
  };

  const handleTriggerJob = async (jobId: string, jobName: string) => {
    try {
      setActionLoading((prev) => ({ ...prev, [jobId]: true }));
      setMessage(null);
      await triggerJobNow(jobId);
      setMessage({ text: `Started task: "${jobName}"`, type: 'success' });
      await fetchSummary();
    } catch (err: unknown) {
      const errMsg =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : (err as Error).message;
      setMessage({ text: errMsg || 'Failed to start task', type: 'error' });
    } finally {
      setActionLoading((prev) => ({ ...prev, [jobId]: false }));
    }
  };

  const handleTogglePause = async (job: JobInfo) => {
    const isPaused = job.status === 'PAUSED';
    try {
      setActionLoading((prev) => ({ ...prev, [job.id]: true }));
      setMessage(null);
      if (isPaused) {
        await resumeScheduledJob(job.id);
        setMessage({ text: `Resumed task: "${job.name}"`, type: 'success' });
      } else {
        await pauseScheduledJob(job.id);
        setMessage({ text: `Paused task: "${job.name}"`, type: 'success' });
      }
      await fetchSummary();
    } catch (err: unknown) {
      const errMsg =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : (err as Error).message;
      setMessage({ text: errMsg || 'Failed to update task status', type: 'error' });
    } finally {
      setActionLoading((prev) => ({ ...prev, [job.id]: false }));
    }
  };

  const handlePruneLogs = async () => {
    if (!window.confirm('Are you sure you want to clear history older than 30 days?')) return;
    try {
      setPruning(true);
      const res = await pruneScheduledJobLogs(30);
      setMessage({ text: `Cleared ${res.deleted_count} older records.`, type: 'success' });
      await fetchLogs();
    } catch (err: unknown) {
      setMessage({ text: 'Failed to clear activity history', type: 'error' });
    } finally {
      setPruning(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  const formatSchedule = (triggerStr: string) => {
    if (!triggerStr) return 'Manual';
    if (triggerStr.includes("hour='0'") && triggerStr.includes("minute='5'")) {
      return 'Daily at 00:05';
    }
    if (triggerStr.includes('6:00:00') || triggerStr.includes('hours=6')) {
      return 'Every 6 hours';
    }
    if (triggerStr.startsWith('cron')) {
      return 'Daily Scheduled';
    }
    if (triggerStr.startsWith('interval')) {
      return 'Periodic Interval';
    }
    return triggerStr;
  };

  const formatDateTime = (isoString?: string | null) => {
    if (!isoString) return 'Paused / Not Scheduled';
    const date = new Date(isoString);
    return date.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'RUNNING':
        return (
          <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300 animate-pulse">
            In Progress
          </span>
        );
      case 'ACTIVE':
        return (
          <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300">
            Active
          </span>
        );
      case 'PAUSED':
        return (
          <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-slate-200 text-slate-800 dark:bg-slate-700 dark:text-slate-300">
            Paused
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
            {status}
          </span>
        );
    }
  };

  if (loading && !summary) {
    return (
      <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow animate-pulse">
        <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-4"></div>
        <div className="h-24 bg-gray-200 dark:bg-gray-700 rounded mb-4"></div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              Automated Tasks
            </h2>
            <span
              className={`px-2 py-0.5 text-xs font-bold rounded ${
                summary?.is_running
                  ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300'
                  : 'bg-rose-100 text-rose-800 dark:bg-rose-900/50 dark:text-rose-300'
              }`}
            >
              {summary?.is_running ? 'Active' : 'Stopped'}
            </span>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Automated daily portfolio valuation snapshots, corporate action processing, and routine maintenance tasks.
          </p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={fetchSummary}
            disabled={loading}
            className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 rounded transition font-medium"
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
          <button
            onClick={handleOpenLogs}
            className="px-3 py-1.5 text-sm bg-primary-600 hover:bg-primary-700 text-white rounded transition font-medium"
          >
            Activity History
          </button>
        </div>
      </div>

      {/* Alert Banner */}
      {message && (
        <div
          className={`mb-6 p-4 rounded-lg flex items-center justify-between text-sm ${
            message.type === 'success'
              ? 'bg-emerald-50 text-emerald-800 border border-emerald-200 dark:bg-emerald-900/20 dark:text-emerald-300 dark:border-emerald-800'
              : 'bg-rose-50 text-rose-800 border border-rose-200 dark:bg-rose-900/20 dark:text-rose-300 dark:border-rose-800'
          }`}
        >
          <span>{message.text}</span>
          <button
            onClick={() => setMessage(null)}
            className="ml-4 font-bold text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            &times;
          </button>
        </div>
      )}

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-lg border border-gray-100 dark:border-gray-700">
          <span className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider font-semibold">
            Total Tasks
          </span>
          <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
            {summary?.total_jobs ?? 0}
          </p>
        </div>
        <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-lg border border-gray-100 dark:border-gray-700">
          <span className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider font-semibold">
            Active
          </span>
          <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
            {summary?.active_jobs ?? 0}
          </p>
        </div>
        <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-lg border border-gray-100 dark:border-gray-700">
          <span className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider font-semibold">
            Paused
          </span>
          <p className="text-2xl font-bold text-amber-600 dark:text-amber-400 mt-1">
            {summary?.paused_jobs ?? 0}
          </p>
        </div>
        <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-lg border border-gray-100 dark:border-gray-700">
          <span className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider font-semibold">
            Errors (24h)
          </span>
          <p
            className={`text-2xl font-bold mt-1 ${
              (summary?.failed_last_24h ?? 0) > 0
                ? 'text-rose-600 dark:text-rose-400'
                : 'text-gray-900 dark:text-white'
            }`}
          >
            {summary?.failed_last_24h ?? 0}
          </p>
        </div>
      </div>

      {/* Desktop Task Table */}
      <div className="hidden md:block overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700 text-sm">
          <thead className="bg-gray-50 dark:bg-gray-700/50">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-gray-500 dark:text-gray-400">
                Task
              </th>
              <th className="px-4 py-3 text-left font-medium text-gray-500 dark:text-gray-400">
                Frequency
              </th>
              <th className="px-4 py-3 text-left font-medium text-gray-500 dark:text-gray-400">
                Next Run
              </th>
              <th className="px-4 py-3 text-center font-medium text-gray-500 dark:text-gray-400">
                Status
              </th>
              <th className="px-4 py-3 text-right font-medium text-gray-500 dark:text-gray-400">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-gray-800">
            {summary?.jobs.map((job) => (
              <tr key={job.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                <td className="px-4 py-3">
                  <div className="font-semibold text-gray-900 dark:text-white">{job.name}</div>
                  {job.description && (
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 max-w-sm">
                      {job.description}
                    </div>
                  )}
                </td>
                <td className="px-4 py-3 text-xs text-gray-700 dark:text-gray-300">
                  {formatSchedule(job.trigger)}
                </td>
                <td className="px-4 py-3 text-xs text-gray-700 dark:text-gray-300">
                  {formatDateTime(job.next_run_time)}
                </td>
                <td className="px-4 py-3 text-center">{getStatusBadge(job.status)}</td>
                <td className="px-4 py-3 text-right">
                  <div className="inline-flex gap-2">
                    <button
                      onClick={() => handleTriggerJob(job.id, job.name)}
                      disabled={actionLoading[job.id] || job.status === 'RUNNING'}
                      className="px-2.5 py-1 text-xs bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white rounded font-medium transition"
                    >
                      {actionLoading[job.id] ? 'Starting...' : 'Run Now'}
                    </button>
                    <button
                      onClick={() => handleTogglePause(job)}
                      disabled={actionLoading[job.id]}
                      className="px-2.5 py-1 text-xs bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 rounded font-medium transition"
                    >
                      {job.status === 'PAUSED' ? 'Resume' : 'Pause'}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile Task Cards View (< 768px) */}
      <div className="md:hidden space-y-4">
        {summary?.jobs.map((job) => (
          <div
            key={job.id}
            className="p-4 bg-gray-50 dark:bg-gray-700/40 rounded-lg border border-gray-200 dark:border-gray-700"
          >
            <div className="flex justify-between items-start gap-2 mb-2">
              <h3 className="font-semibold text-gray-900 dark:text-white text-base">
                {job.name}
              </h3>
              <div>{getStatusBadge(job.status)}</div>
            </div>

            {job.description && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">{job.description}</p>
            )}

            <div className="space-y-1 mb-4 text-xs text-gray-700 dark:text-gray-300">
              <div>
                <span className="font-medium text-gray-500 dark:text-gray-400">Frequency: </span>
                <span>{formatSchedule(job.trigger)}</span>
              </div>
              <div>
                <span className="font-medium text-gray-500 dark:text-gray-400">Next Run: </span>
                <span>{formatDateTime(job.next_run_time)}</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 pt-2 border-t border-gray-200 dark:border-gray-600">
              <button
                onClick={() => handleTriggerJob(job.id, job.name)}
                disabled={actionLoading[job.id] || job.status === 'RUNNING'}
                className="w-full py-2 text-sm bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white rounded-md font-medium transition"
              >
                {actionLoading[job.id] ? 'Starting...' : 'Run Now'}
              </button>
              <button
                onClick={() => handleTogglePause(job)}
                disabled={actionLoading[job.id]}
                className="w-full py-2 text-sm bg-gray-200 hover:bg-gray-300 dark:bg-gray-600 dark:hover:bg-gray-500 text-gray-800 dark:text-gray-200 rounded-md font-medium transition"
              >
                {job.status === 'PAUSED' ? 'Resume' : 'Pause'}
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Activity History Modal */}
      {showLogsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-4xl max-h-[85vh] flex flex-col border border-gray-200 dark:border-gray-700">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700">
              <div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                  Task Activity History
                </h3>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  Recent automated task runs and system activity.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handlePruneLogs}
                  disabled={pruning}
                  className="px-3 py-1.5 text-xs text-rose-600 hover:text-rose-700 hover:bg-rose-50 dark:hover:bg-rose-900/20 rounded font-medium transition border border-rose-200 dark:border-rose-800"
                >
                  {pruning ? 'Clearing...' : 'Clear Old History'}
                </button>
                <button
                  onClick={() => setShowLogsModal(false)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-xl font-bold p-1"
                >
                  &times;
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="overflow-y-auto p-5 flex-1 space-y-3">
              {logsLoading ? (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400 text-sm">
                  Loading activity history...
                </div>
              ) : logs.length === 0 ? (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400 text-sm">
                  No task activity recorded yet.
                </div>
              ) : (
                logs.map((log) => (
                  <div
                    key={log.id}
                    className="p-3.5 bg-gray-50 dark:bg-gray-700/30 rounded-lg border border-gray-200 dark:border-gray-700 text-xs"
                  >
                    <div className="flex justify-between items-start mb-1.5">
                      <span className="font-semibold text-gray-900 dark:text-white text-sm">
                        {log.job_name}
                      </span>
                      <span
                        className={`px-2 py-0.5 font-bold rounded ${
                          log.status === 'SUCCESS'
                            ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300'
                            : 'bg-rose-100 text-rose-800 dark:bg-rose-900/50 dark:text-rose-300'
                        }`}
                      >
                        {log.status === 'SUCCESS' ? 'Completed' : 'Failed'}
                      </span>
                    </div>

                    <div className="flex flex-wrap gap-x-4 gap-y-1 text-gray-500 dark:text-gray-400 mt-1">
                      <span>Ran: {formatDateTime(log.started_at)}</span>
                      {log.execution_time_seconds !== null && (
                        <span>Duration: {log.execution_time_seconds.toFixed(2)}s</span>
                      )}
                    </div>

                    {log.error_message && (
                      <div className="mt-2.5 p-2.5 bg-gray-900 text-rose-300 font-mono rounded overflow-x-auto text-[11px] whitespace-pre-wrap border border-rose-950">
                        {log.error_message}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex justify-end">
              <button
                onClick={() => setShowLogsModal(false)}
                className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 rounded font-medium transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SchedulerDashboard;
