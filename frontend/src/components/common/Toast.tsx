import React from 'react';
import { CheckCircleIcon, ExclamationCircleIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface ToastProps {
  message: string;
  type: 'success' | 'error';
  onClose: () => void;
}

const Toast: React.FC<ToastProps> = ({ message, type, onClose }) => {
  const baseClasses = 'fixed top-5 right-5 p-4 rounded-lg shadow-lg text-white flex items-center gap-3 z-50';
  const typeClasses = {
    success: 'bg-green-600',
    error: 'bg-red-600',
  };

  const Icon = type === 'success' ? CheckCircleIcon : ExclamationCircleIcon;
  const role = type === 'error' ? 'alert' : 'status';

  return (
    <div
      className={`${baseClasses} ${typeClasses[type]}`}
      role={role}
      aria-live={type === 'error' ? 'assertive' : 'polite'}
    >
      <Icon className="h-6 w-6 flex-shrink-0" aria-hidden="true" />
      <span className="flex-grow font-medium">{message}</span>
      <button
        onClick={onClose}
        className="ml-2 p-1 hover:bg-white/20 rounded-full focus:outline-none focus:ring-2 focus:ring-white/50 transition-colors"
        aria-label="Close notification"
      >
        <XMarkIcon className="h-5 w-5" />
      </button>
    </div>
  );
};

export default Toast;
