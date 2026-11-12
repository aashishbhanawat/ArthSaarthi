import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import {
    HomeIcon,
    BriefcaseIcon,
    ArrowUpTrayIcon,
    ListBulletIcon,
    UsersIcon,
    ArrowLeftOnRectangleIcon,
    EyeIcon,
    TrophyIcon,
    UserCircleIcon,
    ScaleIcon,
    BanknotesIcon,
    WrenchScrewdriverIcon,
    SunIcon,
    MoonIcon,
    ComputerDesktopIcon,
    ShieldCheckIcon,
    BellIcon,
} from '@heroicons/react/24/outline';
import { CorporateActionNotificationModal } from './Notifications/CorporateActionNotificationModal';
import { getCorporateActionEvents } from '../services/corporateActionsApi';

const appVersion = import.meta.env.VITE_APP_VERSION;


const NavBar: React.FC = () => {
    const { user, logout, deploymentMode } = useAuth();
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

    const baseLinkClass = "py-2 px-3 rounded-md transition-colors";
    const inactiveLinkClass = "text-gray-600 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-gray-100";
    const activeLinkClass = "font-semibold bg-blue-600 text-white";

    const linkClass = (isActive: boolean) =>
        `${baseLinkClass} ${isActive ? activeLinkClass : inactiveLinkClass} flex items-center gap-3`;

    return (
        <>
            <aside className="hidden lg:flex bg-white flex-col flex-shrink-0 w-64 p-4 border-r border-gray-200 dark:bg-gray-800 dark:border-gray-700 h-full max-h-full overflow-hidden">
                {/* Header with Logo & Notification Bell */}
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <img src="ArthSaarthi.png" alt="ArthSaarthi Logo" className="h-14 w-14" />
                        <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">ArthSaarthi</h2>
                    </div>
                    <button
                        onClick={() => setShowNotifications(true)}
                        className="relative p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition"
                        title="Automated Activity Receipts"
                        aria-label="Automated Activity Receipts"
                    >
                        <BellIcon className="h-5 w-5" />
                        {unreadCount > 0 && (
                            <span className="absolute top-1 right-1 flex h-4 w-4 items-center justify-center rounded-full bg-emerald-600 text-[10px] font-bold text-white shadow-sm">
                                {unreadCount > 9 ? '9+' : unreadCount}
                            </span>
                        )}
                    </button>
                </div>

            {/* Theme Selector */}
            <div className="flex items-center justify-center gap-1 p-1 rounded-lg bg-gray-100 dark:bg-gray-700 mb-4">
                <button
                    onClick={() => setTheme('light')}
                    className={`flex-1 py-1.5 rounded-md transition-colors flex items-center justify-center gap-1 ${theme === 'light'
                        ? 'bg-white dark:bg-gray-600 shadow-sm'
                        : 'hover:bg-gray-200 dark:hover:bg-gray-600'
                        }`}
                    title="Light mode"
                >
                    <SunIcon className={`h-4 w-4 ${theme === 'light' ? 'text-yellow-500' : 'text-gray-500 dark:text-gray-400'}`} />
                    <span className={`text-xs ${theme === 'light' ? 'text-gray-800 dark:text-gray-100' : 'text-gray-500 dark:text-gray-400'}`}>Light</span>
                </button>
                <button
                    onClick={() => setTheme('system')}
                    className={`flex-1 py-1.5 rounded-md transition-colors flex items-center justify-center gap-1 ${theme === 'system'
                        ? 'bg-white dark:bg-gray-600 shadow-sm'
                        : 'hover:bg-gray-200 dark:hover:bg-gray-600'
                        }`}
                    title="System preference"
                >
                    <ComputerDesktopIcon className={`h-4 w-4 ${theme === 'system' ? 'text-blue-500' : 'text-gray-500 dark:text-gray-400'}`} />
                    <span className={`text-xs ${theme === 'system' ? 'text-gray-800 dark:text-gray-100' : 'text-gray-500 dark:text-gray-400'}`}>Auto</span>
                </button>
                <button
                    onClick={() => setTheme('dark')}
                    className={`flex-1 py-1.5 rounded-md transition-colors flex items-center justify-center gap-1 ${theme === 'dark'
                        ? 'bg-white dark:bg-gray-600 shadow-sm'
                        : 'hover:bg-gray-200 dark:hover:bg-gray-600'
                        }`}
                    title="Dark mode"
                >
                    <MoonIcon className={`h-4 w-4 ${theme === 'dark' ? 'text-indigo-400' : 'text-gray-500 dark:text-gray-400'}`} />
                    <span className={`text-xs ${theme === 'dark' ? 'text-gray-800 dark:text-gray-100' : 'text-gray-500 dark:text-gray-400'}`}>Dark</span>
                </button>
            </div>

            <nav className="flex flex-col gap-2 flex-grow overflow-y-auto min-h-0 pr-1">
                <NavLink
                    to="/dashboard"
                    className={({ isActive }) => linkClass(isActive)}
                >
                    <HomeIcon className="h-5 w-5" />
                    <span>Dashboard</span>
                </NavLink>
                <NavLink
                    to="/portfolios"
                    className={({ isActive }) => linkClass(isActive)}
                >
                    <BriefcaseIcon className="h-5 w-5" />
                    <span>Portfolios</span>
                </NavLink>
                <NavLink
                    to="/transactions"
                    className={({ isActive }) => linkClass(isActive)}
                >
                    <ListBulletIcon className="h-5 w-5" aria-hidden="true" />
                    <span>Transactions</span>
                </NavLink>
                <NavLink
                    to="/capital-gains"
                    className={({ isActive }) => linkClass(isActive)}
                >
                    <ScaleIcon className="h-5 w-5" />
                    <span>Capital Gains</span>
                </NavLink>
                <NavLink
                    to="/income"
                    className={({ isActive }) => linkClass(isActive)}
                >
                    <BanknotesIcon className="h-5 w-5" />
                    <span>Income & Tax Hub</span>
                </NavLink>

                <NavLink to="/import" className={({ isActive }) => linkClass(isActive)}>
                    <ArrowUpTrayIcon className="h-5 w-5" /> <span>Import</span>
                </NavLink>
                <NavLink
                    to="/watchlists"
                    className={({ isActive }) => linkClass(isActive)}
                >
                    <EyeIcon className="h-5 w-5" />
                    <span>Watchlists</span>
                </NavLink>
                <NavLink
                    to="/goals"
                    className={({ isActive }) => linkClass(isActive)}
                >
                    <TrophyIcon className="h-5 w-5" />
                    <span>Goals</span>
                </NavLink>
                <NavLink
                    to="/risk-profile"
                    className={({ isActive }) => linkClass(isActive)}
                >
                    <ShieldCheckIcon className="h-5 w-5" />
                    <span>Risk Profile</span>
                </NavLink>
                {user?.is_admin && (
                    <>
                        {/* User Management is only available in server mode (multi-user) */}
                        {deploymentMode === 'server' && (
                            <NavLink to="/admin/users" className={({ isActive }) => linkClass(isActive)}>
                                <UsersIcon className="h-5 w-5" />
                                <span>User Management</span>
                            </NavLink>
                        )}
                        {/* Interest Rates and System Maintenance available in all modes */}
                        <NavLink to="/admin/interest-rates" className={({ isActive }) => linkClass(isActive)}>
                            <ScaleIcon className="h-5 w-5" />
                            <span>Interest Rates</span>
                        </NavLink>
                        <NavLink to="/admin/maintenance" className={({ isActive }) => linkClass(isActive)}>
                            <WrenchScrewdriverIcon className="h-5 w-5" />
                            <span>System Maintenance</span>
                        </NavLink>
                        <NavLink to="/admin/fmv" className={({ isActive }) => linkClass(isActive)}>
                            <ScaleIcon className="h-5 w-5" />
                            <span>FMV Management</span>
                        </NavLink>
                        <NavLink to="/admin/aliases" className={({ isActive }) => linkClass(isActive)}>
                            <ListBulletIcon className="h-5 w-5" aria-hidden="true" />
                            <span>Symbol Aliases</span>
                        </NavLink>
                    </>
                )}
            </nav>
            <div className="mt-auto pt-4 border-t dark:border-gray-700">
                <div className="text-center text-sm text-gray-600 dark:text-gray-400 mb-2 truncate" title={user?.email}>{user?.full_name || user?.email}</div>
                <NavLink
                    to="/profile"
                    className="btn btn-secondary w-full flex items-center justify-center mb-2"
                >
                    <UserCircleIcon className="h-5 w-5 mr-2" />
                    <span>Profile</span>
                </NavLink>
                <button
                    onClick={logout}
                    className="btn btn-danger w-full flex items-center justify-center"
                >
                    <ArrowLeftOnRectangleIcon className="h-5 w-5 mr-2" />
                    <span>Logout</span>
                </button>
                <div className="text-center text-xs text-gray-500 dark:text-gray-500 mt-4">
                    Version: {appVersion}
                </div>
            </div>
        </aside>
        <CorporateActionNotificationModal
            isOpen={showNotifications}
            onClose={() => setShowNotifications(false)}
            onCountChange={setUnreadCount}
        />
        </>
    );
};

export default NavBar;
