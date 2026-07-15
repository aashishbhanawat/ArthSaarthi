import React, { useState } from 'react';
import { useRiskProfile, useSaveRiskProfile } from '../hooks/useRisk';
import RiskQuestionnaireWizard from '../components/Risk/RiskQuestionnaireWizard';
import RiskProfileResults from '../components/Risk/RiskProfileResults';

const RiskProfilePage: React.FC = () => {
    const { data: profile, isLoading, error } = useRiskProfile();
    const saveProfile = useSaveRiskProfile();
    const [forceWizard, setForceWizard] = useState(false);

    const handleSubmit = (answersData: { answers: Record<string, string> }) => {
        saveProfile.mutate(answersData, {
            onSuccess: () => {
                setForceWizard(false);
            },
        });
    };

    if (isLoading) {
        return (
            <div className="flex justify-center items-center min-h-[300px]">
                <div className="text-gray-600 dark:text-gray-400 font-semibold animate-pulse">
                    Loading risk profile...
                </div>
            </div>
        );
    }

    // Check if error is not a 404 (404 means user hasn't filled it yet, which is expected)
    const isNotFoundError = error && (error as any).response?.status === 404;
    const hasProfile = !!profile && !isNotFoundError;

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Risk Profiling</h1>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                        Assess your risk tolerance to align your investments.
                    </p>
                </div>
            </div>

            {hasProfile && !forceWizard ? (
                <RiskProfileResults
                    profile={profile!}
                    onRetake={() => setForceWizard(true)}
                />
            ) : (
                <RiskQuestionnaireWizard
                    onSubmit={handleSubmit}
                    isSubmitting={saveProfile.isPending}
                />
            )}
        </div>
    );
};

export default RiskProfilePage;
