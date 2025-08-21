import React from 'react';
import { Goal } from '../../types/goal';
import { useQuery } from '@tanstack/react-query';
import * as goalApi from '../../services/goalApi';

interface GoalDetailViewProps {
  goal: Goal;
}

const GoalDetailView: React.FC<GoalDetailViewProps> = ({ goal }) => {
  const { data: progress, isLoading } = useQuery({
    queryKey: ['goalProgress', goal.id],
    queryFn: () => goalApi.getGoalProgress(goal.id),
  });

  if (isLoading) return <div>Loading progress...</div>;

  return (
    <div className="mt-4 p-4 bg-gray-100 rounded-lg">
      <h3 className="text-lg font-bold">Goal Progress</h3>
      {progress && (
        <div>
          <p>
            Current Value: ${progress.current_value.toFixed(2)} / ${progress.target_amount.toFixed(2)}
          </p>
          <div className="w-full bg-gray-200 rounded-full h-4">
            <div
              className="bg-blue-500 h-4 rounded-full"
              style={{ width: `${progress.progress_percentage}%` }}
            ></div>
          </div>
          <p>{progress.progress_percentage.toFixed(2)}% Complete</p>
        </div>
      )}
    </div>
  );
};

export default GoalDetailView;
