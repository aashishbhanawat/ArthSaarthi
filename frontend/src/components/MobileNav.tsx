import React from 'react';
import { NavLink } from 'react-router-dom';
import {
    HomeIcon,
    BriefcaseIcon,
    ListBulletIcon,
    ArrowUpTrayIcon,
    EllipsisHorizontalIcon
} from '@heroicons/react/24/outline';

const MobileNav: React.FC = () => {
    const baseLinkClass = "flex flex-col items-center justify-center p-2 rounded-lg transition-all duration-300 transform active:scale-95";
    const inactiveLinkClass = "text-gray-500 hover:text-blue-500 dark:text-gray-400 dark:hover:text-blue-400";
    const activeLinkClass = "text-blue-600 bg-blue-50/50 dark:text-blue-400 dark:bg-blue-900/40";

    const linkClass = (isActive: boolean) =>
        `${baseLinkClass} ${isActive ? activeLinkClass : inactiveLinkClass}`;

    return (
        <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-white/95 dark:bg-gray-800/95 border-t border-gray-200 dark:border-gray-700 backdrop-blur-md px-4 py-2 pb-safe shadow-[0_-4px_10px_0_rgba(0,0,0,0.05)]">
            <div className="flex items-center justify-between gap-1">
                <NavLink to="/dashboard" className={({ isActive }) => linkClass(isActive)}>
                    <HomeIcon className="h-6 w-6" />
                    <span className="text-[10px] mt-1 font-medium">Home</span>
                </NavLink>

                <NavLink to="/portfolios" className={({ isActive }) => linkClass(isActive)}>
                    <BriefcaseIcon className="h-6 w-6" />
                    <span className="text-[10px] mt-1 font-medium">Portfolios</span>
                </NavLink>

                <NavLink to="/transactions" className={({ isActive }) => linkClass(isActive)}>
                    <ListBulletIcon className="h-6 w-6" />
                    <span className="text-[10px] mt-1 font-medium">History</span>
                </NavLink>

                <NavLink to="/import" className={({ isActive }) => linkClass(isActive)}>
                    <ArrowUpTrayIcon className="h-6 w-6" />
                    <span className="text-[10px] mt-1 font-medium">Import</span>
                </NavLink>

                <NavLink to="/more" className={({ isActive }) => linkClass(isActive)}>
                    <EllipsisHorizontalIcon className="h-6 w-6" />
                    <span className="text-[10px] mt-1 font-medium">More</span>
                </NavLink>
            </div>
        </nav>
    );
};

export default MobileNav;
