import { useEffect, useState } from 'react';
import { FiDownload, FiX, FiInfo, FiExternalLink } from 'react-icons/fi';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';

interface UpdateInfo {
    available: boolean;
    version?: string;
    url?: string;
    name?: string;
    error?: string;
}

const DISMISSED_VERSION_KEY = 'dismissed_update_version';

export default function UpdateBanner() {
    const [updateInfo, setUpdateInfo] = useState<UpdateInfo | null>(null);
    const [dismissed, setDismissed] = useState(false);
    const [isDesktopMode, setIsDesktopMode] = useState(false);
    const { user } = useAuth();

    const isAdmin = user?.is_admin === true;

    useEffect(() => {
        const checkUpdates = async () => {
            try {
                let result: UpdateInfo;

                // Check if running in Electron (desktop mode)
                if (window.electronAPI?.checkForUpdates) {
                    setIsDesktopMode(true);
                    result = await window.electronAPI.checkForUpdates();
                } else {
                    // Server mode - call backend API
                    setIsDesktopMode(false);
                    const response = await api.get('/api/v1/system/check-updates');
                    result = response.data;
                }

                if (result.available && result.version) {
                    // Check if this version was already dismissed
                    const dismissedVersion = localStorage.getItem(DISMISSED_VERSION_KEY);
                    if (dismissedVersion === result.version) {
                        setDismissed(true);
                        return;
                    }
                    setUpdateInfo(result);
                }
            } catch (err) {
                console.error('Failed to check for updates:', err);
            }
        };

        // Check after a short delay to not block initial load
        const timer = setTimeout(checkUpdates, 3000);
        return () => clearTimeout(timer);
    }, []);

    const handleViewRelease = () => {
        if (updateInfo?.url) {
            if (isDesktopMode && window.electronAPI?.openReleasePage) {
                window.electronAPI.openReleasePage(updateInfo.url);
            } else {
                // Server mode - open in new tab
                window.open(updateInfo.url, '_blank', 'noopener,noreferrer');
            }
        }
    };

    const handleDismiss = () => {
        if (updateInfo?.version) {
            localStorage.setItem(DISMISSED_VERSION_KEY, updateInfo.version);
        }
        setDismissed(true);
    };

    // Don't render if no update available or dismissed
    if (!updateInfo?.available || dismissed) {
        return null;
    }

    // Desktop mode - always show Download button
    if (isDesktopMode) {
        return (
            <div className="update-banner">
                <div className="update-banner-content">
                    <FiDownload className="update-icon" />
                    <span className="update-text">
                        <strong>ArthSaarthi {updateInfo.version}</strong> is available!
                    </span>
                    <button
                        onClick={handleViewRelease}
                        className="update-download-btn"
                        title="Open GitHub Releases"
                    >
                        Download
                    </button>
                </div>
                <button
                    onClick={handleDismiss}
                    className="update-dismiss-btn"
                    title="Dismiss this notification"
                    aria-label="Close banner"
                >
                    <FiX />
                </button>
            </div>
        );
    }

    // Server mode - Admin: show View Release Notes, Regular user: Ask admin
    return (
        <div className="update-banner">
            <div className="update-banner-content">
                <FiInfo className="update-icon" />
                <span className="update-text">
                    <strong>ArthSaarthi {updateInfo.version}</strong> is available!
                    {!isAdmin && (
                        <span className="update-admin-note"> Ask your administrator to update.</span>
                    )}
                </span>
                {isAdmin && (
                    <button
                        onClick={handleViewRelease}
                        className="update-download-btn"
                        title="View release notes on GitHub"
                    >
                        <FiExternalLink className="inline mr-1" />
                        View Release Notes
                    </button>
                )}
            </div>
            <button
                onClick={handleDismiss}
                className="update-dismiss-btn"
                title="Dismiss this notification"
                aria-label="Close banner"
            >
                <FiX />
            </button>
        </div>
    );
}
