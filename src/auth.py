"""
CampusSpace Authentication & Authorization Module
Handles secure PBKDF2 password hashing, credential verification,
role-based access control, and session helpers.
"""

import hashlib
import hmac
import secrets
from typing import Dict, Any, Optional, Tuple


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Hash a password using PBKDF2-HMAC-SHA256 with 100,000 iterations.
    Returns (salt_hex, hash_hex).
    """
    if not salt:
        salt = secrets.token_hex(16)
    salt_bytes = bytes.fromhex(salt)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, 100_000)
    return salt, key.hex()


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    """
    Verify a password against stored salt and PBKDF2-HMAC-SHA256 hash
    using constant-time comparison to prevent timing attacks.
    """
    try:
        salt_bytes = bytes.fromhex(salt)
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, 100_000)
        return hmac.compare_digest(key.hex(), expected_hash)
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────
# Default User Store (Salted PBKDF2 Hashes)
# ─────────────────────────────────────────────────────────────
# We generate secure salted hashes for the 4 university personas:
# 1. student  / campus123  (Alex Kumar - Student)
# 2. faculty  / faculty456 (Dr. Priya Sharma - Faculty)
# 3. admin    / admin789   (Campus Administrator - Administrator)
# 4. club     / club321    (Rohan Verma - Club Organizer)
_USER_STORE: Dict[str, Dict[str, Any]] = {}

def _init_default_users():
    defaults = [
        ("student", "student@campus.edu", "campus123", "Student", "Alex Kumar"),
        ("faculty", "faculty@campus.edu", "faculty456", "Faculty", "Dr. Priya Sharma"),
        ("admin", "admin@campus.edu", "admin789", "Administrator", "Campus Admin"),
        ("club", "club@campus.edu", "club321", "Club Organizer", "Rohan Verma"),
    ]
    for username, email, pw, role, display in defaults:
        salt, hsh = hash_password(pw)
        _USER_STORE[username.lower()] = {
            "username": username.lower(),
            "email": email.lower(),
            "salt": salt,
            "hash": hsh,
            "role": role,
            "display": display,
        }

_init_default_users()


def register_user(
    username: str,
    email: str,
    password: str,
    role: str = "Student",
    display: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Register or update a user with a securely salted PBKDF2 hash.
    """
    username = username.strip().lower()
    email = email.strip().lower()
    if not username:
        return False, "Username cannot be empty."
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters."

    salt, hsh = hash_password(password)
    _USER_STORE[username] = {
        "username": username,
        "email": email,
        "salt": salt,
        "hash": hsh,
        "role": role,
        "display": display or username.title(),
    }
    return True, "User registered successfully."


def authenticate_user(identifier: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Authenticate a user by username OR email.
    Returns: (is_success, user_dict_or_none, error_message)
    """
    identifier = (identifier or "").strip().lower()
    if not identifier:
        return False, None, "Please enter your username or university email."
    if not password:
        return False, None, "Please enter your password."

    # Lookup user by username, email, display name, or role
    user = None
    if identifier in _USER_STORE:
        user = _USER_STORE[identifier]
    else:
        for u in _USER_STORE.values():
            if (u["email"] == identifier or
                u["display"].lower() == identifier or
                u["role"].lower() == identifier or
                u["display"].lower().split()[0] == identifier):
                user = u
                break

    if not user:
        return False, None, "Invalid username/email or password."

    # Verify password against hash
    if not verify_password(password, user["salt"], user["hash"]):
        return False, None, "Invalid username/email or password."

    # Return safe user dictionary (strip salt and hash)
    safe_user = {
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
        "display": user["display"],
    }
    return True, safe_user, ""


def get_demo_accounts_table() -> list[dict]:
    """
    Return clean metadata about the configured demo accounts for evaluation.
    """
    return [
        {"Role": "Student", "Username": "student", "Email": "student@campus.edu", "Demo Password": "campus123", "Persona": "Alex Kumar"},
        {"Role": "Faculty", "Username": "faculty", "Email": "faculty@campus.edu", "Demo Password": "faculty456", "Persona": "Dr. Priya Sharma"},
        {"Role": "Administrator", "Username": "admin", "Email": "admin@campus.edu", "Demo Password": "admin789", "Persona": "Campus Admin"},
        {"Role": "Club Organizer", "Username": "club", "Email": "club@campus.edu", "Demo Password": "club321", "Persona": "Rohan Verma"},
    ]


# ─────────────────────────────────────────────────────────────
# Session State Helpers
# ─────────────────────────────────────────────────────────────
def is_authenticated(session_state) -> bool:
    """Check if the user is authenticated (not guest)."""
    return bool(session_state.get("logged_in") and session_state.get("username") and session_state.get("role") != "Guest")


def is_guest(session_state) -> bool:
    """Check if browsing in guest mode."""
    return bool(session_state.get("logged_in") and session_state.get("role") == "Guest")


def is_admin(session_state) -> bool:
    """Check if current user is an Administrator."""
    return is_authenticated(session_state) and session_state.get("role") == "Administrator"


def is_faculty_or_admin(session_state) -> bool:
    """Check if user has Faculty or Administrator privileges."""
    return is_authenticated(session_state) and session_state.get("role") in ("Administrator", "Faculty")


def login_user(session_state, user_dict: Dict[str, Any], remember: bool = False):
    """Set authentication session state."""
    session_state["logged_in"] = True
    session_state["username"] = user_dict.get("username", "")
    session_state["email"] = user_dict.get("email", "")
    session_state["role"] = user_dict.get("role", "Student")
    session_state["display_name"] = user_dict.get("display", user_dict.get("username", "").title())
    session_state["remember_me"] = remember


def login_guest(session_state):
    """Enable public browsing mode."""
    session_state["logged_in"] = True
    session_state["username"] = "guest"
    session_state["email"] = "visitor@campus.edu"
    session_state["role"] = "Guest"
    session_state["display_name"] = "Campus Visitor"
    session_state["remember_me"] = False


def logout_user(session_state):
    """Clear authentication session state."""
    session_state["logged_in"] = False
    session_state["username"] = ""
    session_state["email"] = ""
    session_state["role"] = ""
    session_state["display_name"] = ""
    session_state["remember_me"] = False
    session_state["search_done"] = False
