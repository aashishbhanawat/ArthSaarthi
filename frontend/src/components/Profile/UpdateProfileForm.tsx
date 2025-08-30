import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useUpdateMe } from '../../hooks/useUsers';

const UpdateProfileForm: React.FC = () => {
  const { user } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || '');
  const { mutate: updateMe, isPending, isSuccess, reset } = useUpdateMe();

  useEffect(() => {
    if (user?.full_name) {
      setFullName(user.full_name);
    }
  }, [user]);

  useEffect(() => {
    // If user starts typing again, clear the success message
    if (isSuccess && fullName !== user?.full_name) {
      reset();
    }
  }, [fullName, user?.full_name, isSuccess, reset]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (fullName === user?.full_name) {
        // Don't submit if the name hasn't changed
        return;
    }
    updateMe({ full_name: fullName });
  };

  return (
    <div className="card bg-white">
      <div className="card-body">
        <h2 className="card-title">Update Profile</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
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

          <div className="pt-2 h-10">
            {isSuccess && (
                <div className="alert alert-success">
                    <span>Profile updated successfully!</span>
                </div>
            )}
          </div>

          <div className="form-control mt-6">
            <button type="submit" className="btn btn-primary" disabled={isPending || fullName === user?.full_name}>
              {isPending ? 'Saving...' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default UpdateProfileForm;
