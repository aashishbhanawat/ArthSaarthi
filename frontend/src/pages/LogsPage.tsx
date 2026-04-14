import React, { useState, useEffect, useRef } from 'react';
import api from '../services/api';
import { ClipboardIcon, ArrowPathIcon, ChevronLeftIcon } from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';

const LogsPage: React.FC = () => {
    const [logs, setLogs] = useState<string>('Loading logs...');
    const [loading, setLoading] = useState<boolean>(true);
    const [autoRefresh, setAutoRefresh] = useState<boolean>(false);
    const logContainerRef = useRef<HTMLPreElement>(null);
    const navigate = useNavigate();

    const fetchLogs = async () => {
        setLoading(true);
        try {
            const response = await api.get('/api/v1/system/logs');
            setLogs(response.data.msg);
        } catch (error) {
            setLogs('Error fetching logs. Make sure you are an admin and the backend is running.');
            console.error('Failed to fetch logs:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchLogs();
    }, []);

    useEffect(() => {
        let interval: NodeJS.Timeout | undefined;
        if (autoRefresh) {
            interval = setInterval(fetchLogs, 5000);
        }
        return () => clearInterval(interval);
    }, [autoRefresh]);

    useEffect(() => {
        // Scroll to bottom when logs change
        if (logContainerRef.current) {
            logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
        }
    }, [logs]);

    const copyToClipboard = () => {
        navigator.clipboard.writeText(logs);
        alert('Logs copied to clipboard');
    };

    return (
        <div className="flex flex-col h-[calc(100vh-64px)] bg-gray-50 dark:bg-gray-900 overflow-hidden">
            <div className="flex items-center justify-between p-4 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm">
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => navigate(-1)}
                        className="p-2 -ml-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full"
                    >
                        <ChevronLeftIcon className="h-6 w-6" />
                    </button>
                    <h1 className="text-xl font-bold text-gray-900 dark:text-white">System Logs</h1>
                </div>

                <div className="flex gap-2">
                    <button
                        onClick={() => setAutoRefresh(!autoRefresh)}
                        className={`p-2 rounded-lg border flex items-center gap-2 text-sm font-medium transition-colors ${autoRefresh
                            ? 'bg-blue-50 border-blue-200 text-blue-600 dark:bg-blue-900/30 dark:border-blue-800 dark:text-blue-400'
                            : 'bg-white border-gray-200 text-gray-700 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300'
                            }`}
                    >
                        <ArrowPathIcon className={`h-5 w-5 ${autoRefresh ? 'animate-spin' : ''}`} />
                        <span className="hidden sm:inline">{autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}</span>
                    </button>

                    <button
                        onClick={copyToClipboard}
                        className="p-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
                        title="Copy to clipboard"
                    >
                        <ClipboardIcon className="h-5 w-5" />
                    </button>

                    <button
                        onClick={fetchLogs}
                        disabled={loading}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-all shadow-sm active:scale-95 disabled:opacity-50"
                    >
                        Refresh
                    </button>
                </div>
            </div>

            <div className="flex-1 overflow-hidden p-4">
                <div className="h-full bg-gray-900 rounded-xl border border-gray-800 shadow-inner overflow-hidden flex flex-col">
                    <pre
                        ref={logContainerRef}
                        className="flex-1 overflow-auto p-4 font-mono text-sm text-green-400 whitespace-pre-wrap selection:bg-green-800 selection:text-white"
                    >
                        {logs || 'No logs available.'}
                    </pre>
                    {loading && (
                        <div className="px-4 py-1 bg-gray-800 text-[10px] text-gray-500 font-mono italic">
                            Updating...
                        </div>
                    )}
                </div>
            </div>

            <div className="p-4 bg-gray-50 dark:bg-gray-900 text-xs text-gray-500 dark:text-gray-400 text-center">
                Showing last 1000 lines of system output.
            </div>
        </div>
    );
};

export default LogsPage;
