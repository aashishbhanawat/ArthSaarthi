import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useUpdateMe } from '../../hooks/useUsers';

const UpdateProfileForm: React.FC = () => {
  const { user } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || '');
  const { mutate: updateMe, isPending } = useUpdateMe();

  useEffect(() => {
    if (user?.full_name) {
      setFullName(user.full_name);
    }
  }, [user]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMe({ full_name: fullName });
  };

  return (
    <div className="card bg-white">
      <div className="card-body">
        <h2 className="card-title">Update Profile</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-control">
            <label className="label" htmlFor="full-name">
              <span className="label-text">Full Name</span>
            </label>
            <input
              id="full-name"
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="input input-bordered"
            />
          </div>
          <div className="form-control mt-6">
            <button type="submit" className="btn btn-primary" disabled={isPending}>
              {isPending ? 'Saving...' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default UpdateProfileForm;
