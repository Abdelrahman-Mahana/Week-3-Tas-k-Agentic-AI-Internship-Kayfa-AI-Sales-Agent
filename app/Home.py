"""
Home.py — Streamlit entrypoint and authentication gate.

This is the first page users see. It handles:
- Login / Signup forms
- Role-based redirect after login
- Logout
- Clean information overview of platform capabilities
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import streamlit as st

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
# CSS Styling (Premium Design System)
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

    .stApp, .stApp [data-testid="stHeader"] {
        font-family: 'Plus Jakarta Sans', 'Cairo', 'Segoe UI', Tahoma, sans-serif !important;
        background-color: #f8fafc !important;
    }

    /* Hero section styling */
    .hero-container {
        background: #ffffff;
        border-radius: 20px;
        padding: 40px 30px;
        text-align: center;
        margin-bottom: 35px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.03), 0 8px 10px -6px rgba(15, 23, 42, 0.03) !important;
        border: 1px solid #e2e8f0;
    }
    .hero-title {
        background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Plus Jakarta Sans', 'Cairo', sans-serif !important;
        font-weight: 800 !important;
        font-size: 2.3rem !important;
        margin-bottom: 12px !important;
        letter-spacing: -0.02em !important;
    }
    .hero-subtitle {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 500 !important;
        font-size: 1.1rem !important;
        color: #475569 !important;
        margin-bottom: 8px !important;
        line-height: 1.4 !important;
    }
    .hero-subtitle-ar {
        font-family: 'Cairo', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        color: #64748b !important;
        line-height: 1.4 !important;
    }

    /* Form container (tabs) styling */
    [data-testid="stTabs"] {
        background-color: #ffffff !important;
        border: 1px solid rgba(226, 232, 240, 0.8) !important;
        border-radius: 16px !important;
        padding: 28px !important;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.04), 0 8px 10px -6px rgba(15, 23, 42, 0.04) !important;
        margin-top: 15px !important;
        margin-bottom: 25px !important;
    }

    /* Tabs buttons styling */
    [data-testid="stTabBar"] {
        background-color: transparent !important;
        border-bottom: 2px solid rgba(241, 245, 249, 0.8) !important;
        gap: 24px !important;
        margin-bottom: 15px !important;
    }
    
    [data-testid="stTabBar"] button {
        font-weight: 600 !important;
        font-family: 'Plus Jakarta Sans', 'Cairo', sans-serif !important;
        color: #64748b !important;
        border: none !important;
        padding: 12px 16px !important;
        background-color: transparent !important;
        transition: all 0.2s ease !important;
    }
    
    [data-testid="stTabBar"] button[aria-selected="true"] {
        color: #2563eb !important;
        border-bottom: 2px solid #2563eb !important;
    }

    /* Primary buttons (Login, Sign Up) */
    div.stButton > button[kind="primary"] {
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        font-family: 'Plus Jakarta Sans', 'Cairo', sans-serif !important;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
        color: #ffffff !important;
        border: none !important;
        padding: 12px 24px !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2) !important;
        transition: all 0.25s ease !important;
        width: 100% !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.35) !important;
        transform: translateY(-1px) !important;
    }
    div.stButton > button[kind="primary"]:active {
        transform: translateY(1px) !important;
    }

    /* Form input styling */
    [data-testid="stTextInput"] input {
        border-radius: 10px !important;
        border: 1px solid #cbd5e1 !important;
        padding: 12px 16px !important;
        font-family: 'Plus Jakarta Sans', 'Cairo', sans-serif !important;
        font-size: 0.95rem !important;
        background-color: #f8fafc !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stTextInput"] input:focus {
        border-color: #3b82f6 !important;
        background-color: #ffffff !important;
        box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.12) !important;
    }

    /* Capabilities Section */
    .info-section {
        margin-top: 35px;
        margin-bottom: 35px;
    }
    .section-title {
        font-family: 'Plus Jakarta Sans', 'Cairo', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1.3rem !important;
        color: #0f172a !important;
        margin-top: 10px !important;
        margin-bottom: 20px !important;
        border-bottom: 2px solid #f1f5f9 !important;
        padding-bottom: 8px !important;
    }
    .info-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 20px;
    }
    .info-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 22px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.01);
        transition: all 0.3s ease;
    }
    .info-card:hover {
        transform: translateY(-3px);
        border-color: #cbd5e1;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.04);
    }
    .info-icon {
        font-size: 1.8rem;
        margin-bottom: 12px;
    }
    .info-card-title {
        font-weight: 700;
        font-size: 1.05rem;
        color: #1e293b;
        margin-bottom: 8px;
        font-family: 'Plus Jakarta Sans', 'Cairo', sans-serif;
    }
    .info-card-desc {
        font-size: 0.88rem;
        color: #64748b;
        line-height: 1.5;
        font-family: 'Plus Jakarta Sans', 'Cairo', sans-serif;
    }

    /* Custom Metric Cards */
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.01);
        font-family: 'Plus Jakarta Sans', 'Cairo', sans-serif;
        text-align: center;
        transition: all 0.2s ease;
        margin-bottom: 15px;
    }
    .metric-card:hover {
        border-color: #cbd5e1;
        box-shadow: 0 8px 12px -3px rgba(0, 0, 0, 0.04);
    }
    .metric-label {
        font-size: 0.82rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 4px;
    }
    .metric-desc {
        font-size: 0.78rem;
        color: #94a3b8;
    }
    .kb-ready {
        color: #10b981 !important;
    }
    .kb-not-ready {
        color: #f59e0b !important;
    }

    /* About Card */
    .about-card {
        background: #ffffff;
        border-left: 4px solid #3b82f6;
        border-radius: 12px;
        padding: 24px;
        margin-top: 30px;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.01);
    }
    .about-card h4 {
        margin-top: 0;
        font-weight: 700;
        font-size: 1.15rem;
        color: #0f172a;
        margin-bottom: 12px;
        font-family: 'Plus Jakarta Sans', 'Cairo', sans-serif;
    }
    .about-card p {
        font-size: 0.92rem;
        color: #475569;
        line-height: 1.6;
        margin: 0;
        font-family: 'Plus Jakarta Sans', 'Cairo', sans-serif;
    }

    /* Welcome Banner */
    .welcome-banner {
        background-color: #eff6ff;
        border: 1px solid #bfdbfe;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 30px;
        font-family: 'Plus Jakarta Sans', 'Cairo', sans-serif;
    }
    .welcome-text {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1e3a8a;
        margin-bottom: 4px;
    }
    .welcome-subtext {
        font-size: 0.88rem;
        color: #1d4ed8;
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
# Logo Layout (centered)
col_logo_1, col_logo_2, col_logo_3 = st.columns([1, 2, 1])
with col_logo_2:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), use_container_width=True)

# Hero Header Container
st.markdown(
    """
    <div class="hero-container">
        <h1 class="hero-title">Kayfa Sales Agent</h1>
        <p class="hero-subtitle">Smart AI Guidance for the Next Generation of Tech Leaders</p>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------------------------------
