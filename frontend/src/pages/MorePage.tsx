import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
    ScaleIcon,
    EyeIcon,
    TrophyIcon,
    UsersIcon,
    WrenchScrewdriverIcon,
    ListBulletIcon,
    UserCircleIcon,
    ChevronRightIcon
} from '@heroicons/react/24/outline';

const MenuItem = ({ to, icon: Icon, label }: { to: string, icon: any, label: string }) => (
    <Link to={to} className="flex items-center justify-between p-4 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors">
        <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-50 dark:bg-blue-900/30 rounded-full text-blue-600 dark:text-blue-400">
                <Icon className="h-5 w-5" />
            </div>
            <span className="font-medium text-gray-800 dark:text-gray-200">{label}</span>
        </div>
        <ChevronRightIcon className="h-5 w-5 text-gray-400" />
    </Link>
);

const MorePage: React.FC = () => {
    const { user, deploymentMode } = useAuth();

    return (
        <div className="space-y-6 pb-20 max-w-2xl mx-auto">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">More Options</h1>

            <div className="space-y-6">
                <section>
                    <h2 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3 px-1">Features</h2>
                    <div className="space-y-2">
                        <MenuItem to="/capital-gains" icon={ScaleIcon} label="Capital Gains" />
                        <MenuItem to="/watchlists" icon={EyeIcon} label="Watchlists" />
                        <MenuItem to="/goals" icon={TrophyIcon} label="Goals" />
                        <MenuItem to="/profile" icon={UserCircleIcon} label="Profile & Settings" />
                    </div>
                </section>

                {user?.is_admin && (
                    <section className="pt-2 border-t border-gray-200 dark:border-gray-700">
                        <h2 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3 mt-4 px-1">Administration</h2>
                        <div className="space-y-2">
                            {deploymentMode === 'server' && (
                                <MenuItem to="/admin/users" icon={UsersIcon} label="User Management" />
                            )}
                            <MenuItem to="/admin/interest-rates" icon={ScaleIcon} label="Interest Rates" />
                            <MenuItem to="/admin/maintenance" icon={WrenchScrewdriverIcon} label="System Maintenance" />
                            <MenuItem to="/admin/logs" icon={ListBulletIcon} label="System Logs" />
                            <MenuItem to="/admin/fmv" icon={ScaleIcon} label="FMV Management" />
                            <MenuItem to="/admin/aliases" icon={ListBulletIcon} label="Symbol Aliases" />
                        </div>
                    </section>
                )}
            </div>
        </div>
    );
};

export default MorePage;
