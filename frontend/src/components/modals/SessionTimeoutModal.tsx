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
    <div className="modal-overlay z-50">
      <div
        className="modal-content max-w-md"
        role="dialog"
        aria-modal="true"
        aria-labelledby="session-timeout-title"
        aria-describedby="session-timeout-desc"
      >
        <div className="modal-header">
          <h2 id="session-timeout-title" className="text-2xl font-bold dark:text-gray-100">Session Timeout</h2>
        </div>
        <div className="p-6">
          <p id="session-timeout-desc" className="mb-4 text-gray-700 dark:text-gray-300">You will be logged out in {countdown} seconds due to inactivity.</p>
          <div className="flex justify-end space-x-4">
            <button
              onClick={onClose}
              className="btn btn-secondary"
            >
              Stay Logged In
            </button>
            <button
              onClick={onLogout}
              className="btn btn-danger"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SessionTimeoutModal;
