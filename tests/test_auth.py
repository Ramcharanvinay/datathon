"""
Unit tests for CampusSpace Authentication & Security Module (src/auth.py)
"""

import pytest
from src.auth import (
    hash_password,
    verify_password,
    authenticate_user,
    register_user,
    is_authenticated,
    is_admin,
    is_guest,
    login_user,
    login_guest,
    logout_user,
)


def test_hash_and_verify_password():
    salt, hsh = hash_password("secret123")
    assert salt is not None and len(salt) == 32
    assert hsh is not None and len(hsh) == 64
    assert verify_password("secret123", salt, hsh) is True
    assert verify_password("wrongpassword", salt, hsh) is False
    assert verify_password("", salt, hsh) is False


def test_authenticate_default_users():
    # Test all 4 standard personas by username
    ok, u, err = authenticate_user("student", "campus123")
    assert ok is True
    assert u["role"] == "Student"
    assert u["display"] == "Alex Kumar"
    assert err == ""

    ok, u, err = authenticate_user("faculty", "faculty456")
    assert ok is True
    assert u["role"] == "Faculty"

    ok, u, err = authenticate_user("admin", "admin789")
    assert ok is True
    assert u["role"] == "Administrator"

    ok, u, err = authenticate_user("club", "club321")
    assert ok is True
    assert u["role"] == "Club Organizer"


def test_authenticate_by_email():
    ok, u, err = authenticate_user("student@campus.edu", "campus123")
    assert ok is True
    assert u["username"] == "student"

    ok, u, err = authenticate_user("admin@campus.edu", "admin789")
    assert ok is True
    assert u["role"] == "Administrator"


def test_authenticate_by_persona_and_role():
    # Test by display name
    ok, u, err = authenticate_user("Alex Kumar", "campus123")
    assert ok is True
    assert u["role"] == "Student"

    # Test by first name
    ok, u, err = authenticate_user("Alex", "campus123")
    assert ok is True

    # Test by role title
    ok, u, err = authenticate_user("Administrator", "admin789")
    assert ok is True
    assert u["role"] == "Administrator"


def test_empty_or_invalid_credentials():
    # Empty username
    ok, u, err = authenticate_user("", "campus123")
    assert ok is False
    assert "Please enter your username" in err

    # Empty password
    ok, u, err = authenticate_user("student", "")
    assert ok is False
    assert "Please enter your password" in err

    # Nonexistent user
    ok, u, err = authenticate_user("nonexistent_user", "password123")
    assert ok is False
    assert "Invalid username" in err

    # Incorrect password
    ok, u, err = authenticate_user("student", "wrongpass")
    assert ok is False
    assert "Invalid username" in err


def test_user_registration():
    ok, msg = register_user("testuser", "test@campus.edu", "newsecurepass99", "Student", "Test User")
    assert ok is True
    ok_auth, u, _ = authenticate_user("testuser", "newsecurepass99")
    assert ok_auth is True
    assert u["display"] == "Test User"


def test_session_helpers():
    session = {}
    assert is_authenticated(session) is False
    assert is_admin(session) is False

    # Simulate Student login
    login_user(session, {"username": "student", "email": "student@campus.edu", "role": "Student", "display": "Alex Kumar"})
    assert is_authenticated(session) is True
    assert is_admin(session) is False
    assert is_guest(session) is False

    # Simulate Admin login
    login_user(session, {"username": "admin", "email": "admin@campus.edu", "role": "Administrator", "display": "Campus Admin"})
    assert is_authenticated(session) is True
    assert is_admin(session) is True

    # Simulate Guest login
    login_guest(session)
    assert is_guest(session) is True
    assert is_authenticated(session) is False
    assert is_admin(session) is False

    # Logout
    logout_user(session)
    assert is_authenticated(session) is False
    assert session["logged_in"] is False
