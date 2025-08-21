import React from 'react';

interface GoalFormModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const GoalFormModal: React.FC<GoalFormModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center">
      <div className="bg-white p-6 rounded-lg">
        <h2 className="text-2xl font-bold mb-4">Create Goal</h2>
        {/* Form fields will go here */}
        <button onClick={onClose} className="mt-4 px-4 py-2 bg-gray-300 rounded">
          Close
        </button>
      </div>
    </div>
  );
};

export default GoalFormModal;
