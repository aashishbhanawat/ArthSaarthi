import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import PythonBackend from '../../plugins/PythonBackend';
import { useToast } from '../../context/ToastContext';
import { Capacitor } from '@capacitor/core';

const AndroidSettingsCard = () => {
    const { deploymentMode } = useAuth();
    const { showToast } = useToast();
    const [enabled, setEnabled] = useState(true);

    useEffect(() => {
        if (deploymentMode === 'android' && Capacitor.isNativePlatform()) {
            const stored = localStorage.getItem('android_background_snapshot');
            if (stored === null) {
                // Default to true
                enableSnapshot(true);
            } else {
                setEnabled(stored === 'true');
            }
        }
    }, [deploymentMode]);

    const enableSnapshot = async (isInit = false) => {
        try {
            await PythonBackend.enableDailySnapshot();
            localStorage.setItem('android_background_snapshot', 'true');
            setEnabled(true);
            if (!isInit) showToast('Background daily snapshots enabled', 'success');
        } catch (e: unknown) {
            if (!isInit) showToast('Failed to enable: ' + (e as Error).message, 'error');
        }
    }

    const disableSnapshot = async () => {
        try {
            await PythonBackend.disableDailySnapshot();
            localStorage.setItem('android_background_snapshot', 'false');
            setEnabled(false);
            showToast('Background daily snapshots disabled', 'success');
        } catch (e: unknown) {
            showToast('Failed to disable: ' + (e as Error).message, 'error');
        }
    }

    const handleToggle = () => {
        if (enabled) {
            disableSnapshot();
        } else {
            enableSnapshot();
        }
    }

    if (deploymentMode !== 'android' || !Capacitor.isNativePlatform()) {
        return null;
    }

    return (
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                        Android Background Sync
                    </h3>
                    <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                        Automatically update portfolio values once a day in the background. Uses minimal battery and only runs on Wi-Fi or Cellular data.
                    </p>
                </div>
                <div className="ml-4">
                    <button
                        onClick={handleToggle}
                        className={`relative inline-flex flex-shrink-0 h-6 w-11 border-2 border-transparent rounded-full cursor-pointer transition-colors ease-in-out duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${enabled ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'}`}
                    >
                        <span className="sr-only">Use setting</span>
                        <span
                            aria-hidden="true"
                            className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform ring-0 transition ease-in-out duration-200 ${enabled ? 'translate-x-5' : 'translate-x-0'}`}
                        />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AndroidSettingsCard;
