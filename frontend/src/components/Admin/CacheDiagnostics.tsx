import React, { useEffect, useState } from 'react';
import apiClient from '../../services/api';

interface RateLimitInfo {
  provider: string;
  current_calls: number;
  max_limit: number;
  window_seconds: number;
}

interface CacheStatsResponse {
  status: string;
  cache_type: string;
  performance: {
    hits: number;
    misses: number;
    total_requests: number;
    hit_ratio_percent: number;
  };
  rate_limits: Record<string, RateLimitInfo>;
}

export const CacheDiagnostics: React.FC = () => {
  const [data, setData] = useState<CacheStatsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [clearing, setClearing] = useState<boolean>(false);
  const [message, setMessage] = useState<string | null>(null);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<CacheStatsResponse>('/api/v1/admin/cache/stats');
      setData(res.data);
    } catch (err: unknown) {
      console.error('Failed to fetch cache stats:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClearCache = async () => {
    if (!window.confirm('Are you sure you want to flush all application cache entries?')) {
      return;
    }
    try {
      setClearing(true);
      setMessage(null);
      await apiClient.post('/api/v1/admin/cache/clear');
      setMessage('Cache flushed successfully!');
      await fetchStats();
    } catch (err: unknown) {
      const errorMsg =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : (err as Error).message;
      setMessage(`Failed to clear cache: ${errorMsg || 'Unknown error'}`);
    } finally {
      setClearing(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (loading && !data) {
    return (
      <div className="p-4 bg-white dark:bg-gray-800 rounded-lg shadow animate-pulse">
        <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-4"></div>
        <div className="h-20 bg-gray-200 dark:bg-gray-700 rounded mb-4"></div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border border-gray-200 dark:border-gray-700">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            Cache & API Rate Limit Diagnostics
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Engine Type:{' '}
            <span className="font-semibold text-blue-600 dark:text-blue-400">
              {data?.cache_type || 'Disabled'}
            </span>
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchStats}
            className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200 rounded font-medium transition"
          >
            Refresh
          </button>
          <button
            onClick={handleClearCache}
            disabled={clearing}
            className="px-4 py-1.5 text-sm bg-red-600 hover:bg-red-700 text-white rounded font-medium transition disabled:opacity-50"
          >
            {clearing ? 'Flushing...' : 'Flush Cache'}
          </button>
        </div>
      </div>

      {message && (
        <div className="mb-4 p-3 text-sm rounded bg-blue-50 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">
          {message}
        </div>
      )}

      {/* Performance Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-100 dark:border-gray-700">
          <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">Hit Ratio</p>
          <p className="text-2xl font-bold text-green-600 dark:text-green-400">
            {data?.performance.hit_ratio_percent}%
          </p>
        </div>
        <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-100 dark:border-gray-700">
          <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">Hits</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {data?.performance.hits}
          </p>
        </div>
        <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-100 dark:border-gray-700">
          <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">Misses</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {data?.performance.misses}
          </p>
        </div>
        <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-100 dark:border-gray-700">
          <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">Total Requests</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {data?.performance.total_requests}
          </p>
        </div>
      </div>

      {/* Rate Limits Usage */}
      <div>
        <h3 className="text-md font-semibold text-gray-800 dark:text-gray-200 mb-3">
          Provider Rate Limit Usage (Current Window)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data?.rate_limits &&
            Object.entries(data.rate_limits).map(([providerKey, info]) => {
              const usagePercent = Math.min(
                100,
                Math.round((info.current_calls / info.max_limit) * 100)
              );
              return (
                <div
                  key={providerKey}
                  className="p-3 bg-gray-50 dark:bg-gray-700/30 rounded border border-gray-200 dark:border-gray-700"
                >
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm font-medium capitalize text-gray-800 dark:text-gray-200">
                      {info.provider}
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {info.current_calls} / {info.max_limit} per {info.window_seconds}s
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all duration-300 ${
                        usagePercent > 80 ? 'bg-red-500' : 'bg-blue-600'
                      }`}
                      style={{ width: `${usagePercent}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
        </div>
      </div>
    </div>
  );
};
