import React, { useState, useEffect } from 'react';
import { useUpdatePassword } from '../../hooks/useUsers';
import { UserPasswordChange } from '../../types/user';

interface PydanticError {
    loc: (string | number)[];
    msg: string;
    type: string;
}

const getApiErrorMessage = (error: unknown): string => {
    if (typeof error === 'object' && error !== null && 'response' in error) {
        const axiosError = error as { response?: { data?: { detail?: string | PydanticError[] } } };
        const detail = axiosError.response?.data?.detail;

        if (typeof detail === 'string') {
            return detail;
        }

        if (Array.isArray(detail) && detail.length > 0 && typeof detail[0] === 'object' && detail[0] !== null && 'msg' in detail[0]) {
            return detail[0].msg;
        }
    }
    return 'An unexpected error occurred. Please try again.';
};

const ChangePasswordForm: React.FC = () => {
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');

    const { mutate: updatePassword, isPending, isSuccess, error: apiError, reset } = useUpdatePassword();

    useEffect(() => {
        if (currentPassword || newPassword || confirmPassword) {
            reset();
            setError('');
        }
    }, [currentPassword, newPassword, confirmPassword, reset]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        reset();
        if (newPassword !== confirmPassword) {
            setError('New passwords do not match.');
            return;
        }
        const passwordData: UserPasswordChange = {
            old_password: currentPassword,
            new_password: newPassword
        };
        updatePassword(passwordData, {
            onSuccess: () => {
                setCurrentPassword('');
                setNewPassword('');
                setConfirmPassword('');
            },
        });
    };

    return (
        <div className="card bg-base-100 shadow-xl">
            <div className="card-body">
                <h2 className="card-title">Change Password</h2>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="form-control">
                        <label className="label" htmlFor="current-password">
                            <span className="label-text">Current Password</span>
                        </label>
                        <input
                            id="current-password"
                            type="password"
                            value={currentPassword}
                            onChange={(e) => setCurrentPassword(e.target.value)}
                            className="input input-bordered"
                            required
                        />
                    </div>
                    <div className="form-control">
                        <label className="label" htmlFor="new-password">
                            <span className="label-text">New Password</span>
                        </label>
                        <input
                            id="new-password"
                            type="password"
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            className="input input-bordered"
                            required
                        />
                    </div>
                    <div className="form-control">
                        <label className="label" htmlFor="confirm-password">
                            <span className="label-text">Confirm New Password</span>
                        </label>
                        <input
                            id="confirm-password"
                            type="password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            className="input input-bordered"
                            required
                        />
                    </div>
                    <div className="pt-2 h-10">
                        {error && <div className="alert alert-error"><span>{error}</span></div>}
                        {isSuccess && <div className="alert alert-success"><span>Password updated successfully!</span></div>}
                        {apiError && <div className="alert alert-error"><span>{getApiErrorMessage(apiError)}</span></div>}
                    </div>
                    <div className="form-control mt-6">
                        <button type="submit" className="btn btn-primary" disabled={isPending}>
                            {isPending ? 'Changing...' : 'Change Password'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default ChangePasswordForm;
