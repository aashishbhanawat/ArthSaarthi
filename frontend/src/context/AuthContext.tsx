import { createContext, useState, ReactNode, useContext, useEffect } from "react";
import api from "../services/api";

interface AuthContextType {
    token: string | null;
    login: (token: string) => void;
    logout: () => void;
    user: { is_admin: boolean; full_name?: string } | null; // Add user state with default structure
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [token, setTokenState] = useState<string | null>(localStorage.getItem("token"));
    const [user, setUser] = useState<{ is_admin: boolean; full_name?: string } | null>(null); // Initialize with a default structure

    useEffect(() => {
        const fetchUserData = async () => {
            if (token) {
                try {
                    const response = await api.get('/api/v1/users/me', { headers: { Authorization: `Bearer ${token}` } });
                    setUser(response.data);
                } catch (error) {
                    console.error("Failed to fetch user data on login", error);
                    setUser({ is_admin: false }); // Default to non-admin on error
                }
            } else {
                setUser(null);
            }
        };

        fetchUserData();
    }, [token]);

    const login = (token: string) => {
        localStorage.setItem("token", token);
        setTokenState(token);
    };

    const logout = () => {
        localStorage.removeItem("token");
        setTokenState(null);
        setUser(null);
    };

    const value: AuthContextType = { token, login, logout, user };
    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};