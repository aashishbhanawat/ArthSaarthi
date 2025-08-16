import { createContext, useState, useContext, useEffect, ReactNode, useCallback } from 'react';
import api from '../services/api';
import { User, UserWithDeploymentMode } from '../types/user';

interface AuthContextType {
  token: string | null;
  user: User | null;
  deploymentMode: 'single_user' | 'multi_user' | null;
  isLoading: boolean;
  error: string | null;
  login: (token: string, user: User, deploymentMode: 'single_user' | 'multi_user') => void;
  logout: () => void;
  register: (email: string) => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [user, setUser] = useState<User | null>(null);
  const [deploymentMode, setDeploymentMode] = useState<'single_user' | 'multi_user' | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error] = useState<string | null>(null);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    setDeploymentMode(null);
    localStorage.removeItem('token');
    delete api.defaults.headers.common['Authorization'];
  }, []);

  useEffect(() => {
    const responseInterceptor = api.interceptors.response.use(
      response => response,
      (error) => {
        if (error.response && error.response.status === 403) {
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
      const { data } = await api.get<UserWithDeploymentMode>('/api/v1/users/me');
      setUser(data);
      setDeploymentMode(data.deployment_mode);
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

  const login = (newToken: string, newUser: User, newDeploymentMode: 'single_user' | 'multi_user') => {
    setToken(newToken);
    localStorage.setItem('token', newToken);
    setUser(newUser);
    setDeploymentMode(newDeploymentMode);
    api.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
  };

  const register = async (email: string) => {
    console.log("Register function called for", email);
  };

  return (
    <AuthContext.Provider value={{ token, user, deploymentMode, isLoading, error, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};