import React, { createContext, useState, useContext, useEffect, ReactNode, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../services/api';
import * as api from '../services/api';
import { User } from '../types';
import axios, { AxiosError } from 'axios';

interface AuthContextType {
    token: string | null;
    user: User | null;
    loading: boolean;
    login: (token: string) => void;
    logout: () => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchUserData = async () => {
            if (token) {
                try {
                    const userData = await api.getCurrentUser();
                    setUser(userData);
                } catch (error) {
                    console.error("Failed to fetch user data, session might be invalid.", error);
                    // The interceptor will handle logging out if the token is truly invalid
                }
            }
            setLoading(false);
        };

        fetchUserData();
    }, [token]);

    const login = (newToken: string) => {
        setToken(newToken);
        localStorage.setItem('token', newToken);
    };

    const logout = () => {
        api.logoutUser().catch(err => console.error("Logout API call failed, but proceeding with client-side logout.", err));
        setUser(null);
        setToken(null);
        localStorage.removeItem('token');
        navigate('/login', { replace: true });
    };

    useEffect(() => {
        const requestInterceptor = apiClient.interceptors.request.use(
            (config) => {
                const currentToken = localStorage.getItem('token');
                if (currentToken) {
                    config.headers.Authorization = `Bearer ${currentToken}`;
                }
                return config;
            },
            (error) => Promise.reject(error)
        );

        const responseInterceptor = apiClient.interceptors.response.use(
            (response) => response,
            async (error: AxiosError) => {
                const originalRequest = error.config;
                // @ts-ignore
                if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
                    // @ts-ignore
                    originalRequest._retry = true;
                    try {
                        console.log("Access token expired. Attempting to refresh...");
                        const { access_token } = await api.refreshToken();
                        login(access_token);
                        // @ts-ignore
                        originalRequest.headers.Authorization = `Bearer ${access_token}`;
                        return apiClient(originalRequest);
                    } catch (refreshError) {
                        console.error("Refresh token failed or expired. Logging out.", refreshError);
                        logout();
                        return Promise.reject(refreshError);
                    }
                }
                return Promise.reject(error);
            }
        );

        return () => {
            apiClient.interceptors.request.eject(requestInterceptor);
            apiClient.interceptors.response.eject(responseInterceptor);
        };
    }, [login, logout]); // Re-run effect if login/logout functions change

    return (
        <AuthContext.Provider value={{ token, user, loading, login, logout }}>
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
