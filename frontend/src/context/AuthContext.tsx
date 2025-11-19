import { createContext, useState, useContext, useEffect, ReactNode, useCallback } from 'react';
import api from '../services/api';
import { User } from '../types/user';
import useIdleTimer from '../hooks/useIdleTimer';
import SessionTimeoutModal from '../components/modals/SessionTimeoutModal';

interface AuthContextType {
  token: string | null;
  user: User | null;
  setUser: React.Dispatch<React.SetStateAction<User | null>>;
  isLoading: boolean;
  error: string | null;
  deploymentMode: 'server' | 'desktop' | null;
  login: (data: { access_token: string, deployment_mode: 'server' | 'desktop' }) => void;
  logout: () => void;
  register: (email: string) => Promise<void>;
}

// eslint-disable-next-line react-refresh/only-export-components
export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [deploymentMode, setDeploymentMode] = useState<'server' | 'desktop' | null>(
    localStorage.getItem('deployment_mode') as 'server' | 'desktop' | null
  );
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error] = useState<string | null>(null);
  const [isIdle, setIsIdle] = useState(false);

  const getTimeout = () => {
    const e2eTimeout = sessionStorage.getItem('e2e_inactivity_timeout');
    if (e2eTimeout) {
      return parseInt(e2eTimeout, 10);
    }
    const timeoutMinutes = parseInt(import.meta.env.VITE_INACTIVITY_TIMEOUT_MINUTES || '30', 10);
    return timeoutMinutes * 60 * 1000;
  };

  const timeout = getTimeout();

  const handleIdle = () => {
    setIsIdle(true);
  };

  const handleCloseModal = () => {
    setIsIdle(false);
  };

  useIdleTimer(timeout, handleIdle);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    setDeploymentMode(null);
    localStorage.removeItem('token');
    localStorage.removeItem('deployment_mode');
    delete api.defaults.headers.common['Authorization'];
    window.location.href = '/login';
  }, []);

  useEffect(() => {
    const responseInterceptor = api.interceptors.response.use(
      response => response,
      (error) => {
        if (error.response && error.response.status === 403) {
          // This indicates an expired or invalid token
          logout();
        }
        return Promise.reject(error);
      }
    );

    return () => {
      api.interceptors.response.eject(responseInterceptor);
    };
  }, [logout]);

  const fetchUserData = useCallback(async () => {
    setIsLoading(true);
    try {
      const { data } = await api.get<User>('/api/v1/users/me');
      setUser(data);
    } catch (err) {
      logout();
    } finally {
      setIsLoading(false);
    }
  }, [logout]);

  useEffect(() => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUserData();
    } else {
      setIsLoading(false);
    }
  }, [token, fetchUserData]);

  const login = (data: { access_token: string, deployment_mode: 'server' | 'desktop' }) => {
    setToken(data.access_token);
    setDeploymentMode(data.deployment_mode);
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('deployment_mode', data.deployment_mode);
  };

  const register = async (email: string) => {
    // This function can be expanded if needed
    console.log("Register function called for", email);
  };

  const getModalCountdown = () => {
    const e2eCountdown = sessionStorage.getItem('e2e_modal_countdown_seconds');
    if (e2eCountdown) {
      return parseInt(e2eCountdown, 10);
    }
    return 120;
  };

  return (
    <AuthContext.Provider value={{ token, user, setUser, isLoading, error, deploymentMode, login, logout, register }}>
      {children}
      <SessionTimeoutModal
        isOpen={isIdle}
        onClose={handleCloseModal}
        onLogout={logout}
        countdownSeconds={getModalCountdown()}
      />
    </AuthContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};