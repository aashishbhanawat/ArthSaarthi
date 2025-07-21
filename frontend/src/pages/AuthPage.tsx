import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import LoginForm from '../components/auth/LoginForm';
import SetupForm from '../components/auth/SetupForm';
import * as api from '../services/api';
import { useAuth } from '../context/AuthContext';

const AuthPage: React.FC = () => {
    const { token } = useAuth();
    const navigate = useNavigate();
    const [setupNeeded, setSetupNeeded] = useState<boolean | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        // If the user is already logged in, redirect them away from the auth page.
        if (token) {
            navigate('/dashboard', { replace: true });
        }
    }, [token, navigate]);

    const checkStatus = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        try {
            const status = await api.getAuthStatus();
            setSetupNeeded(status.setup_needed);
        } catch (err) {
            setError('Failed to check setup status.');
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        checkStatus();
    }, [checkStatus]);

    const handleSetupSuccess = () => {
        // After setup, we know we no longer need it, so just switch to the login form.
        setSetupNeeded(false);
    };

    const renderContent = () => {
        if (isLoading) {
            return <p className="text-center">Loading...</p>;
        }
        if (error) {
            return <p className="text-center text-red-500">{error}</p>;
        }
        if (setupNeeded) {
            return <SetupForm onSuccess={handleSetupSuccess} />;
        }
        return <LoginForm />;
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
            <div className="sm:mx-auto sm:w-full sm:max-w-md card">{renderContent()}</div>
        </div>
    );
};

export default AuthPage;