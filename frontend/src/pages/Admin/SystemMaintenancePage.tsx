import React from 'react';
import AssetSyncCard from '../../components/Admin/AssetSyncCard';

/**
 * SystemMaintenancePage - Admin page for system maintenance operations.
 * FR2.3: Manual Asset Seeding
 */
const SystemMaintenancePage: React.FC = () => {
    return (
        <div className="container mx-auto px-4 py-6">
            <h1 className="page-title mb-6">System Maintenance</h1>

            <div className="grid gap-6 md:grid-cols-2">
                <AssetSyncCard />

                {/* Placeholder for future maintenance cards */}
                <div className="card opacity-50">
                    <div className="card-header">
                        <h3 className="card-title">Coming Soon</h3>
                    </div>
                    <div className="card-body">
                        <p className="text-gray-500">
                            More maintenance options will be available here.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SystemMaintenancePage;
