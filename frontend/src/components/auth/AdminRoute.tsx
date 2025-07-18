import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const AdminRoute: React.FC = () => {
    const { user } = useAuth();

    if (!user) return null; // Or a loading spinner

    return user.is_admin ? <Outlet /> : <Navigate to="/" replace />;
};

export default AdminRoute;