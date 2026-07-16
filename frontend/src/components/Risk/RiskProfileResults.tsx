import React from 'react';
import { UserRiskProfile } from '../../types/risk';
import { ArrowPathIcon, ShieldCheckIcon } from '@heroicons/react/24/outline';

interface RiskProfileResultsProps {
    profile: UserRiskProfile;
    onRetake: () => void;
}

const PROFILE_DETAILS: Record<
    string,
    { description: string; debt: string; equity: string; color: string; bg: string }
> = {
    Conservative: {
        description: 'You are prepared to accept lower returns with lower levels of risk in order to preserve your capital.',
        debt: '80%',
        equity: '20%',
        color: 'text-green-600 dark:text-green-400',
        bg: 'bg-green-50 dark:bg-green-950/20',
    },
    Moderate: {
        description: 'You would like to invest in both income and growth assets. You are comfortable with calculated risks to achieve good returns.',
        debt: '50%',
        equity: '50%',
        color: 'text-blue-600 dark:text-blue-400',
        bg: 'bg-blue-50 dark:bg-blue-950/20',
    },
    Growth: {
        description: 'You are comfortable with high volatility and high level of risk in order to achieve higher returns over the long term.',
        debt: '30%',
        equity: '70%',
        color: 'text-orange-600 dark:text-orange-400',
        bg: 'bg-orange-50 dark:bg-orange-950/20',
    },
    Aggressive: {
        description: 'You are comfortable with a higher level of risk in order to achieve potentially higher returns. Capital security is secondary.',
        debt: '10%',
        equity: '90%',
        color: 'text-red-600 dark:text-red-400',
        bg: 'bg-red-50 dark:bg-red-950/20',
    },
};

const RiskProfileResults: React.FC<RiskProfileResultsProps> = ({ profile, onRetake }) => {
    const category = profile.risk_category || 'Moderate';
    const details = PROFILE_DETAILS[category] || PROFILE_DETAILS['Moderate'];

    return (
        <div className="max-w-4xl mx-auto mt-8 space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Left Side: Assessed Profile */}
                <div className="card shadow-md flex flex-col justify-between">
                    <div>
                        <div className="flex items-center gap-3 mb-6">
                            <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-full text-blue-600 dark:text-blue-400">
                                <ShieldCheckIcon className="h-6 w-6" />
                            </div>
                            <h2 className="text-xl font-bold text-gray-900 dark:text-white">Assessed Risk Profile</h2>
                        </div>

                        <div className={`p-6 rounded-lg ${details.bg} mb-6 text-center`}>
                            <span className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider block mb-1">
                                Your Profile
                            </span>
                            <span className={`text-3xl font-extrabold ${details.color}`}>
                                {category.toUpperCase()}
                            </span>
                            <span className="text-sm text-gray-600 dark:text-gray-400 block mt-2 font-medium">
                                Score: {profile.score || 0} / 47
                            </span>
                        </div>

                        <p className="text-gray-600 dark:text-gray-300 leading-relaxed mb-6">
                            {details.description}
                        </p>
                    </div>

                    <button
                        onClick={onRetake}
                        className="btn btn-secondary flex items-center justify-center gap-2 w-full mt-4"
                    >
                        <ArrowPathIcon className="h-5 w-5" />
                        <span>Retake Questionnaire</span>
                    </button>
                </div>

                {/* Right Side: Allocation & Description */}
                <div className="card shadow-md">
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-6">
                        Indicative Asset Allocation
                    </h3>

                    {/* Simple Donut / Bar visualization */}
                    <div className="space-y-6">
                        <div>
                            <div className="flex justify-between text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                                <span>Equity (Growth)</span>
                                <span className="text-blue-600 dark:text-blue-400">{details.equity}</span>
                            </div>
                            <div className="w-full bg-gray-200 dark:bg-gray-700 h-4 rounded-full overflow-hidden">
                                <div
                                    className="bg-blue-600 dark:bg-blue-500 h-4 rounded-full transition-all duration-500"
                                    style={{ width: details.equity }}
                                ></div>
                            </div>
                        </div>

                        <div>
                            <div className="flex justify-between text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                                <span>Debt / Fixed Income (Preservation)</span>
                                <span className="text-green-600 dark:text-green-400">{details.debt}</span>
                            </div>
                            <div className="w-full bg-gray-200 dark:bg-gray-700 h-4 rounded-full overflow-hidden">
                                <div
                                    className="bg-green-600 dark:bg-green-500 h-4 rounded-full transition-all duration-500"
                                    style={{ width: details.debt }}
                                ></div>
                            </div>
                        </div>
                    </div>

                    <div className="mt-8 p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-gray-100 dark:border-gray-800">
                        <h4 className="text-sm font-bold text-gray-800 dark:text-gray-200 mb-2">What does this mean?</h4>
                        <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
                            This asset allocation serves as a general guide. In future releases, we will calculate your actual portfolio risk score and compare it with this model target to flag any mismatches on your dashboard.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default RiskProfileResults;
