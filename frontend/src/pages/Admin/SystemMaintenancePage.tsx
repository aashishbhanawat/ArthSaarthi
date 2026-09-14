import React from 'react';
import AssetSyncCard from '../../components/Admin/AssetSyncCard';
import { CacheDiagnostics } from '../../components/Admin/CacheDiagnostics';

/**
 * SystemMaintenancePage - Admin page for system maintenance operations.
 * FR2.3: Manual Asset Seeding & NFR13: Cache Diagnostics
 */
const SystemMaintenancePage: React.FC = () => {
    return (
        <div className="container mx-auto px-4 py-6">
            <h1 className="page-title mb-6">System Maintenance</h1>

            <div className="grid gap-6 md:grid-cols-1">
                <AssetSyncCard />
                <CacheDiagnostics />
            </div>
        </div>
    );
};

export default SystemMaintenancePage;
