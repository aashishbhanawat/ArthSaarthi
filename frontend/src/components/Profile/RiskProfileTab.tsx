import React, { useState } from 'react';
import { AxiosError } from 'axios';
import { useRiskProfile, useSaveRiskProfile } from '../../hooks/useRisk';
import RiskQuestionnaireWizard from '../Risk/RiskQuestionnaireWizard';
import RiskProfileResults from '../Risk/RiskProfileResults';
import { ShieldCheckIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

export const RiskProfileTab: React.FC = () => {
    const { data: profile, isLoading, error } = useRiskProfile();
    const saveProfile = useSaveRiskProfile();
    const [forceWizard, setForceWizard] = useState(false);

    const handleSubmit = (answersData: { answers: Record<string, string> }) => {
        saveProfile.mutate(answersData, {
            onSuccess: () => {
                localStorage.removeItem('risk_wizard_step');
                localStorage.removeItem('risk_wizard_answers');
                setForceWizard(false);
            },
        });
    };

    if (isLoading) {
        return (
            <div className="flex justify-center items-center min-h-[250px]">
                <div className="text-gray-600 dark:text-gray-400 font-semibold animate-pulse flex items-center gap-2">
                    <ArrowPathIcon className="h-5 w-5 animate-spin" />
                    Loading risk profile...
                </div>
            </div>
        );
    }

    const isNotFoundError = error && (error as AxiosError).response?.status === 404;
    const hasProfile = !!profile && !isNotFoundError;

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4 border-b border-gray-200 dark:border-gray-700 gap-2">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                        <ShieldCheckIcon className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                        Risk Tolerance Profile
                    </h2>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                        Assess your risk tolerance to guide strategic asset allocation between equity, debt, and cash.
                    </p>
                </div>
                {hasProfile && forceWizard && (
                    <button
                        onClick={() => setForceWizard(false)}
                        className="btn btn-secondary text-sm self-start sm:self-auto"
                    >
                        Cancel Retake
                    </button>
                )}
            </div>

            {hasProfile && !forceWizard ? (
                <div className="w-full">
                    <RiskProfileResults
                        profile={profile!}
                        onRetake={() => {
                            localStorage.removeItem('risk_wizard_step');
                            localStorage.removeItem('risk_wizard_answers');
                            setForceWizard(true);
                        }}
                    />
                </div>
            ) : (
                <div className="w-full">
                    <RiskQuestionnaireWizard
                        onSubmit={handleSubmit}
                        isSubmitting={saveProfile.isPending}
                    />
                </div>
            )}
        </div>
    );
};

export default RiskProfileTab;
