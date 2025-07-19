import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const AdminRoute: React.FC = () => {
    const { user } = useAuth();

    // This check is important. If user data is not yet loaded, we can show a loader or null.
    if (!user) return null; // Or a loading spinner

    return user.is_admin ? <Outlet /> : <Navigate to="/dashboard" replace />;
};

export default AdminRoute;