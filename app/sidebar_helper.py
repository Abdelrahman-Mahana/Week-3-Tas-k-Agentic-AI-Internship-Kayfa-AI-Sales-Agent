"""
sidebar_helper.py — Centralized Custom Sidebar Navigation.
Hides Streamlit's default page list and builds a premium, clean menu.
"""

import sys
from pathlib import Path
repo_root = str(Path(__file__).resolve().parent.parent)
if repo_root not in sys.path:
    sys.path.append(repo_root)

import streamlit as st
from core.auth import is_authenticated, is_admin, get_current_user, logout_user

LOGO_PATH = Path(__file__).resolve().parent / "logo.png"

def render_sidebar():
    """Inject custom styles and render the sidebar navigation menu."""
    
    # CSS injection for styling custom page links, hiding Streamlit default navigation,
    # and adjusting general sidebar cosmetics
    st.markdown(
        """
        <style>
        /* Hide Streamlit default pages list */
        [data-testid="stSidebarNav"] {
            display: none !important;
        }

        /* Sidebar container layout styling */
        [data-testid="stSidebar"] {
            background-color: #f8fafc !important;
            border-right: 1px solid rgba(0, 0, 0, 0.06) !important;
        }

        /* Styled User profile card */
        .sidebar-user-card {
            background-color: #ffffff;
            border: 1px solid rgba(0, 0, 0, 0.05);
            border-radius: 12px;
            padding: 14px 16px;
            margin: 12px 0;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
            font-family: 'Inter', 'Cairo', sans-serif;
        }
        
        .sidebar-user-name {
            font-weight: 700;
            color: #1e293b;
            font-size: 0.95rem;
        }

        .sidebar-user-role {
            font-size: 0.8rem;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-top: 4px;
        }

        /* Menu section headers */
        .sidebar-menu-header {
            font-size: 0.72rem !important;
            font-weight: 700 !important;
            color: #94a3b8 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.08em !important;
            margin: 20px 14px 8px 14px !important;
            font-family: 'Inter', 'Cairo', sans-serif !important;
        }

        /* Style native page_link widgets in sidebar */
        [data-testid="stSidebar"] [data-testid="stPageLink"] a {
            display: flex !important;
            align-items: center !important;
            padding: 10px 14px !important;
            border-radius: 10px !important;
            color: #475569 !important;
            font-family: 'Inter', 'Cairo', sans-serif !important;
            font-weight: 500 !important;
            text-decoration: none !important;
            background-color: transparent !important;
            transition: all 0.2s ease-in-out !important;
            margin-bottom: 4px !important;
            border: none !important;
        }

        [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
            background-color: rgba(59, 130, 246, 0.08) !important;
            color: #1d4ed8 !important;
            transform: translateX(4px) !important;
        }

        /* Active page page_link styling */
        [data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"] {
            background-color: #3b82f6 !important;
            color: #ffffff !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.2) !important;
        }

        /* Red logout button customization */
        [data-testid="stSidebar"] button[kind="secondary"] {
            border-radius: 8px !important;
            border: 1px solid rgba(0, 0, 0, 0.1) !important;
            background-color: #ffffff !important;
            color: #ef4444 !important;
            font-weight: 600 !important;
            transition: all 0.2s !important;
            font-family: 'Inter', 'Cairo', sans-serif !important;
        }
        
        [data-testid="stSidebar"] button[kind="secondary"]:hover {
            background-color: #fef2f2 !important;
            border-color: #fca5a5 !important;
            color: #dc2626 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        # Display Logo
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), use_container_width=True)
        else:
            st.markdown(
                '<div style="font-size:1.3rem; font-weight:700; color:#1e293b; font-family:\'Cairo\'; text-align:center;">🎓 Kayfa Sales Agent</div>', 
                unsafe_allow_html=True
            )
        
        st.markdown("---")

        if is_authenticated():
            user = get_current_user()
            
            # User profile card
            st.markdown(
                f"""
                <div class="sidebar-user-card">
                    <div class="sidebar-user-name">👤 {user['username']}</div>
                    <div class="sidebar-user-role">🔑 {user['role']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            st.markdown("---")

            # Main category links
            st.markdown('<div class="sidebar-menu-header">Menu</div>', unsafe_allow_html=True)
            st.page_link("Home.py", label="🏠 Home")
            st.page_link("pages/1_Chat_Agent.py", label="💬 Chat Agent")

            # Admin tools category links
            if is_admin():
                st.markdown('<div class="sidebar-menu-header">Admin Tools</div>', unsafe_allow_html=True)
                st.page_link("pages/2_CRM_Tickets.py", label="📋 CRM Tickets")
                st.page_link("pages/3_Cost_Monitor.py", label="💰 Cost Monitor")
                st.page_link("pages/4_Behaviour_Trace.py", label="🔍 Behaviour Trace")

            st.markdown("---")
            if st.button("Logout", use_container_width=True, key="sidebar_logout_btn"):
                logout_user()
                st.rerun()
        else:
            st.info("Please log in to access the agent.")
