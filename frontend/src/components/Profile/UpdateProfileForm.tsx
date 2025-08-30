import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useUpdateProfile } from '../../hooks/useProfile';

const UpdateProfileForm: React.FC = () => {
  const { user } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || '');
  const { mutate: updateProfile, isPending: isUpdating } = useUpdateProfile();

  useEffect(() => {
    if (user?.full_name) {
      setFullName(user.full_name);
    }
  }, [user]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateProfile({ full_name: fullName });
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">Update Profile Information</h3>
      </div>
      <div className="card-body">
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div className="form-group">
              <label htmlFor="fullName" className="form-label">
                Full Name
              </label>
              <input
                id="fullName"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="form-input"
                disabled={isUpdating}
              />
            </div>
            <div className="form-group">
              <label htmlFor="email" className="form-label">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={user?.email || ''}
                className="form-input bg-gray-100"
                disabled
              />
            </div>
          </div>
          <div className="card-footer">
            <button type="submit" className="btn btn-primary" disabled={isUpdating}>
              {isUpdating ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default UpdateProfileForm;
