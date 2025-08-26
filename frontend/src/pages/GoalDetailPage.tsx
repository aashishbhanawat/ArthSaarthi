import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useGoal } from '../hooks/useGoals';
import { formatCurrency, formatDate } from '../utils/formatting';
import AssetLinkModal from '../components/modals/AssetLinkModal';

const GoalDetailPage: React.FC = () => {
    const { id: goalId } = useParams<{ id: string }>();
    const { data: goal, isLoading, isError, error } = useGoal(goalId);
    const [isLinkModalOpen, setLinkModalOpen] = useState(false);

    if (isLoading) return <div className="text-center p-8">Loading goal details...</div>;
    if (isError) return <div className="text-center p-8 text-red-500">Error: {error.message}</div>;
    if (!goal) return <div className="text-center p-8">Goal not found.</div>;

    const currentAmount = goal.current_value ?? 0;
    const progress = goal.progress ?? 0;

    return (
        <div>
            <div className="mb-8">
                <Link to="/goals" className="text-blue-600 hover:underline text-sm">
                    &larr; Back to Goals
                </Link>
                <div className="flex justify-between items-center mt-2">
                    <h1 className="text-3xl font-bold">{goal.name}</h1>
                    <button onClick={() => setLinkModalOpen(true)} className="btn btn-primary">
                        Link Asset/Portfolio
                    </button>
                </div>
                <p className="text-gray-600 mt-1">
                    Target: {formatCurrency(goal.target_amount)} by {formatDate(goal.target_date)}
                </p>
            </div>

            <div className="mt-8 bg-white shadow-md rounded-lg p-6">
                <h2 className="text-2xl font-bold mb-4">Progress</h2>
                <div className="flex justify-between items-center mb-1">
                    <span className="text-sm font-medium text-gray-700">
                        Progress ({progress.toFixed(2)}%)
                    </span>
                    <span className="text-sm font-medium text-gray-700">
                        {formatCurrency(currentAmount)} / {formatCurrency(goal.target_amount)}
                    </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-4">
                    <div
                        className="bg-blue-600 h-4 rounded-full"
                        style={{ width: `${progress}%` }}
                    ></div>
                </div>
            </div>

            <section className="mt-8 bg-white shadow-md rounded-lg p-6" aria-labelledby="linked-items-header">
                <h2 id="linked-items-header" className="text-2xl font-bold mb-4">Linked Items</h2>
                {goal.links && goal.links.length > 0 ? (
                    <ul className="space-y-2">
                        {goal.links.map(link => (
                            <li key={link.id} className="p-2 bg-gray-100 rounded">
                                {link.portfolio ? link.portfolio.name : link.asset?.name || 'Unknown'}
                            </li>
                        ))}
                    </ul>
                ) : (
                    <p className="text-gray-500">No portfolios or assets linked yet.</p>
                )}
            </section>

            <AssetLinkModal
                isOpen={isLinkModalOpen}
                onClose={() => setLinkModalOpen(false)}
                goalId={goal.id}
            />
        </div>
    );
};

export default GoalDetailPage;
