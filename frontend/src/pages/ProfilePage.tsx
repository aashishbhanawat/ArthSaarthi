import React from 'react';
import { useSearchParams } from 'react-router-dom';
import UpdateProfileForm from '../components/Profile/UpdateProfileForm';
import ChangePasswordForm from '../components/Profile/ChangePasswordForm';
import BackupRestoreCard from '../components/Profile/BackupRestoreCard';
import AndroidSettingsCard from '../components/Profile/AndroidSettingsCard';
import { BrokerSettings } from '../components/settings/BrokerSettings';
import RiskProfileTab from '../components/Profile/RiskProfileTab';
import AIIntelligenceTab from '../components/Profile/AIIntelligenceTab';
import {
  UserCircleIcon,
  ShieldCheckIcon,
  ArrowsRightLeftIcon,
  CircleStackIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';

type ProfileTab = 'account' | 'risk' | 'brokers' | 'data' | 'ai';

interface TabItem {
  id: ProfileTab;
  label: string;
  icon: React.ElementType;
  badge?: string;
}

const TABS: TabItem[] = [
  { id: 'account', label: 'Account & Security', icon: UserCircleIcon },
  { id: 'risk', label: 'Risk Profile', icon: ShieldCheckIcon },
  { id: 'brokers', label: 'Broker Integrations', icon: ArrowsRightLeftIcon },
  { id: 'data', label: 'Data & System', icon: CircleStackIcon },
  { id: 'ai', label: 'AI & Intelligence', icon: SparklesIcon, badge: 'Coming Soon' },
];

const ProfilePage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const currentTab = (searchParams.get('tab') as ProfileTab) || 'account';

  const handleTabChange = (tabId: ProfileTab) => {
    setSearchParams({ tab: tabId });
  };

  return (
    <div className="w-full max-w-6xl mx-auto px-4 py-6 space-y-6">
      {/* Page Header */}
      <div className="border-b border-gray-200 dark:border-gray-700 pb-4">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Profile & Settings</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Manage your personal details, investment risk profile, broker APIs, and platform configurations.
        </p>
      </div>

      {/* Tabs Header Navigation */}
      <div className="flex border-b border-gray-200 dark:border-gray-700 overflow-x-auto no-scrollbar gap-2 sm:gap-4">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = currentTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id)}
              className={`flex items-center gap-2 py-3 px-3 sm:px-4 text-sm font-medium border-b-2 whitespace-nowrap transition-colors ${
                isActive
                  ? 'border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-200'
              }`}
            >
              <Icon className="h-5 w-5" />
              <span>{tab.label}</span>
              {tab.badge && (
                <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded-full bg-purple-100 text-purple-700 dark:bg-purple-900/50 dark:text-purple-300">
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab Panes */}
      <div className="mt-4">
        {currentTab === 'account' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
            <UpdateProfileForm />
            <ChangePasswordForm />
          </div>
        )}

        {currentTab === 'risk' && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <RiskProfileTab />
          </div>
        )}

        {currentTab === 'brokers' && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <BrokerSettings />
          </div>
        )}

        {currentTab === 'data' && (
          <div className="space-y-6">
            <BackupRestoreCard />
            <AndroidSettingsCard />
          </div>
        )}

        {currentTab === 'ai' && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <AIIntelligenceTab />
          </div>
        )}
      </div>
    </div>
  );
};

export default ProfilePage;
