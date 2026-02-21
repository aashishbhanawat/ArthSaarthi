import React from 'react';

interface ToastProps {
  message: string;
  type: 'success' | 'error';
  onClose: () => void;
}

const Toast: React.FC<ToastProps> = ({ message, type, onClose }) => {
  // Removed fixed positioning so toasts can stack naturally in the container
  const baseClasses = 'mb-3 w-80 p-4 rounded-lg shadow-lg text-white flex justify-between items-center transition-all duration-300';
  const typeClasses = {
    success: 'bg-green-500',
    error: 'bg-red-500',
  };

  const role = type === 'error' ? 'alert' : 'status';
  const ariaLive = type === 'error' ? 'assertive' : 'polite';

  return (
    <div
      className={`${baseClasses} ${typeClasses[type]}`}
      role={role}
      aria-live={ariaLive}
    >
      <span>{message}</span>
      <button
        onClick={onClose}
        className="ml-4 font-bold focus:outline-none focus:ring-2 focus:ring-white/50 rounded"
        aria-label="Close"
      >
        &times;
      </button>
    </div>
  );
};

export default Toast;
