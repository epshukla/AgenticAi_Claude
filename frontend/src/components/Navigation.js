import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Navigation.css';

const Navigation = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const isActive = (path) => location.pathname === path;

  const getRoleBadgeColor = (role) => {
    const colors = {
      admin: '#e53e3e',
      developer: '#3182ce',
      tester: '#38a169'
    };
    return colors[role] || '#666';
  };

  return (
    <nav className="navigation">
      <div className="nav-container">
        <Link to="/dashboard" className="nav-brand">
          AI Agent Dashboard
        </Link>

        <div className="nav-links">
          <Link
            to="/dashboard"
            className={`nav-link ${isActive('/dashboard') ? 'active' : ''}`}
          >
            Dashboard
          </Link>
          <Link
            to="/files"
            className={`nav-link ${isActive('/files') ? 'active' : ''}`}
          >
            File Browser
          </Link>
        </div>

        <div className="nav-user">
          {user && (
            <>
              <span className="user-name">{user.username}</span>
              <span
                className="user-role"
                style={{ background: getRoleBadgeColor(user.role) }}
              >
                {user.role}
              </span>
              <button className="logout-button" onClick={handleLogout}>
                Logout
              </button>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
