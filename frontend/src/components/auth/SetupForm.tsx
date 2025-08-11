import React, { useState } from 'react';
import * as api from '../../services/api';

interface SetupFormProps {
    onSuccess: () => void;
}

const SetupForm: React.FC<SetupFormProps> = ({ onSuccess }) => {
    const [fullName, setFullName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setIsLoading(true);

        try {
            await api.setupAdminUser(fullName, email, password);
            onSuccess();
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        } catch (err: any) {
            if (err.response?.data?.detail) {
                // Handle validation errors which might be an array
                if (Array.isArray(err.response.data.detail)) {
                    setError(err.response.data.detail[0].msg);
                } else {
                    setError(err.response.data.detail);
                }
            } else {
                setError('An unexpected error occurred during setup.');
            }
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div>
            <h2 className="text-center text-3xl font-extrabold text-gray-900 mb-6">
                Initial Setup
            </h2>
            <p className="text-center text-sm text-gray-600 mb-6">
                Create the first administrator account.
            </p>
            <form onSubmit={handleSubmit} className="space-y-6">
                <div className="form-group">
                    <label htmlFor="full_name" className="form-label">Full Name</label>
                    <input
                        id="full_name" type="text" required value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        className="form-input"
                        disabled={isLoading}
                    />
                </div>
                <div className="form-group">
                    <label htmlFor="email" className="form-label">Email address</label>
                    <input
                        id="email" type="email" autoComplete="email" required value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="form-input"
                        disabled={isLoading}
                    />
                </div>
                <div className="form-group">
                    <label htmlFor="password" className="form-label">Password</label>
                    <input
                        id="password" type="password" autoComplete="new-password" required value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="form-input"
                        disabled={isLoading}
                    />
                </div>

                {error && (
                    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded" role="alert">
                        <p>{error}</p>
                    </div>
                )}

                <div>
                    <button type="submit" className="w-full flex justify-center btn btn-primary" disabled={isLoading}>
                        {isLoading ? 'Creating Account...' : 'Create Admin Account'}
                    </button>
                </div>
            </form>
        </div>
    );
};

export default SetupForm;