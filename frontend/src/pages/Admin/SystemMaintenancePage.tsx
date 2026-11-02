import React from 'react';
import AssetSyncCard from '../../components/Admin/AssetSyncCard';
import { CacheDiagnostics } from '../../components/Admin/CacheDiagnostics';
import { SchedulerDashboard } from '../../components/Admin/SchedulerDashboard';

/**
 * SystemMaintenancePage - Admin page for system maintenance operations.
 * FR2.3: Manual Asset Seeding & NFR13: Cache Diagnostics & FR17: Background Job Scheduler
 */
const SystemMaintenancePage: React.FC = () => {
    return (
        <div className="container mx-auto px-4 py-6">
            <h1 className="page-title mb-6">System Maintenance</h1>

            <div className="grid gap-6 md:grid-cols-1">
                <AssetSyncCard />
                <CacheDiagnostics />
                <SchedulerDashboard />
            </div>
        </div>
    );
};

export default SystemMaintenancePage;
