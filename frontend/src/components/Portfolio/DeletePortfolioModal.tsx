import React from 'react';

interface DeletePortfolioModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    portfolioName: string;
    isPending: boolean;
}

const DeletePortfolioModal: React.FC<DeletePortfolioModalProps> = ({ isOpen, onClose, onConfirm, portfolioName, isPending }) => {
    if (!isOpen) return null;

    return (
        <div className="modal-overlay">
            <div className="modal-content max-w-md" role="dialog" aria-modal="true" aria-labelledby="delete-modal-title">
                <div className="modal-header">
                    <h2 id="delete-modal-title" className="text-2xl font-bold text-red-600 dark:text-red-400">Delete Portfolio</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">&times;</button>
                </div>
                <div className="p-6">
                    <p className="text-gray-700 dark:text-gray-300 mb-4">
                        Are you sure you want to delete the portfolio "<strong>{portfolioName}</strong>"?
                    </p>
                    <p className="text-sm text-red-500 dark:text-red-400 bg-red-100 dark:bg-red-900/30 p-3 rounded-md">
                        This action cannot be undone. All associated transactions will be permanently deleted.
                    </p>
                    <div className="flex items-center justify-end pt-6">
                        <button type="button" onClick={onClose} className="btn btn-secondary mr-2" disabled={isPending}>
                            Cancel
                        </button>
                        <button type="button" onClick={onConfirm} className="btn btn-danger" disabled={isPending}>
                            {isPending ? 'Deleting...' : 'Delete'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DeletePortfolioModal;