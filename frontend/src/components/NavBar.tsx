import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
    HomeIcon,
    BriefcaseIcon,
    ArrowUpTrayIcon,
    UsersIcon,
} from '@heroicons/react/24/outline';

const NavBar: React.FC = () => {
    const { user, logout } = useAuth();

    const baseLinkClass = "py-2 px-3 rounded-md transition-colors";
    const inactiveLinkClass = "text-gray-600 hover:bg-gray-100 hover:text-gray-900";
    const activeLinkClass = "font-semibold bg-blue-600 text-white";

    const linkClass = (isActive: boolean) =>
        `${baseLinkClass} ${isActive ? activeLinkClass : inactiveLinkClass} flex items-center gap-3`;

    return (
        <aside className="bg-white flex flex-col flex-shrink-0 w-64 p-4 border-r border-gray-200">
            <h2 className="text-xl font-bold mb-6 text-gray-800">My PMS</h2>
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
                {user?.is_admin && (
                    <NavLink to="/admin/users" className={({ isActive }) => linkClass(isActive)}>
                        <UsersIcon className="h-5 w-5" />
                        <span>User Management</span>
                    </NavLink>
                )}
            </nav>
            <div className="mt-auto pt-4 border-t">
                <div className="text-center text-sm text-gray-600 mb-2 truncate" title={user?.email}>{user?.email}</div>
                <button onClick={logout} className="btn btn-secondary w-full">
                    Logout
                </button>
            </div>
        </aside>
    );
};

export default NavBar;
