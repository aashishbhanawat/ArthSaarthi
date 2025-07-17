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
    <div className="modal-backdrop">
      <div className="modal-content">
        <h2>Confirm Deletion</h2>
        <p>
          Are you sure you want to delete the user{' '}
          <strong>{user.full_name || user.email}</strong>?
        </p>
        <p>This action cannot be undone.</p>
        <div className="modal-actions">
          <button onClick={onClose} className="button-secondary">
            Cancel
          </button>
          <button onClick={onConfirm} className="button-danger">
            Delete
          </button>
        </div>
      </div>
    </div>
  );
};

export default DeleteConfirmationModal;