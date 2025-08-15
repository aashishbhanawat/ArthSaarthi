import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { HomeIcon,
  BriefcaseIcon,
  ArrowUpTrayIcon,
  UsersIcon,
  ArrowLeftOnRectangleIcon,
 } from '@heroicons/react/24/outline';

const appVersion = import.meta.env.VITE_APP_VERSION;


const NavBar: React.FC = () => {
    const { user, logout, deploymentMode } = useAuth();

    const baseLinkClass = "py-2 px-3 rounded-md transition-colors";
    const inactiveLinkClass = "text-gray-600 hover:bg-gray-100 hover:text-gray-900";
    const activeLinkClass = "font-semibold bg-blue-600 text-white";

    const linkClass = (isActive: boolean) =>
        `${baseLinkClass} ${isActive ? activeLinkClass : inactiveLinkClass} flex items-center gap-3`;

    return (
        <aside className="bg-white flex flex-col flex-shrink-0 w-64 p-4 border-r border-gray-200">
            <div className="flex items-center gap-3 mb-6">
                <img src="/ArthSaarthi.png" alt="ArthSaarthi Logo" className="h-8 w-8" />
                <h2 className="text-xl font-bold text-gray-800">ArthSaarthi</h2>
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
                <NavLink to="/import" className={({ isActive }) => linkClass(isActive)}>
                    <ArrowUpTrayIcon className="h-5 w-5" /> <span>Import</span>
                </NavLink>
                {user?.is_admin && deploymentMode === 'multi_user' && (
                    <NavLink to="/admin/users" className={({ isActive }) => linkClass(isActive)}>
                        <UsersIcon className="h-5 w-5" />
                        <span>User Management</span>
                    </NavLink>
                )}
            </nav>
            <div className="mt-auto pt-4 border-t">
                <div className="text-center text-sm text-gray-600 mb-2 truncate" title={user?.email}>{user?.email}</div>
                <button
                    onClick={logout}
                    className="btn btn-secondary w-full flex items-center justify-center"
                >
                    <ArrowLeftOnRectangleIcon className="h-5 w-5 mr-2" />
                    <span>Logout</span>
                </button>
                <div className="text-center text-xs text-gray-500 mt-4">
                    Version: {appVersion}
                </div>
            </div>
        </aside>
    );
};

export default NavBar;
