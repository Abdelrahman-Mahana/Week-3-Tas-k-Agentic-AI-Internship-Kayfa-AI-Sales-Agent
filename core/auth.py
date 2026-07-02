"""
Authentication layer: signup, login, session management, role checks.

This module is used by:
- Home.py         → login / signup gate
- 1_Chat_Agent.py → visitor chat (any authenticated user)
- 2_CRM_Tickets.py, 3_Cost_Monitor.py, 4_Behaviour_Trace.py → admin-only pages

Roles:
- "visitor"   → can chat with the sales agent
- "admin"     → can access CRM, Cost Monitor, Behaviour Trace
"""

import bcrypt
import streamlit as st
from core.db import get_users_collection
from pymongo.collection import Collection

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    """Hash a plain-text password."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ---------------------------------------------------------------------------
# User CRUD
# ---------------------------------------------------------------------------

def create_user(username: str, password: str, role: str = "visitor") -> dict:
    """Create a new user. Returns user dict or raises ValueError on duplicate."""
    coll: Collection = get_users_collection()

    if coll.find_one({"username": username}):
        raise ValueError(f"Username '{username}' already exists.")

    user_doc = {
        "username": username,
        "password_hash": hash_password(password),
        "role": role,  # "visitor" | "admin"
    }
    coll.insert_one(user_doc)
    return {"username": username, "role": role}


def authenticate_user(username: str, password: str) -> dict | None:
    """Authenticate and return user dict (without password), or None."""
    coll: Collection = get_users_collection()
    user = coll.find_one({"username": username})
    if user and verify_password(password, user["password_hash"]):
        return {"username": user["username"], "role": user["role"]}
    return None


# ---------------------------------------------------------------------------
# Streamlit session helpers
# ---------------------------------------------------------------------------

def login_user(username: str, role: str):
    """Store user in Streamlit session state."""
    st.session_state["user"] = {"username": username, "role": role}


def logout_user():
    """Clear user from Streamlit session state."""
    st.session_state.pop("user", None)
    # Also clear chat-related state on logout
    for key in list(st.session_state.keys()):
        if key.startswith(("chat_", "agent_")):
            st.session_state.pop(key, None)


def get_current_user() -> dict | None:
    """Return current user dict from session state, or None."""
    return st.session_state.get("user")


def is_authenticated() -> bool:
    """Check if a user is currently logged in."""
    return get_current_user() is not None


def is_admin() -> bool:
    """Check if current user has admin role."""
    user = get_current_user()
    return user is not None and user.get("role") == "admin"


def require_auth():
    """Call at the top of a page to enforce login.

    Usage:
        require_auth()  # redirects to login if not authenticated
    """
    if not is_authenticated():
        st.error("Please log in to access this page.")
        st.stop()


def require_admin():
    """Call at the top of an admin page to enforce admin role.

    Usage:
        require_auth()
        require_admin()
    """
    if not is_admin():
        st.error("Access denied. Admin privileges required.")
        st.stop()


def init_session_state():
    """Initialize session-state keys on first run."""
    if "user" not in st.session_state:
        st.session_state["user"] = None
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    if "agent_run_id" not in st.session_state:
        st.session_state["agent_run_id"] = None
