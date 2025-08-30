import React from 'react';

interface DeleteGoalModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    goalName: string;
    isPending: boolean;
}

const DeleteGoalModal: React.FC<DeleteGoalModalProps> = ({ isOpen, onClose, onConfirm, goalName, isPending }) => {
    if (!isOpen) return null;

    return (
        <div className="modal-overlay">
            <div className="modal-content max-w-md">
                <div className="modal-header">
                    <h2 className="text-2xl font-bold">Delete Goal</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600">&times;</button>
                </div>
                <div className="p-6">
                    <p className="text-gray-600 mb-4">
                        Are you sure you want to delete the goal "<strong>{goalName}</strong>"? This action cannot be undone.
                    </p>
                    <div className="flex items-center justify-end pt-4">
                        <button onClick={onClose} className="btn btn-secondary mr-2" disabled={isPending}>
                            Cancel
                        </button>
                        <button onClick={onConfirm} className="btn btn-danger" disabled={isPending}>
                            {isPending ? 'Deleting...' : 'Delete'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DeleteGoalModal;