# Authentication Flow / Dashboard
# ---------------------------------------------------------------------------
if not is_authenticated():
    # Login / Sign up tabs styled elegantly
    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

    with tab_login:
        st.write("")  # padding
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
        st.write("")  # padding
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
    # User is logged in — show professional onboarding and overview
    user = get_current_user()
    
    st.markdown(
        f"""
        <div class="welcome-banner">
            <div class="welcome-text">Welcome back, <strong>{user['username']}</strong>! 👋</div>
            <div class="welcome-subtext">You are successfully authenticated as a <strong>{user['role']}</strong>. Please use the sidebar on the left to navigate between pages.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Capabilities overview replacing the redundant card buttons
    st.markdown(
        """
        <div class="info-section">
            <h3 class="section-title">✨ Platform Capabilities</h3>
            <div class="info-grid">
                <div class="info-card">
                    <div class="info-icon">💬</div>
                    <div class="info-card-title">Intelligent Consultation</div>
                    <div class="info-card-desc">The AI Agent interacts naturally, analyzing learner goals and recommending customized educational paths.</div>
                </div>
                <div class="info-card">
                    <div class="info-icon">📚</div>
                    <div class="info-card-title">Real-Time Knowledge</div>
                    <div class="info-card-desc">Instantly retrieves course availability, pricing, accreditation info, and syllabus details from our structured knowledge base.</div>
                </div>
                <div class="info-card">
                    <div class="info-icon">🤝</div>
                    <div class="info-card-title">Seamless CRM Handoff</div>
                    <div class="info-card-desc">Automatically compiles conversation details and customer preferences into structured CRM leads for final enrollment.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Clean information card explaining Kayfa e-learning
    st.markdown(
        """
        <div class="about-card">
            <h4>🏫 About Kayfa</h4>
            <p>Kayfa is a leading Arabic e-learning platform offering professional training in high-demand tech fields such as Data Science, Cybersecurity (SOC), Web Development, and Artificial Intelligence. Our mission is to bridge the skills gap and empower learners across the MENA region to build successful tech careers.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Interactive Course Catalog
    st.markdown('<h3 class="section-title">🎓 Training Programs & Tracks</h3>', unsafe_allow_html=True)
    cat_tab1, cat_tab2, cat_tab3, cat_tab4 = st.tabs([
        "🤖 AI & Machine Learning", 
        "🛡️ SOC Cybersecurity", 
        "📊 Data Science", 
        "💻 Web Development"
    ])
    
    with cat_tab1:
        st.markdown(
            """
            <div style="background-color: #ffffff; padding: 22px; border-radius: 14px; border: 1px solid #e2e8f0; margin-top: 10px;">
                <h4 style="color: #2563eb; margin: 0 0 10px 0; font-family: 'Plus Jakarta Sans', 'Cairo', sans-serif;">Artificial Intelligence Diploma</h4>
                <p style="margin: 0 0 6px 0; font-size: 0.9rem; color: #475569;"><b>Duration:</b> 6 Months (Live interactive lectures + practical labs)</p>
                <p style="margin: 0 0 6px 0; font-size: 0.9rem; color: #475569;"><b>Accreditation:</b> IAO, Leeds Academy, University of Delaware partner credentials</p>
                <p style="margin: 0 0 12px 0; font-size: 0.9rem; color: #475569;"><b>Syllabus:</b> Python Foundations, Machine Learning Models, Deep Learning (PyTorch), LLM Fine-tuning & RAG architectures, MLOps deployment pipelines.</p>
                <p style="margin: 0; font-size: 0.88rem; color: #64748b; line-height: 1.5; border-top: 1px solid #f1f5f9; padding-top: 8px;">Perfect for developers and analysts wanting to specialize in building next-gen intelligent applications.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with cat_tab2:
        st.markdown(
            """
            <div style="background-color: #ffffff; padding: 22px; border-radius: 14px; border: 1px solid #e2e8f0; margin-top: 10px;">
                <h4 style="color: #2563eb; margin: 0 0 10px 0; font-family: 'Plus Jakarta Sans', 'Cairo', sans-serif;">SOC Cybersecurity Track</h4>
                <p style="margin: 0 0 6px 0; font-size: 0.9rem; color: #475569;"><b>Duration:</b> 4 Months (Practical threat hunting labs)</p>
                <p style="margin: 0 0 6px 0; font-size: 0.9rem; color: #475569;"><b>Target Roles:</b> Tier 1/2 SOC Analyst, Incident Responder</p>
                <p style="margin: 0 0 12px 0; font-size: 0.9rem; color: #475569;"><b>Syllabus:</b> Networking Essentials, Linux Security, SIEM & Log Analysis (Splunk / ELK), Threat Detection, Incident Handling & Digital Forensics.</p>
                <p style="margin: 0; font-size: 0.88rem; color: #64748b; line-height: 1.5; border-top: 1px solid #f1f5f9; padding-top: 8px;">Hands-on defensive security curriculum matching industry-recognized standard practices.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with cat_tab3:
        st.markdown(
            """
            <div style="background-color: #ffffff; padding: 22px; border-radius: 14px; border: 1px solid #e2e8f0; margin-top: 10px;">
                <h4 style="color: #2563eb; margin: 0 0 10px 0; font-family: 'Plus Jakarta Sans', 'Cairo', sans-serif;">Data Science & Analytics Track</h4>
                <p style="margin: 0 0 6px 0; font-size: 0.9rem; color: #475569;"><b>Duration:</b> 4 Months (Project-based learning)</p>
                <p style="margin: 0 0 6px 0; font-size: 0.9rem; color: #475569;"><b>Key Tools:</b> SQL, Excel, Power BI, Python, Pandas, Tableau</p>
                <p style="margin: 0 0 12px 0; font-size: 0.9rem; color: #475569;"><b>Syllabus:</b> Database querying (SQL), Data Cleaning, Business Intelligence dashboards, Exploratory Data Analysis (EDA), Statistical Foundations.</p>
                <p style="margin: 0; font-size: 0.88rem; color: #64748b; line-height: 1.5; border-top: 1px solid #f1f5f9; padding-top: 8px;">Go from absolute beginner to building industry-grade corporate reports and data visualizations.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with cat_tab4:
        st.markdown(
            """
            <div style="background-color: #ffffff; padding: 22px; border-radius: 14px; border: 1px solid #e2e8f0; margin-top: 10px;">
                <h4 style="color: #2563eb; margin: 0 0 10px 0; font-family: 'Plus Jakarta Sans', 'Cairo', sans-serif;">Full-Stack Web Development</h4>
                <p style="margin: 0 0 6px 0; font-size: 0.9rem; color: #475569;"><b>Duration:</b> 5 Months (Career-launching bootcamp)</p>
                <p style="margin: 0 0 6px 0; font-size: 0.9rem; color: #475569;"><b>Stack:</b> React, Node.js, Express, MongoDB, TypeScript</p>
                <p style="margin: 0 0 12px 0; font-size: 0.9rem; color: #475569;"><b>Syllabus:</b> HTML5 & CSS3 layout architecture, JavaScript ES6, frontend states with React, REST APIs development with Node.js, database integration.</p>
                <p style="margin: 0; font-size: 0.88rem; color: #64748b; line-height: 1.5; border-top: 1px solid #f1f5f9; padding-top: 8px;">Build, secure, and deploy high-performance web applications and databases.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Premium stats dashboard (admin only)
    if is_admin():
        st.markdown("---")
        st.markdown('<h3 class="section-title">📊 System Overview</h3>', unsafe_allow_html=True)
        st.caption("Here's a quick look at how the platform is performing today. You can monitor total leads captured, check today's API usage, and verify that the knowledge base is fully synced at a glance.")

        try:
            from core.db import get_leads_collection, get_usage_logs_collection

            leads_coll = get_leads_collection()
            usage_coll = get_usage_logs_collection()

            lead_count = leads_coll.count_documents({})
            today = datetime.now().strftime("%Y-%m-%d")
            today_usage = usage_coll.count_documents({
                "timestamp": {"$gte": f"{today}T00:00:00"}
            })
            kb_status_text = "Ready ✅" if is_kb_ready() else "Not Built ⚠️"
            kb_class = "kb-ready" if is_kb_ready() else "kb-not-ready"

            # Render styled metric cards inside Streamlit columns
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">📋 Total Leads</div>
                        <div class="metric-value">{lead_count}</div>
                        <div class="metric-desc">Registered prospects in CRM</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col2:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">⚡ Today's API Calls</div>
                        <div class="metric-value">{today_usage}</div>
                        <div class="metric-desc">Usage logs since midnight</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col3:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">🗂️ KB Status</div>
                        <div class="metric-value {kb_class}">{kb_status_text}</div>
                        <div class="metric-desc">Knowledge Base synchronization</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
            # Quick Actions Section (Admin CRM Export)
            st.markdown("<br>", unsafe_allow_html=True)
            import pandas as pd
            
            leads_data = list(leads_coll.find({}, {"_id": 0}))
            if leads_data:
                # Convert ObjectIds to strings if any
                for lead in leads_data:
                    for k, v in lead.items():
                        if not isinstance(v, (str, int, float, bool, list, dict, type(None))):
                            lead[k] = str(v)
                
                df = pd.DataFrame(leads_data)
                csv = df.to_csv(index=False).encode('utf-8')
                
                st.download_button(
                    label="📥 Export Registered Leads to CSV",
                    data=csv,
                    file_name=f"kayfa_crm_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            else:
                st.caption("No CRM leads available to export")
                
        except Exception as e:
            st.caption(f"Stats/Export unavailable: {e}")
