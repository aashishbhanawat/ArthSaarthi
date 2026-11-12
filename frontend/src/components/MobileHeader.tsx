import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { usePrivacy } from '../context/PrivacyContext';
import { useTheme } from '../context/ThemeContext';
import {
    EyeIcon,
    EyeSlashIcon,
    SunIcon,
    MoonIcon,
    ComputerDesktopIcon,
    BellIcon,
} from '@heroicons/react/24/outline';
import { CorporateActionNotificationModal } from './Notifications/CorporateActionNotificationModal';
import { getCorporateActionEvents } from '../services/corporateActionsApi';

const MobileHeader: React.FC = () => {
    const location = useLocation();
    const { isPrivacyMode, togglePrivacyMode } = usePrivacy();
    const { theme, setTheme } = useTheme();
    const [showNotifications, setShowNotifications] = useState(false);
    const [unreadCount, setUnreadCount] = useState(0);

    useEffect(() => {
        const fetchUnread = async () => {
            try {
                const res = await getCorporateActionEvents(undefined, 0, 1);
                setUnreadCount(res.unread_count);
            } catch (err) {
                // Silently handle if unauthenticated or error
            }
        };
        fetchUnread();
    }, []);

    // Derive title from path
    const getPageTitle = () => {
        const path = location.pathname;
        if (path.startsWith('/dashboard')) return 'Dashboard';
        if (path.startsWith('/portfolios')) return 'Portfolios';
        if (path.startsWith('/transactions')) return 'History';
        if (path.startsWith('/capital-gains')) return 'Capital Gains';
        if (path.startsWith('/import')) return 'Import';
        if (path.startsWith('/watchlists')) return 'Watchlists';
        if (path.startsWith('/goals')) return 'Goals';
        if (path.startsWith('/risk-profile')) return 'Risk Profiling';
        if (path.startsWith('/profile')) return 'Profile';
        if (path.startsWith('/admin')) return 'Admin';
        return 'ArthSaarthi';
    };

    const cycleTheme = () => {
        if (theme === 'light') setTheme('dark');
        else if (theme === 'dark') setTheme('system');
        else setTheme('light');
    };

    return (
        <>
        <header className="lg:hidden sticky top-0 z-40 w-full bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3 pt-safe flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-3">
                <img src="ArthSaarthi.png" alt="Logo" className="h-8 w-8" />
                <h1 className="text-xl font-bold text-gray-800 dark:text-gray-100 truncate max-w-[150px]">
                    {getPageTitle()}
                </h1>
            </div>

            <div className="flex items-center gap-2">
                <button
                    onClick={togglePrivacyMode}
                    className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    aria-label="Toggle Privacy"
                >
                    {isPrivacyMode ? (
                        <EyeSlashIcon className="h-5 w-5 text-gray-500" />
                    ) : (
                        <EyeIcon className="h-5 w-5 text-gray-500" />
                    )}
                </button>

                <button
                    onClick={() => setShowNotifications(true)}
                    className="relative p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    aria-label="Automated Activity Receipts"
                >
                    <BellIcon className="h-5 w-5 text-gray-500" />
                    {unreadCount > 0 && (
                        <span className="absolute top-1 right-1 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-emerald-600 text-[9px] font-bold text-white">
                            {unreadCount > 9 ? '9+' : unreadCount}
                        </span>
                    )}
                </button>

                <button
                    onClick={cycleTheme}
                    className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    aria-label="Cycle Theme"
                >
                    {theme === 'light' && <SunIcon className="h-5 w-5 text-yellow-500" />}
                    {theme === 'dark' && <MoonIcon className="h-5 w-5 text-indigo-400" />}
                    {theme === 'system' && <ComputerDesktopIcon className="h-5 w-5 text-blue-500" />}
                </button>
            </div>
        </header>
        <CorporateActionNotificationModal
            isOpen={showNotifications}
            onClose={() => setShowNotifications(false)}
            onCountChange={setUnreadCount}
        />
        </>
    );
};

export default MobileHeader;
