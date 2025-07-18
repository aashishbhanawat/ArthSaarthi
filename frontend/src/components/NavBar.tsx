import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const NavBar: React.FC = () => {
  const { token, logout, user } = useAuth();
  const isLoggedIn = !!token;

  const handleLogout = () => {
    logout();
  };

  if (!isLoggedIn) {
    return null; // Don't render the navbar if the user isn't logged in
  }

  return (
    <div className="navbar">
      <nav>
        <ul>
          <li>
            <NavLink to="/" end className={({ isActive }) => isActive ? 'active' : ''}>
              Dashboard
            </NavLink>
          </li>
          {user?.is_admin && (
            <li>
              <NavLink to="/admin/users" className={({ isActive }) => isActive ? 'active' : ''}>
                User Management
              </NavLink>
            </li>
          )}
          {/* Add more navigation items here as needed */}
        </ul>
      </nav>
      <button onClick={handleLogout} className="button-danger">
        Logout
      </button>
    </div>
  );
};

export default NavBar;