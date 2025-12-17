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
        <h2 className="text-2xl font-bold mb-4">Change Password</h2>
        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          <div className="form-group">
            <label htmlFor="old_password" className="form-label">
              Current Password
            </label>
            <input
              type="password"
              id="old_password"
              autoComplete="current-password"
              {...register('old_password', { required: 'Current password is required' })}
              className={`form-input font-bold ${errors.old_password ? 'border-red-500' : ''}`}
            />
            {errors.old_password && <p className="text-red-500 text-xs italic mt-1">{errors.old_password.message}</p>}
          </div>

          <div className="form-group">
            <label htmlFor="new_password" className="form-label">
              New Password
            </label>
            <input
              type="password"
              id="new_password"
              autoComplete="new-password"
              {...register('new_password', passwordValidation)}
              className={`form-input font-bold ${errors.new_password ? 'border-red-500' : ''}`}
            />
            {errors.new_password && <p className="text-red-500 text-xs italic mt-1">{errors.new_password.message}</p>}
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword" className="form-label">
              Confirm New Password
            </label>
            <input
              type="password"
              id="confirmPassword"
              autoComplete="new-password"
              {...register('confirmPassword', {
                required: 'Please confirm your new password',
                validate: (value) => value === newPassword || 'Passwords do not match',
              })}
              className={`form-input font-bold ${errors.confirmPassword ? 'border-red-500' : ''}`}
            />
            {errors.confirmPassword && <p className="text-red-500 text-xs italic mt-1">{errors.confirmPassword.message}</p>}
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
