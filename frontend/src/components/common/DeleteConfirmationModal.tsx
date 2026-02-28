import React from 'react';

interface DeleteConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: React.ReactNode; // Allow for complex messages with JSX
  isDeleting: boolean;
}

export const DeleteConfirmationModal: React.FC<DeleteConfirmationModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  isDeleting,
}) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" data-testid="delete-confirmation-modal">
      <div className="modal-content max-w-md">
        <div className="modal-header">
          <h2 className="text-2xl font-bold text-red-600 dark:text-red-400">{title}</h2>
          <button onClick={onClose} aria-label="Close" className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" disabled={isDeleting}>&times;</button>
        </div>
        <div className="p-6">
          <div className="text-gray-700 dark:text-gray-300 mb-4">{message}</div>
          <p className="text-sm text-red-500 dark:text-red-400 bg-red-100 dark:bg-red-900/30 p-3 rounded-md">This action is permanent and cannot be undone.</p>
          <div className="flex items-center justify-end pt-6">
            <button type="button" onClick={onClose} className="btn btn-secondary mr-2" disabled={isDeleting}>Cancel</button>
            <button type="button" onClick={onConfirm} className="btn btn-danger" disabled={isDeleting}>{isDeleting ? 'Deleting...' : 'Confirm Delete'}</button>
          </div>
        </div>
      </div>
    </div>
  );
};
