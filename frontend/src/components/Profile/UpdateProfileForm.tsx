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
        <h2 className="card-title">Update Profile Information</h2>
        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          <div className="form-control">
            <label htmlFor="fullName" className="label">
              <span className="label-text">Full Name</span>
            </label>
            <input
              type="text"
              id="fullName"
              {...register('full_name', {
                required: 'Full name is required',
              })}
              className={`input input-bordered w-full ${errors.full_name ? 'input-error' : ''}`}
            />
            {errors.full_name && <p className="text-red-500 text-xs mt-1">{errors.full_name.message}</p>}
          </div>

          <div className="form-control mt-4">
            <label htmlFor="email" className="label">
              <span className="label-text">Email</span>
            </label>
            <input
              type="email"
              id="email"
              value={user?.email || ''}
              className="input input-bordered w-full bg-gray-100"
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
