import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { getCurrentUser } from "../services/api";

interface User {
    full_name: string;
    email: string;
}

const DashboardPage: React.FC = () => {
    const { setToken } = useAuth();
    const [user, setUser] = useState<User | null>(null);
    const [error, setError] = useState("");

    useEffect(() => {
        const fetchUser = async () => {
            try {
                const userData = await getCurrentUser();
                setUser(userData);
            } catch (err) {
                setError("Failed to fetch user data.");
                // Optional: handle token expiration by logging out
                // setToken(null);
            }
        };
        fetchUser();
    }, []);

    const handleLogout = () => {
        setToken(null);
    };

    return (
        <div>
            <h1>Dashboard</h1>
            {user && <p>Welcome, {user.full_name}! You are logged in.</p>}
            {error && <p style={{ color: "red" }}>{error}</p>}
            <button onClick={handleLogout}>Logout</button>
        </div>
    );
};

export default DashboardPage;