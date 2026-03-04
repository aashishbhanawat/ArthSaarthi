import React, { useEffect, useRef } from "react";
import { XMarkIcon, ArrowPathIcon } from "@heroicons/react/24/outline";

interface DeleteConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: React.ReactNode; // Allow for complex messages with JSX
  isDeleting: boolean;
}

export const DeleteConfirmationModal: React.FC<
  DeleteConfirmationModalProps
> = ({ isOpen, onClose, onConfirm, title, message, isDeleting }) => {
  const cancelRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (isOpen) {
      // Focus on the cancel button when the modal opens to prevent accidental deletion
      setTimeout(() => cancelRef.current?.focus(), 50);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      aria-describedby="modal-description"
      data-testid="delete-confirmation-modal"
    >
      <div className="modal-content max-w-md">
        <div className="modal-header flex justify-between items-center">
          <h2
            id="modal-title"
            className="text-2xl font-bold text-red-600 dark:text-red-400"
          >
            {title}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            disabled={isDeleting}
            aria-label="Close"
          >
            <XMarkIcon className="h-6 w-6" aria-hidden="true" />
          </button>
        </div>
        <div className="p-6">
          <div
            id="modal-description"
            className="text-gray-700 dark:text-gray-300 mb-4"
          >
            {message}
          </div>
          <p className="text-sm text-red-500 dark:text-red-400 bg-red-100 dark:bg-red-900/30 p-3 rounded-md flex items-center gap-2">
            <span role="img" aria-hidden="true">
              ⚠️
            </span>
            This action is permanent and cannot be undone.
          </p>
          <div className="flex items-center justify-end pt-6">
            <button
              ref={cancelRef}
              type="button"
              onClick={onClose}
              className="btn btn-secondary mr-2"
              disabled={isDeleting}
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={onConfirm}
              className="btn btn-danger flex items-center gap-2"
              disabled={isDeleting}
            >
              {isDeleting ? (
                <>
                  <ArrowPathIcon className="h-4 w-4 animate-spin" />
                  <span>Deleting...</span>
                </>
              ) : (
                "Confirm Delete"
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
