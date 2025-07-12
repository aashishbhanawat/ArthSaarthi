import { useState, useEffect } from 'react';
import api from '../services/api';
import LoginForm from '../components/auth/LoginForm';
import SetupForm from '../components/auth/SetupForm';
import AuthLayout from '../components/auth/AuthLayout';

export default function AuthPage() {
  const [isSetupComplete, setIsSetupComplete] = useState<boolean | null>(null);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const response = await api.get('/auth/status');
        setIsSetupComplete(response.data.setup_complete);
      } catch (error) {
        console.error('Failed to check setup status:', error);
        // Assume setup is not complete if status check fails
        setIsSetupComplete(false);
      }
    };
    checkStatus();
  }, []);

  // Callback to refresh status after setup is complete
  const handleSetupSuccess = () => setIsSetupComplete(true);

  if (isSetupComplete === null) {
    return <AuthLayout><div>Loading...</div></AuthLayout>;
  }

  return <AuthLayout>{isSetupComplete ? <LoginForm /> : <SetupForm onSuccess={handleSetupSuccess} />}</AuthLayout>;
}