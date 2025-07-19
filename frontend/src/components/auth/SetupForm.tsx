import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';

interface SetupFormProps {
    onSuccess: () => void;
}

const SetupForm: React.FC<SetupFormProps> = ({ onSuccess }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const { register, isLoading, error } = useAuth();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            // We assume the register function throws on failure
            await register(email, password);
            onSuccess();
        } catch (err) {
            // Error is handled by the useAuth hook's state
            console.error("Registration failed");
        }
    };

    return (
        <div>
            <h2 className="text-center text-3xl font-extrabold text-gray-900 mb-2">
                Create Admin Account
            </h2>
            <p className="text-center text-sm text-gray-600 mb-6">
                No admin user found. Please create one to continue.
            </p>
            <form onSubmit={handleSubmit} className="space-y-6">
                <div className="form-group">
                    <label htmlFor="email" className="form-label">
                        Admin Email
                    </label>
                    <input
                        id="email"
                        name="email"
                        type="email"
                        autoComplete="email"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="form-input"
                        disabled={isLoading}
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="password" className="form-label">
                        Password
                    </label>
                    <input
                        id="password"
                        name="password"
                        type="password"
                        autoComplete="new-password"
                        required
                        value={password}
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
                    <button type="submit" className="w-full flex justify-center btn btn-primary" disabled={isLoading} >
                        {isLoading ? 'Creating...' : 'Create Admin'}
                    </button>
                </div>
            </form>
        </div>
    );
};

export default SetupForm;