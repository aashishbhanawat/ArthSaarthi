import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useAuth } from '../../context/AuthContext';
import { useUpdateProfile } from '../../hooks/useProfile';
import { UserUpdateMe } from '../../types/user';

const UpdateProfileForm = () => {
  const { user } = useAuth();
  const { mutate: updateProfile, isPending } = useUpdateProfile();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<UserUpdateMe>({
    defaultValues: {
      full_name: user?.full_name || '',
    },
  });

  useEffect(() => {
    reset({ full_name: user?.full_name || '' });
  }, [user, reset]);

  const onSubmit = (data: UserUpdateMe) => {
    updateProfile(data);
  };

  return (
    <div className="card">
      <div className="card-body">
        <h2 className="text-2xl font-bold mb-4">Update Profile Information</h2>
        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          <div className="form-group">
            <label htmlFor="fullName" className="form-label">
              Full Name
            </label>
            <input
              type="text"
              id="fullName"
              {...register('full_name', {
                required: 'Full name is required',
              })}
              className={`form-input font-bold ${errors.full_name ? 'border-red-500' : ''}`}
            />
            {errors.full_name && <p className="text-red-500 text-xs italic mt-1">{errors.full_name.message}</p>}
          </div>

          <div className="form-group">
            <label htmlFor="email" className="form-label">
              Email
            </label>
            <input
              type="email"
              id="email"
              value={user?.email || ''}
              className="form-input bg-gray-100"
              readOnly
              disabled
            />
          </div>

          <div className="flex items-center justify-end mt-6">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isPending || !isDirty}
            >
              {isPending ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default UpdateProfileForm;
