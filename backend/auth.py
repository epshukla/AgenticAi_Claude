"""
Authentication module for the AI Agent.

Simple session-based authentication with shared demo password.
"""

import hashlib
from functools import wraps
from flask import session, request, jsonify
from typing import Optional, Dict

from . import database as db

SHARED_PASSWORD = "demo123"


def hash_password(password: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == password_hash


def login_user(username: str, password: str) -> Dict:
    """
    Attempt to log in a user.
    Returns user dict on success, error dict on failure.
    """
    user = db.get_user_by_username(username)

    if not user:
        return {"error": "User not found", "success": False}

    # Check password
    if not verify_password(password, user.get('password_hash', '')):
        return {"error": "Invalid password", "success": False}

    # Set session
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['role'] = user['role']

    return {
        "success": True,
        "user": {
            "id": user['id'],
            "username": user['username'],
            "role": user['role'],
            "email": user.get('email')
        }
    }


def logout_user() -> Dict:
    """Log out the current user."""
    session.clear()
    return {"success": True, "message": "Logged out successfully"}


def get_current_user() -> Optional[Dict]:
    """Get the current logged-in user from session."""
    if 'user_id' not in session:
        return None

    return {
        "id": session.get('user_id'),
        "username": session.get('username'),
        "role": session.get('role')
    }


def login_required(f):
    """Decorator to require login for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        if user.get('role') != 'admin':
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated_function
