import React from 'react';
import { ArrowPathIcon } from '@heroicons/react/24/outline';

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
            <div
                className="modal-content max-w-md"
                role="dialog"
                aria-modal="true"
                aria-labelledby="delete-goal-modal-title"
                aria-describedby="delete-goal-modal-desc"
            >
                <div className="modal-header">
                    <h2 id="delete-goal-modal-title" className="text-2xl font-bold">Delete Goal</h2>
                    <button type="button" aria-label="Close" onClick={onClose} className="text-gray-400 hover:text-gray-600">&times;</button>
                </div>
                <div className="p-6">
                    <p id="delete-goal-modal-desc" className="text-gray-600 mb-4">
                        Are you sure you want to delete the goal "<strong>{goalName}</strong>"? This action cannot be undone.
                    </p>
                    <div className="flex items-center justify-end pt-4">
                        <button type="button" onClick={onClose} className="btn btn-secondary mr-2" disabled={isPending}>
                            Cancel
                        </button>
                        <button type="button" onClick={onConfirm} className="btn btn-danger flex items-center gap-2" disabled={isPending}>
                            {isPending ? (
                                <>
                                    <ArrowPathIcon className="h-4 w-4 animate-spin" />
                                    <span>Deleting...</span>
                                </>
                            ) : (
                                'Delete'
                            )}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DeleteGoalModal;
