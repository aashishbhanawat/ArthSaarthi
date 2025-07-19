import React from 'react';
import { User } from '../../types/user';

interface DeleteConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  user: User | null;
}

const DeleteConfirmationModal: React.FC<DeleteConfirmationModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  user,
}) => {
  if (!isOpen || !user) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content max-w-md">
        <div className="modal-header">
          <h2 className="text-2xl font-bold text-red-600">Delete User</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">&times;</button>
        </div>
        <div className="p-6">
          <p className="text-gray-700 mb-4">
            Are you sure you want to delete the user "<strong>{user.email}</strong>"?
          </p>
          <p className="text-sm text-red-500 bg-red-100 p-3 rounded-md">
            This action is permanent and cannot be undone.
          </p>
          <div className="flex items-center justify-end pt-6">
            <button type="button" onClick={onClose} className="btn btn-secondary mr-2">
              Cancel
            </button>
            <button type="button" onClick={onConfirm} className="btn btn-danger">
              Confirm Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeleteConfirmationModal;