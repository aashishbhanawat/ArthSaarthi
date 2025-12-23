import { useState, useEffect } from 'react';

interface SessionTimeoutModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLogout: () => void;
  countdownSeconds?: number;
}

const SessionTimeoutModal = ({ isOpen, onClose, onLogout, countdownSeconds = 120 }: SessionTimeoutModalProps) => {
  const [countdown, setCountdown] = useState(countdownSeconds);

  useEffect(() => {
    if (isOpen) {
      const timer = setInterval(() => {
        setCountdown((prevCountdown) => (prevCountdown > 0 ? prevCountdown - 1 : 0));
      }, 1000);

      return () => clearInterval(timer);
    }
  }, [isOpen]);

  useEffect(() => {
    if (countdown === 0) {
      onLogout();
    }
  }, [countdown, onLogout]);

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-8 shadow-xl">
        <h2 className="text-2xl font-bold mb-4 dark:text-gray-100">Session Timeout</h2>
        <p className="mb-4 dark:text-gray-300">You will be logged out in {countdown} seconds due to inactivity.</p>
        <div className="flex justify-end space-x-4">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-800 dark:text-gray-200 rounded hover:bg-gray-400 dark:hover:bg-gray-500"
          >
            Stay Logged In
          </button>
          <button
            onClick={onLogout}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  );
};

export default SessionTimeoutModal;
