import React, { useState, useEffect } from 'react';
import { useChangePassword } from '../../hooks/useProfile';

const ChangePasswordForm: React.FC = () => {
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [localError, setLocalError] = useState('');

  const { mutate: changePassword, isPending: isUpdating, isSuccess, error: apiError, reset } = useChangePassword();

  const apiErrorMessage = (apiError as { response?: { data?: { detail?: string } } })?.response?.data?.detail;

  useEffect(() => {
    // If the form is successful, clear local errors.
    if (isSuccess) {
      setLocalError('');
    }
  }, [isSuccess]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError('');
    reset(); // Reset the mutation state (isSuccess, error)

    if (newPassword !== confirmPassword) {
      setLocalError('New passwords do not match.');
      return;
    }

    changePassword({ old_password: oldPassword, new_password: newPassword }, {
      onSuccess: () => {
        setOldPassword('');
        setNewPassword('');
        setConfirmPassword('');
      }
    });
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">Change Password</h3>
      </div>
      <div className="card-body">
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div className="form-group">
              <label htmlFor="currentPassword">Current Password</label>
              <input
                id="currentPassword"
                type="password"
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
                className="form-input"
                required
                disabled={isUpdating}
              />
            </div>
            <div className="form-group">
              <label htmlFor="newPassword">New Password</label>
              <input
                id="newPassword"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="form-input"
                required
                disabled={isUpdating}
              />
            </div>
            <div className="form-group">
              <label htmlFor="confirmPassword">Confirm New Password</label>
              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="form-input"
                required
                disabled={isUpdating}
              />
            </div>
          </div>
          {(localError || apiErrorMessage) && (
            <p role="alert" className="text-red-500 text-sm mt-2">{localError || apiErrorMessage}</p>
          )}
          {isSuccess && <p role="status" className="text-green-500 text-sm mt-2">Password updated successfully!</p>}
          <div className="card-footer">
            <button type="submit" className="btn btn-primary" disabled={isUpdating}>
              {isUpdating ? 'Updating...' : 'Update Password'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChangePasswordForm;
