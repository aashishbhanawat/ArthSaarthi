import React from 'react';
import { useForm } from 'react-hook-form';
import { useChangePassword } from '../../hooks/useProfile';
import { UserPasswordChange } from '../../types/user';

type ChangePasswordFormData = UserPasswordChange & {
  confirmPassword?: string;
};

const passwordValidation = {
  required: 'Password is required',
  minLength: {
    value: 8,
    message: 'Password must be at least 8 characters long',
  },
  pattern: {
    value: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?:{}|<>]).{8,}$/,
    message:
      'Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character.',
  },
};

const ChangePasswordForm = () => {
  const { mutate: changePassword, isPending } = useChangePassword();
  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    reset,
  } = useForm<ChangePasswordFormData>();

  const newPassword = watch('new_password');

  const onSubmit = (data: ChangePasswordFormData) => {
    const { old_password, new_password } = data;
    changePassword({ old_password, new_password }, {
      onSuccess: () => {
        reset();
      },
    });
  };

  return (
    <div className="card mt-8">
      <div className="card-body">
        <h2 className="card-title">Change Password</h2>
        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          <div className="form-control">
            <label htmlFor="old_password" className="label">
              <span className="label-text">Current Password</span>
            </label>
            <input
              type="password"
              id="old_password"
              {...register('old_password', { required: 'Current password is required' })}
              className={`input input-bordered w-full ${errors.old_password ? 'input-error' : ''}`}
            />
            {errors.old_password && <p className="text-red-500 text-xs mt-1">{errors.old_password.message}</p>}
          </div>

          <div className="form-control mt-4">
            <label htmlFor="new_password" className="label">
              <span className="label-text">New Password</span>
            </label>
            <input
              type="password"
              id="new_password"
              {...register('new_password', passwordValidation)}
              className={`input input-bordered w-full ${errors.new_password ? 'input-error' : ''}`}
            />
            {errors.new_password && <p className="text-red-500 text-xs mt-1">{errors.new_password.message}</p>}
          </div>

          <div className="form-control mt-4">
            <label htmlFor="confirmPassword" className="label">
              <span className="label-text">Confirm New Password</span>
            </label>
            <input
              type="password"
              id="confirmPassword"
              {...register('confirmPassword', {
                required: 'Please confirm your new password',
                validate: (value) => value === newPassword || 'Passwords do not match',
              })}
              className={`input input-bordered w-full ${errors.confirmPassword ? 'input-error' : ''}`}
            />
            {errors.confirmPassword && <p className="text-red-500 text-xs mt-1">{errors.confirmPassword.message}</p>}
          </div>

          <div className="flex items-center justify-end mt-6">
            <button type="submit" className="btn btn-primary" disabled={isPending}>
              {isPending ? 'Updating...' : 'Update Password'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChangePasswordForm;
