import React from 'react';
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
    WrenchScrewdriverIcon,
    SunIcon,
    MoonIcon,
} from '@heroicons/react/24/outline';

const appVersion = import.meta.env.VITE_APP_VERSION;


const NavBar: React.FC = () => {
    const { user, logout, deploymentMode } = useAuth();
    const { isDarkMode, toggleDarkMode } = useTheme();

    const baseLinkClass = "py-2 px-3 rounded-md transition-colors";
    const inactiveLinkClass = "text-gray-600 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-gray-100";
    const activeLinkClass = "font-semibold bg-blue-600 text-white";

    const linkClass = (isActive: boolean) =>
        `${baseLinkClass} ${isActive ? activeLinkClass : inactiveLinkClass} flex items-center gap-3`;

    return (
        <aside className="bg-white flex flex-col flex-shrink-0 w-64 p-4 border-r border-gray-200 dark:bg-gray-800 dark:border-gray-700">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <img src="ArthSaarthi.png" alt="ArthSaarthi Logo" className="h-8 w-8" />
                    <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">ArthSaarthi</h2>
                </div>
                <button
                    onClick={toggleDarkMode}
                    className="p-2 rounded-lg bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 transition-colors"
                    title={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
                >
                    {isDarkMode ? (
                        <SunIcon className="h-5 w-5 text-yellow-500" />
                    ) : (
                        <MoonIcon className="h-5 w-5 text-gray-600" />
                    )}
                </button>
            </div>
            <nav className="flex flex-col gap-2 flex-grow">
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
                    <ListBulletIcon className="h-5 w-5" />
                    <span>Transactions</span>
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
    );
};

export default NavBar;
