import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Menu, Transition } from '@headlessui/react';
import { NavLink as RouterNavLink } from 'react-router-dom';
import {
  HomeIcon,
  BriefcaseIcon,
  ArrowUpTrayIcon,
  ListBulletIcon,
  UsersIcon,
  ArrowLeftOnRectangleIcon,
  EyeIcon,
  UserCircleIcon,
  Cog8ToothIcon,
  ChevronUpIcon,
} from '@heroicons/react/24/outline';
import { Fragment } from 'react';

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
                <img src="ArthSaarthi.png" alt="ArthSaarthi Logo" className="h-8 w-8" />
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
                {user?.is_admin && deploymentMode === 'server' && (
                    <NavLink to="/admin/users" className={({ isActive }) => linkClass(isActive)}>
                        <UsersIcon className="h-5 w-5" />
                        <span>User Management</span>
                    </NavLink>
                )}
            </nav>
            <div className="mt-auto pt-4 border-t border-gray-200">
                <Menu as="div" className="relative">
                    <Menu.Button className="w-full text-left">
                        {({ open }) => (
                            <div className="btn btn-ghost w-full flex items-center justify-between text-left px-2">
                                <div className="flex items-center">
                                    <UserCircleIcon className="h-8 w-8 text-gray-400" />
                                    <div className="flex-grow ml-2 text-left">
                                        <p className="text-sm font-semibold text-gray-800 truncate">{user?.full_name || 'User'}</p>
                                        <p className="text-xs text-gray-500 truncate" title={user?.email}>{user?.email}</p>
                                    </div>
                                </div>
                                <ChevronUpIcon className={`h-5 w-5 text-gray-500 transition-transform ${open ? 'rotate-180' : ''}`} />
                            </div>
                        )}
                    </Menu.Button>
                    <Transition
                        as={Fragment}
                        enter="transition ease-out duration-100"
                        enterFrom="transform opacity-0 scale-95"
                        enterTo="transform opacity-100 scale-100"
                        leave="transition ease-in duration-75"
                        leaveFrom="transform opacity-100 scale-100"
                        leaveTo="transform opacity-0 scale-95"
                    >
                        <Menu.Items className="absolute bottom-full mb-2 w-full origin-bottom-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-10">
                            <div className="py-1">
                                <Menu.Item>
                                    {({ active }) => (
                                        <RouterNavLink
                                            to="/profile"
                                            className={`${
                                                active ? 'bg-gray-100 text-gray-900' : 'text-gray-700'
                                            } group flex w-full items-center rounded-md px-4 py-2 text-sm`}
                                        >
                                            <Cog8ToothIcon className="mr-3 h-5 w-5 text-gray-400 group-hover:text-gray-500" />
                                            Profile Settings
                                        </RouterNavLink>
                                    )}
                                </Menu.Item>
                                <Menu.Item>
                                    {({ active }) => (
                                        <button
                                            onClick={logout}
                                            className={`${
                                                active ? 'bg-gray-100 text-gray-900' : 'text-gray-700'
                                            } group flex w-full items-center rounded-md px-4 py-2 text-sm`}
                                        >
                                            <ArrowLeftOnRectangleIcon className="mr-3 h-5 w-5 text-gray-400 group-hover:text-gray-500" />
                                            Logout
                                        </button>
                                    )}
                                </Menu.Item>
                            </div>
                        </Menu.Items>
                    </Transition>
                </Menu>
                <div className="text-center text-xs text-gray-500 mt-4">
                    Version: {appVersion}
                </div>
            </div>
        </aside>
    );
};

export default NavBar;
