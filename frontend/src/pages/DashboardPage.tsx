import React from "react";
import { useAuth } from "../context/AuthContext";  

const DashboardPage: React.FC = () => {
    const { user } = useAuth();

    return (
        <div className="page-container" id="DashboardPage">
            <h1>Dashboard</h1>
            {user && <p>Welcome, {user.full_name || "User"}! You are logged in.</p>}
        </div>
    );
};

export default DashboardPage;