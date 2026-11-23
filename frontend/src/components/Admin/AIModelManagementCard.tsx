import React, { useCallback, useEffect, useState } from 'react';
import {
    CpuChipIcon,
    ArrowDownTrayIcon,
    TrashIcon,
    ArrowPathIcon,
    ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import {
    deleteEdgeModel,
    downloadEdgeModel,
    EdgeModelInfo,
    getEdgeModels,
    getModelProgress,
} from '../../services/mlApi';
import { useToast } from '../../context/ToastContext';

/**
 * AIModelManagementCard - Admin component for managing shared server Edge ML models.
 * FR10.7: Shared Edge ML Model Administration & Storage Management.
 */
export const AIModelManagementCard: React.FC = () => {
    const [models, setModels] = useState<EdgeModelInfo[]>([]);
    const [loadingModels, setLoadingModels] = useState(false);
    const [actionInProgress, setActionInProgress] = useState<string | null>(null);
    const { showToast } = useToast();

    const fetchModels = useCallback(async () => {
        try {
            setLoadingModels(true);
            const data = await getEdgeModels();
            setModels(data);
        } catch {
            showToast('Failed to load edge model status.', 'error');
        } finally {
            setLoadingModels(false);
        }
    }, [showToast]);

    useEffect(() => {
        fetchModels();
    }, [fetchModels]);

    // Poll while any model download is actively in progress
    useEffect(() => {
        const hasDownloading = models.some((m) => m.status === 'DOWNLOADING');
        if (!hasDownloading) return;

        const interval = setInterval(async () => {
            try {
                const data = await getEdgeModels();
                setModels(data);
            } catch {
                // Silently handle polling error
            }
        }, 1500);

        return () => clearInterval(interval);
    }, [models]);

    const handleDownload = async (modelId: string) => {
        setActionInProgress(modelId);
        try {
            const updated = await downloadEdgeModel(modelId);
            setModels((prev) => prev.map((m) => (m.id === modelId ? updated : m)));
            showToast(`Started download of model ${modelId}.`, 'success');
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : 'Failed to start download';
            showToast(message, 'error');
            const data = await getModelProgress(modelId).catch(() => null);
            if (data) setModels((prev) => prev.map((m) => (m.id === modelId ? data : m)));
        } finally {
            setActionInProgress(null);
        }
    };

    const handleDelete = async (modelId: string, modelName: string) => {
        if (!window.confirm(`Are you sure you want to delete ${modelName}? This will reclaim server disk space and switch sentiment analysis back to the financial lexicon for all users.`)) {
            return;
        }

        setActionInProgress(modelId);
        try {
            await deleteEdgeModel(modelId);
            showToast(`Model ${modelName} deleted from server storage.`, 'success');
            await fetchModels();
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : 'Failed to delete model';
            showToast(message, 'error');
        } finally {
            setActionInProgress(null);
        }
    };

    return (
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <CpuChipIcon className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                    <div>
                        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                            Shared Edge ML Models
                        </h2>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                            Manage server-level quantized machine learning models stored on disk for offline sentiment analysis and market research.
                        </p>
                    </div>
                </div>
                <button
                    type="button"
                    onClick={fetchModels}
                    disabled={loadingModels}
                    className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition"
                    title="Refresh Model Status"
                    aria-label="Refresh Model Status"
                >
                    <ArrowPathIcon className={`h-5 w-5 ${loadingModels ? 'animate-spin' : ''}`} />
                </button>
            </div>

            <div className="space-y-4">
                {models.length === 0 && !loadingModels && (
                    <div className="p-4 rounded-lg bg-gray-50 dark:bg-gray-700/50 text-sm text-gray-500 text-center">
                        No Edge ML models registered in system catalog.
                    </div>
                )}

                {models.map((model) => (
                    <div
                        key={model.id}
                        className="p-5 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50 flex flex-col gap-4"
                    >
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                            <div>
                                <div className="flex items-center gap-2">
                                    <span className="font-semibold text-gray-900 dark:text-white">
                                        {model.name}
                                    </span>
                                    <span className="text-xs text-gray-500 dark:text-gray-400">
                                        ({model.size_mb} MB)
                                    </span>
                                </div>
                                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 max-w-xl">
                                    {model.description}
                                </p>
                            </div>

                            {/* Status Badges */}
                            <div>
                                {model.status === 'ACTIVE' && (
                                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300">
                                        <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
                                        Active (ONNX Inference)
                                    </span>
                                )}
                                {model.status === 'DOWNLOADING' && (
                                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-950/40 dark:text-blue-300">
                                        <ArrowPathIcon className="h-3.5 w-3.5 animate-spin" />
                                        Downloading ({model.progress_percentage}%)
                                    </span>
                                )}
                                {model.status === 'FAILED' && (
                                    <span
                                        title={model.error_message || undefined}
                                        className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-800 dark:bg-red-950/40 dark:text-red-300"
                                    >
                                        <ExclamationTriangleIcon className="h-3.5 w-3.5" />
                                        Download Failed
                                    </span>
                                )}
                                {model.status === 'NOT_DOWNLOADED' && (
                                    <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300">
                                        Not Downloaded (Lexicon Fallback)
                                    </span>
                                )}
                            </div>
                        </div>

                        {/* Error message display */}
                        {model.status === 'FAILED' && model.error_message && (
                            <div className="p-2.5 rounded bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 text-xs text-red-700 dark:text-red-300">
                                {model.error_message}
                            </div>
                        )}

                        {/* Progress Bar */}
                        {model.status === 'DOWNLOADING' && (
                            <div className="w-full space-y-1">
                                <div className="w-full bg-gray-200 dark:bg-gray-700 h-2 rounded-full overflow-hidden">
                                    <div
                                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                                        style={{ width: `${model.progress_percentage}%` }}
                                    ></div>
                                </div>
                                <div className="flex justify-between text-[11px] text-gray-500">
                                    <span>Downloading quantized ONNX weights to server disk...</span>
                                    <span>{model.progress_percentage}%</span>
                                </div>
                            </div>
                        )}

                        {/* Administrative Actions */}
                        <div className="flex items-center gap-3 pt-2 border-t border-gray-200 dark:border-gray-700">
                            {model.status !== 'ACTIVE' && model.status !== 'DOWNLOADING' && (
                                <button
                                    type="button"
                                    onClick={() => handleDownload(model.id)}
                                    disabled={actionInProgress === model.id}
                                    className="btn btn-primary text-xs flex items-center gap-1.5 py-1.5 px-3"
                                >
                                    <ArrowDownTrayIcon className="h-4 w-4" />
                                    {model.status === 'FAILED'
                                        ? 'Retry Download'
                                        : `Download to Server (${model.size_mb} MB)`}
                                </button>
                            )}

                            {model.status === 'ACTIVE' && (
                                <button
                                    type="button"
                                    onClick={() => handleDelete(model.id, model.name)}
                                    disabled={actionInProgress === model.id}
                                    className="btn btn-secondary text-xs flex items-center gap-1.5 py-1.5 px-3 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/20"
                                >
                                    <TrashIcon className="h-4 w-4" />
                                    Delete Model (Free Space)
                                </button>
                            )}

                            <span className="text-[11px] text-gray-400 ml-auto">
                                Storage path: <code className="bg-gray-100 dark:bg-gray-700 px-1 py-0.5 rounded">data/models/{model.id}.onnx</code>
                            </span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default AIModelManagementCard;
