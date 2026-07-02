"""
Home.py — Streamlit entrypoint and authentication gate.

This is the first page users see. It handles:
- Login / Signup forms
- Role-based redirect after login
- Logout

Pages:
- Chat Agent       (any authenticated user)
- CRM Tickets      (admin only)
- Cost Monitor     (admin only)
- Behaviour Trace  (admin only)
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import streamlit as st
import textwrap

# Setup Logo Path and auto-copy logic
LOGO_PATH = Path(__file__).resolve().parent / "logo.png"
_logo_src = "/home/abdelrahman-mahana/.gemini/antigravity-ide/brain/cf8a9508-aa02-4652-9b42-fef9a1bda6af/media__1782842573807.png"
if os.path.exists(_logo_src) and not LOGO_PATH.exists():
    try:
        shutil.copy(_logo_src, LOGO_PATH)
    except Exception:
        pass

# Must be the first Streamlit call
st.set_page_config(
    page_title="Kayfa Sales Agent",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="expanded",
)

from core.auth import (
    init_session_state,
    authenticate_user,
    create_user,
    login_user,
    logout_user,
    get_current_user,
    is_authenticated,
    is_admin,
)
from core.config import get_settings
from rag.retriever import is_kb_ready
from sidebar_helper import render_sidebar

settings = get_settings()

# Initialize session state
init_session_state()

# ---------------------------------------------------------------------------
# CSS Styling (Main Content)
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

    .stApp, .stApp [data-testid="stHeader"] {
        font-family: 'Inter', 'Cairo', 'Segoe UI', Tahoma, sans-serif !important;
    }

    /* Primary buttons */
    div.stButton > button[kind="primary"] {
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-family: 'Inter', 'Cairo', sans-serif !important;
        background-color: #3b82f6 !important;
        border: none !important;
        padding: 10px 24px !important;
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.2) !important;
        transition: all 0.2s !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #2563eb !important;
        box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.3) !important;
        transform: translateY(-1px) !important;
    }

    /* Tabs styling */
    [data-testid="stTabBar"] {
        background-color: transparent !important;
        border-bottom: 2px solid rgba(0, 0, 0, 0.05) !important;
        gap: 24px !important;
    }
    
    [data-testid="stTabBar"] button {
        font-weight: 600 !important;
        font-family: 'Inter', 'Cairo', sans-serif !important;
        color: #64748b !important;
        border: none !important;
        padding: 12px 8px !important;
        transition: all 0.2s !important;
    }
    
    [data-testid="stTabBar"] button[aria-selected="true"] {
        color: #3b82f6 !important;
        border-bottom: 2px solid #3b82f6 !important;
    }

    /* Form input styling */
    [data-testid="stTextInput"] input {
        border-radius: 8px !important;
        border: 1px solid rgba(0, 0, 0, 0.12) !important;
        padding: 10px 14px !important;
        font-family: 'Inter', 'Cairo', sans-serif !important;
        transition: all 0.2s !important;
    }
    
    [data-testid="stTextInput"] input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15) !important;
    }

    /* Dashboard Cards */
    .dashboard-card {
        background-color: #ffffff;
        border: 1px solid rgba(0, 0, 0, 0.06);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.01);
        margin-bottom: 16px;
        font-family: 'Inter', 'Cairo', sans-serif;
    }
    
    .dashboard-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 16px;
        margin-top: 15px;
        margin-bottom: 25px;
    }

    .nav-card {
        background-color: #ffffff;
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
        transition: all 0.2s ease-in-out;
        text-decoration: none !important;
        color: inherit !important;
        display: flex;
        flex-direction: column;
        gap: 6px;
        cursor: pointer;
    }

    .nav-card:hover {
        transform: translateY(-2px);
        border-color: #3b82f6;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
    }

    .nav-card-title {
        font-weight: 700;
        font-size: 1.05rem;
        color: #1e293b;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .nav-card-desc {
        font-size: 0.85rem;
        color: #64748b;
        line-height: 1.4;
    }

    /* Metric cards styling */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #1e293b !important;
    }

    /* Info containers */
    div.stAlert {
        border-radius: 10px !important;
        border: 1px solid rgba(0, 0, 0, 0.05) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Render Sidebar navigation
render_sidebar()

# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------
# Center alignment structure
st.markdown('<div style="text-align: center; margin-bottom: 20px;">', unsafe_allow_html=True)
if LOGO_PATH.exists():
    st.image(str(LOGO_PATH), width=280)
st.title("Welcome to Kayfa Sales Agent")
st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Auth forms
# ---------------------------------------------------------------------------
if not is_authenticated():
    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

    with tab_login:
        st.subheader("Login")
        login_username = st.text_input("Username", key="login_user")
        login_password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login", use_container_width=True, type="primary"):
            if not login_username or not login_password:
                st.error("Please enter both username and password.")
            else:
                user = authenticate_user(login_username, login_password)
                if user:
                    login_user(user["username"], user["role"])
                    st.success(f"Welcome, {user['username']}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

    with tab_signup:
        st.subheader("Create Account")
        new_username = st.text_input("Username", key="signup_user")
        new_password = st.text_input("Password", type="password", key="signup_pass")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")

        if st.button("Sign Up", use_container_width=True, type="primary"):
            if not new_username or not new_password:
                st.error("Please fill in all fields.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                try:
                    user = create_user(new_username, new_password, role="visitor")
                    login_user(user["username"], user["role"])
                    st.success("Account created! Welcome to Kayfa.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Error creating account: {e}")

else:
    # User is logged in — show dashboard
    user = get_current_user()
    st.success(f"Welcome back, **{user['username']}**! 👋")

    # Interactive Dashboard Navigation Cards
    st.markdown("### 🚀 Getting Started / ابدأ من هنا")
    if is_admin():
        html_cards = (
            '<div class="dashboard-grid">'
            '<a class="nav-card" href="/Chat_Agent" target="_self">'
            '<div class="nav-card-title">💬 Chat Agent</div>'
            '<div class="nav-card-desc">Ask about courses, tracks, diplomas, and policies. / اسأل عن مسارات ودبلومات وهيكل أسعار كودر.</div>'
            '</a>'
            '<a class="nav-card" href="/CRM_Tickets" target="_self">'
            '<div class="nav-card-title">📋 CRM Tickets</div>'
            '<div class="nav-card-desc">View and manage leads and potential students. / استعراض وإدارة بيانات الطلاب والعملاء المهتمين.</div>'
            '</a>'
            '<a class="nav-card" href="/Cost_Monitor" target="_self">'
            '<div class="nav-card-title">💰 Cost Monitor</div>'
            '<div class="nav-card-desc">Track and estimate API costs and token usage. / متابعة وإحصاء تكاليف الاستهلاك وحجم الرموز للوكيل.</div>'
            '</a>'
            '<a class="nav-card" href="/Behaviour_Trace" target="_self">'
            '<div class="nav-card-title">🔍 Behaviour Trace</div>'
            '<div class="nav-card-desc">Inspect agent decision steps and details. / تتبع خطوات التفكير وتحليل قرارات الذكاء الاصطناعي.</div>'
            '</a>'
            '</div>'
        )
    else:
        html_cards = (
            '<div class="dashboard-grid">'
            '<a class="nav-card" href="/Chat_Agent" target="_self">'
            '<div class="nav-card-title">💬 Chat Agent</div>'
            '<div class="nav-card-desc">Ask about courses, tracks, diplomas, and policies. / اسأل عن مسارات ودبلومات وهيكل أسعار كودر.</div>'
            '</a>'
            '</div>'
        )
    st.markdown(html_cards, unsafe_allow_html=True)

    st.markdown("### 🏫 About Kayfa / عن كيف")
    st.info(
        "Kayfa is a leading Arabic e-learning platform offering courses in Data Science, "
        "Cybersecurity (SOC), Web Development, AI, and more. This AI sales agent helps "
        "prospective students discover the right learning path."
    )

    # Quick stats
    if is_admin():
        st.markdown("---")
        st.subheader("📊 System Overview / نظرة عامة على النظام")

        try:
            from core.db import get_leads_collection, get_usage_logs_collection

            leads_coll = get_leads_collection()
            usage_coll = get_usage_logs_collection()

            col1, col2, col3 = st.columns(3)
            with col1:
                lead_count = leads_coll.count_documents({})
                st.metric("Total Leads", lead_count)
            with col2:
                today = datetime.now().strftime("%Y-%m-%d")
                today_usage = usage_coll.count_documents({
                    "timestamp": {"$gte": f"{today}T00:00:00"}
                })
                st.metric("Today's API Calls", today_usage)
            with col3:
                if is_kb_ready():
                    st.metric("KB Status", "Ready ✅")
                else:
                    st.metric("KB Status", "Not Built ⚠️")
        except Exception as e:
            st.caption(f"Stats unavailable: {e}")
