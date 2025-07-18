import { useState, useEffect, ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { getAuthStatus } from "../services/api";
import SetupForm from "../components/auth/SetupForm";
import LoginForm from "../components/LoginForm";
import { useAuth } from "../context/AuthContext";

const AuthPage = () => {
    const { token } = useAuth();
    const [setupNeeded, setSetupNeeded] = useState<boolean | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    if (token) {
        return <Navigate to="/" replace />;
    }
    useEffect(() => {
        const checkStatus = async () => {
            try {
                const data = await getAuthStatus();
                setSetupNeeded(data.setup_needed);
            } catch (err: any) {
                setError(
                    err.response?.data?.detail || "Failed to check setup status."
                );
            } finally {
                setLoading(false);
            }
        };
        checkStatus();
    }, []);

    const handleSetupSuccess = () => {
        setSetupNeeded(false); // Re-render to show the login form
    };

    if (loading) {
        return <div>Loading...</div>;
    }

    if (error) {
        return <div>Error: {error}</div>;
    }

    return (
        <div className="auth-container">
            {setupNeeded ? (
                <SetupForm onSuccess={handleSetupSuccess} />
            ) : (
                <LoginForm />
            )}
        </div>
    );
};

export default AuthPage;