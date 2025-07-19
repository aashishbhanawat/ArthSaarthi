import React, { createContext, useState, useContext, useEffect, ReactNode, useCallback } from 'react';
import api from '../services/api';
import { User } from '../types/user';

interface AuthContextType {
  token: string | null;
  user: User | null;
  isLoading: boolean;
  error: string | null;
  login: (token: string) => void;
  logout: () => void;
  register: (email: string, password: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    delete api.defaults.headers.common['Authorization'];
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

  const fetchUserData = async () => {
    setIsLoading(true);
    try {
      const { data } = await api.get<User>('/api/v1/users/me');
      setUser(data);
    } catch (err) {
      logout();
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUserData();
    } else {
      setIsLoading(false);
    }
  }, [token]);

  const login = (newToken: string) => {
    setToken(newToken);
    localStorage.setItem('token', newToken);
  };

  const register = async (email: string, password: string) => {
    // This function can be expanded if needed
    console.log("Register function called for", email);
  };

  return (
    <AuthContext.Provider value={{ token, user, isLoading, error, login, logout, register }}>
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