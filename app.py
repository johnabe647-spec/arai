import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime, time
import time as time_module
from supabase import create_client as supabase_create_client
from auth import register_firm, login_user, get_firm_audits, save_audit, get_firm_stats, register_user_for_existing_firm
from report_generator import generate_audit_pdf
from email_sender import send_report_email
from team import get_invite, get_team_members, remove_team_member, create_invite
from subscription import get_firm_subscription, get_subscription_tiers, update_subscription, check_feature_access, check_feature_access_with_prompt
from recommendations import generate_recommendations, display_recommendations
from branding import get_firm_branding, update_branding, save_firm_logo, remove_logo
from analytics import display_analytics_dashboard, calculate_time_saved, calculate_cost_savings
from scheduler import create_schedule, get_schedules, display_schedules, delete_schedule
from activity_logger import log_activity, display_activity_dashboard
from api_manager import display_api_dashboard
from email_digest import display_digest_settings
from notifications import create_audit_notifications, display_notification_center
from translator import get_text, language_selector, get_theme, theme_selector
from lemonsqueezy_integration import display_payment_options, handle_checkout_success
from bank_integration import display_bank_integration_dashboard
from batch_processor import display_batch_upload_interface
from feedback import display_feedback_form, display_feedback_dashboard
from benchmarking import display_benchmark_dashboard
from usage_tracker import display_usage_dashboard, get_usage_stats
from audit_tracker import display_audit_tracker
from quality_trends import display_quality_trends_dashboard
from audit_templates import display_template_library
from two_factor_auth import display_2fa_setup, get_device_id
import plotly.express as px
import plotly.graph_objects as go

# PWA Meta Tags
st.markdown("""
<link rel="manifest" href="manifest.json">
<meta name="theme-color" content="#1f77b4">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="ARAI">
<link rel="apple-touch-icon" href="icon-192.png">
<link rel="icon" type="image/png" sizes="192x192" href="icon-192.png">
<link rel="icon" type="image/png" sizes="512x512" href="icon-512.png">
""", unsafe_allow_html=True)

# Register Service Worker for PWA
st.markdown("""
<script>
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js').then(function(registration) {
            console.log('ServiceWorker registration successful');
        }, function(err) {
            console.log('ServiceWorker registration failed: ', err);
        });
    });
}
</script>
""", unsafe_allow_html=True)

# Page config
st.set_page_config(
    page_title="ARAI - Audit Risk & AI Intelligence",
    page_icon="🔍",
    layout="wide"
)

# Initialize language in session state
if "language" not in st.session_state:
    st.session_state.language = "en"

# Initialize theme in session state
if "theme" not in st.session_state:
    st.session_state.theme = "light"

# Initialize settings tab index
if "settings_tab_index" not in st.session_state:
    st.session_state.settings_tab_index = 0

# Initialize 2FA state
if "awaiting_2fa" not in st.session_state:
    st.session_state.awaiting_2fa = False
if "temp_email" not in st.session_state:
    st.session_state.temp_email = None
if "temp_password" not in st.session_state:
    st.session_state.temp_password = None
if "remember_device" not in st.session_state:
    st.session_state.remember_device = False

# Handle checkout success
handle_checkout_success()

# Dynamic CSS based on theme
current_theme = get_theme()

if current_theme == "dark":
    css = """
    <style>
        .stApp {
            background-color: #1e1e2e;
        }
        .main-header {
            font-size: 2.5rem;
            font-weight: 700;
            color: #89b4fa;
            margin-bottom: 0;
        }
        .sub-header {
            font-size: 1.2rem;
            color: #a6adc8;
            margin-top: -10px;
            margin-bottom: 30px;
        }
        .stMarkdown, .stText, .stNumber, .stSelectbox label, .stMultiSelect label {
            color: #cdd6f4 !important;
        }
        .stButton > button {
            background-color: #89b4fa;
            color: #1e1e2e;
            border-radius: 5px;
        }
        .stButton > button:hover {
            background-color: #b4befe;
        }
        .stDataFrame {
            background-color: #181825;
        }
        .stAlert {
            background-color: #313244;
            color: #cdd6f4;
        }
        .risk-high {
            background-color: #f38ba8;
            padding: 10px;
            border-radius: 5px;
            color: #1e1e2e;
            text-align: center;
            font-weight: bold;
        }
        .risk-medium {
            background-color: #fab387;
            padding: 10px;
            border-radius: 5px;
            color: #1e1e2e;
            text-align: center;
            font-weight: bold;
        }
        .risk-low {
            background-color: #a6e3a1;
            padding: 10px;
            border-radius: 5px;
            color: #1e1e2e;
            text-align: center;
            font-weight: bold;
        }
        div[data-testid="stSidebar"] {
            background-color: #11111b;
        }
        div[data-testid="stSidebar"] * {
            color: #cdd6f4;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #313244;
            border-radius: 8px;
            padding: 8px 16px;
            color: #cdd6f4;
        }
        .stTabs [aria-selected="true"] {
            background-color: #89b4fa;
            color: #1e1e2e;
        }
        .stMetric {
            background-color: #181825;
            padding: 10px;
            border-radius: 10px;
        }
        .stMetric label {
            color: #a6adc8 !important;
        }
        .stMetric div {
            color: #89b4fa !important;
        }
        .stProgress > div > div > div > div {
            background-color: #89b4fa;
        }
        .stExpander {
            background-color: #181825;
            border-radius: 10px;
        }
        .stDataFrame {
            background-color: #181825;
        }
        .stDataFrame th {
            background-color: #313244;
            color: #cdd6f4;
        }
        .stDataFrame td {
            color: #cdd6f4;
        }
        footer {
            visibility: hidden;
        }
        .st-emotion-cache-1v0mbdj {
            background-color: #1e1e2e;
        }
        .st-emotion-cache-16txtl3 {
            background-color: #11111b;
        }
        .st-emotion-cache-1y4p8pa {
            background-color: #181825;
        }
        .st-emotion-cache-1dp5vir {
            background-color: #1e1e2e;
        }
        .stTextInput > div > div > input {
            background-color: #313244;
            color: #cdd6f4;
        }
        .stTextArea > div > div > textarea {
            background-color: #313244;
            color: #cdd6f4;
        }
        .stSelectbox > div > div {
            background-color: #313244;
            color: #cdd6f4;
        }
        .stFileUploader > div > div {
            background-color: #313244;
        }
        .stAlert {
            background-color: #313244;
            color: #cdd6f4;
        }
        .stSuccess {
            background-color: #1e3a2f;
            color: #a6e3a1;
        }
        .stWarning {
            background-color: #3a2e1e;
            color: #fab387;
        }
        .stError {
            background-color: #3a1e2e;
            color: #f38ba8;
        }
        .stInfo {
            background-color: #1e2e3a;
            color: #89b4fa;
        }
        hr {
            border-color: #45475a;
        }
    </style>
    """
else:
    css = """
    <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: 700;
            color: #1f77b4;
            margin-bottom: 0;
        }
        .sub-header {
            font-size: 1.2rem;
            color: #666;
            margin-top: -10px;
            margin-bottom: 30px;
        }
        .risk-high {
            background-color: #ff6b6b;
            padding: 10px;
            border-radius: 5px;
            color: white;
            text-align: center;
            font-weight: bold;
        }
        .risk-medium {
            background-color: #ffa500;
            padding: 10px;
            border-radius: 5px;
            color: white;
            text-align: center;
            font-weight: bold;
        }
        .risk-low {
            background-color: #4ecdc4;
            padding: 10px;
            border-radius: 5px;
            color: white;
            text-align: center;
            font-weight: bold;
        }
        .feature-yes {
            color: green;
        }
        .feature-no {
            color: #999;
        }
        .stSuccess {
            background-color: #d4edda;
            color: #155724;
        }
        .stWarning {
            background-color: #fff3cd;
            color: #856404;
        }
        .stError {
            background-color: #f8d7da;
            color: #721c24;
        }
        .stInfo {
            background-color: #d1ecf1;
            color: #0c5460;
        }
    </style>
    """

st.markdown(css, unsafe_allow_html=True)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "firm_id" not in st.session_state:
    st.session_state.firm_id = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
if "audit_results" not in st.session_state:
    st.session_state.audit_results = None

# Check for invite token in URL
query_params = st.query_params
if "invite" in query_params:
    token = query_params["invite"]
    invite, error = get_invite(token)
    
    if invite and not error:
        st.session_state.pending_invite = invite
        st.info(f"✨ {get_text('login.invite_message', invite_name=invite['firms']['name'], invite_role=invite['role'])}")

# Header
st.markdown(f'<p class="main-header">🔍 {get_text("app_name")}</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-header">{get_text("tagline")}</p>', unsafe_allow_html=True)
st.markdown("---")

# Authentication
if not st.session_state.authenticated:
    if not st.session_state.awaiting_2fa:
        tab1, tab2 = st.tabs([get_text("login.title"), get_text("login.register")])
        
        with tab1:
            with st.form("login_form"):
                st.markdown(f"### 🔐 {get_text('login.title')}")
                email = st.text_input(get_text("login.email"))
                password = st.text_input(get_text("login.password"), type="password")
                remember_device = st.checkbox("Remember this device for 30 days")
                submitted = st.form_submit_button(get_text("login.button"), width="stretch")
                
                if submitted:
                    device_id = get_device_id() if remember_device else None
                    device_name = "Trusted Device" if remember_device else None
                    
                    success, message, firm_id, role = login_user(
                        email, password,
                        two_factor_code=None,
                        device_id=device_id,
                        device_name=device_name
                    )
                    
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.firm_id = firm_id
                        st.session_state.user_email = email
                        st.session_state.user_role = role
                        log_activity(firm_id, email, "login", {"role": role})
                        st.rerun()
                    elif message == "2FA_REQUIRED":
                        st.session_state.awaiting_2fa = True
                        st.session_state.temp_email = email
                        st.session_state.temp_password = password
                        st.session_state.remember_device = remember_device
                        st.rerun()
                    else:
                        st.error(message)
        
        with tab2:
            with st.form("register_form"):
                st.markdown(f"### 📝 {get_text('login.register_title')}")
                
                if "pending_invite" in st.session_state:
                    invite = st.session_state.pending_invite
                    st.info(get_text("login.joining_firm", firm_name=invite['firms']['name'], role=invite['role']))
                    
                    firm_name = st.text_input(get_text("login.firm_name"), value=invite['firms']['name'], disabled=True)
                    email = st.text_input(get_text("login.email"), value=invite['email'], disabled=True)
                    password = st.text_input(get_text("login.password"), type="password")
                    confirm_password = st.text_input(get_text("login.confirm_password"), type="password")
                    
                    submitted = st.form_submit_button(get_text("login.join_firm"), width="stretch")
                    
                    if submitted:
                        if password != confirm_password:
                            st.error(get_text("login.password_mismatch"))
                        elif len(password) < 6:
                            st.error(get_text("login.password_length"))
                        else:
                            success, result = register_user_for_existing_firm(
                                email, password, 
                                invite['firms']['id'], 
                                invite['role'],
                                token
                            )
                            if success:
                                st.success(get_text("login.registration_success"))
                                del st.session_state.pending_invite
                                st.rerun()
                            else:
                                st.error(result)
                else:
                    firm_name = st.text_input(get_text("login.firm_name"))
                    email = st.text_input(get_text("login.email"))
                    password = st.text_input(get_text("login.password"), type="password")
                    confirm_password = st.text_input(get_text("login.confirm_password"), type="password")
                    submitted = st.form_submit_button(get_text("login.register_button"), width="stretch")
                    
                    if submitted:
                        if password != confirm_password:
                            st.error(get_text("login.password_mismatch"))
                        elif len(password) < 6:
                            st.error(get_text("login.password_length"))
                        else:
                            success, result = register_firm(firm_name, email, password)
                            if success:
                                st.success(get_text("login.registration_success"))
                            else:
                                st.error(result)
    else:
        # 2FA Verification Form
        st.markdown("### 🔐 Two-Factor Authentication Required")
        st.markdown("Please enter the verification code from your authenticator app.")
        
        code = st.text_input("Verification Code", type="password")
        is_backup = st.checkbox("This is a backup code")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Verify", key="verify_2fa"):
                device_id = get_device_id() if st.session_state.remember_device else None
                device_name = "Trusted Device" if st.session_state.remember_device else None
                
                success, message, firm_id, role = login_user(
                    st.session_state.temp_email,
                    st.session_state.temp_password,
                    two_factor_code=code,
                    is_backup_code=is_backup,
                    device_id=device_id,
                    device_name=device_name
                )
                
                if success:
                    st.session_state.authenticated = True
                    st.session_state.firm_id = firm_id
                    st.session_state.user_email = st.session_state.temp_email
                    st.session_state.user_role = role
                    st.session_state.awaiting_2fa = False
                    log_activity(firm_id, st.session_state.temp_email, "login_2fa", {"role": role})
                    st.rerun()
                else:
                    st.error(message)
        
        with col2:
            if st.button("Cancel", key="cancel_2fa"):
                st.session_state.awaiting_2fa = False
                st.rerun()

else:
    # Sidebar navigation
    with st.sidebar:
        st.markdown(f"**{get_text('login.user')}:** {st.session_state.user_email}")
        st.markdown(f"**{get_text('settings.role')}:** {st.session_state.user_role}")
        st.markdown(f"**{get_text('settings.firm_id')}:** {st.session_state.firm_id}")
        
        sub = get_firm_subscription(st.session_state.firm_id)
        st.markdown(f"**{get_text('subscription.current_plan')}:** {sub.get('subscription_tier', 'free').title()}")
        
        st.markdown("---")
        
        # Usage Dashboard
        usage_stats = display_usage_dashboard(st.session_state.firm_id)
        
        st.markdown("---")
        
        page = st.radio(get_text("navigation.title"), [
            get_text("navigation.dashboard"),
            get_text("navigation.new_audit"),
            get_text("navigation.audit_history"),
            get_text("navigation.analytics"),
            get_text("navigation.activity_log"),
            "📝 Feedback",
            get_text("navigation.settings")
        ])
        
        # Map display names back to internal names
        page_map = {
            get_text("navigation.dashboard"): "Dashboard",
            get_text("navigation.new_audit"): "New Audit",
            get_text("navigation.audit_history"): "Audit History",
            get_text("navigation.analytics"): "Analytics",
            get_text("navigation.activity_log"): "Activity Log",
            "📝 Feedback": "Feedback",
            get_text("navigation.settings"): "Settings"
        }
        st.session_state.page = page_map.get(page, "Dashboard")
        
        if st.session_state.page != "New Audit" and st.session_state.page == "New Audit":
            st.session_state.audit_results = None
        
        st.markdown("---")
        
        # Client Portal Link
        st.markdown(f"### 🔗 {get_text('client_portal.title')}")
        st.markdown(f"{get_text('client_portal.share_link')}:")
        st.code("https://arai-client-portal.streamlit.app", language="text")
        st.caption(get_text("client_portal.caption"))
        
        # Notification Center
        display_notification_center(st.session_state.firm_id, st.session_state.user_email)
        
        st.markdown("---")
        
        # Language Selector
        language_selector()
        
        # Theme Selector
        theme_selector()
        
        st.markdown("---")
        
        if st.button(get_text("login.logout")):
            log_activity(st.session_state.firm_id, st.session_state.user_email, "logout", {})
            for key in ["authenticated", "firm_id", "user_email", "user_role", "audit_results", "awaiting_2fa", "temp_email", "temp_password", "remember_device"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    # Dashboard Page
    if st.session_state.page == "Dashboard":
        st.markdown(f"### {get_text('dashboard.welcome')}")
        
        stats = get_firm_stats(st.session_state.firm_id)
        audits = get_firm_audits(st.session_state.firm_id, limit=100)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(get_text("dashboard.total_audits"), stats["total_audits"])
        col2.metric(get_text("dashboard.avg_match_rate"), f"{stats['avg_match_rate']:.1%}")
        col3.metric(get_text("dashboard.avg_fraud_risk"), f"{stats['avg_fraud_risk']:.0f}%")
        col4.metric(get_text("dashboard.time_saved"), f"{stats['total_time_saved']} {get_text('dashboard.hours')}")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"📈 {get_text('dashboard.match_rate_trend')}")
            if len(audits) >= 2:
                valid_audits = [a for a in audits if a.get('created_at')]
                if len(valid_audits) >= 2:
                    df = pd.DataFrame(valid_audits)
                    df['created_at'] = pd.to_datetime(df['created_at'])
                    df = df.sort_values('created_at')
                    
                    fig = px.line(df, x='created_at', y='match_rate', 
                                  title=get_text("dashboard.match_rate_trend"),
                                  labels={'match_rate': get_text("dashboard.match_rate"), 'created_at': get_text("dashboard.date")})
                    fig.update_traces(line_color='#1f77b4', line_width=3)
                    fig.update_layout(showlegend=False, height=300)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    if len(df) >= 3:
                        trend = get_text("dashboard.improving") if df['match_rate'].iloc[-1] > df['match_rate'].iloc[0] else get_text("dashboard.declining")
                        st.caption(f"📊 {get_text('dashboard.trend')}: {trend}")
                else:
                    st.info(get_text("dashboard.run_more_audits"))
            else:
                st.info(get_text("dashboard.run_at_least_2"))
        
        with col2:
            st.subheader(f"🎯 {get_text('dashboard.fraud_risk_distribution')}")
            if len(audits) >= 3:
                risk_levels = []
                for a in audits:
                    risk = a.get('fraud_risk', 0)
                    if risk >= 70:
                        risk_levels.append(get_text("dashboard.high"))
                    elif risk >= 40:
                        risk_levels.append(get_text("dashboard.medium"))
                    else:
                        risk_levels.append(get_text("dashboard.low"))
                
                risk_df = pd.DataFrame({'Risk Level': risk_levels})
                risk_counts = risk_df['Risk Level'].value_counts().reset_index()
                risk_counts.columns = ['Risk Level', 'Count']
                
                colors = {get_text("dashboard.high"): '#ff6b6b', get_text("dashboard.medium"): '#ffa500', get_text("dashboard.low"): '#4ecdc4'}
                fig = px.bar(risk_counts, x='Risk Level', y='Count', 
                             title=get_text("dashboard.audits_by_risk"),
                             color='Risk Level',
                             color_discrete_map=colors)
                fig.update_layout(showlegend=False, height=300)
                st.plotly_chart(fig, use_container_width=True)
                
                high_count = risk_levels.count(get_text("dashboard.high"))
                if high_count > 0:
                    st.warning(f"⚠️ {high_count} {get_text('dashboard.high_risk_audits')}")
            else:
                st.info(get_text("dashboard.run_at_least_3"))
        
        st.markdown("---")
        
        # Row 2: Advanced Analytics
        st.subheader(f"📊 {get_text('dashboard.advanced_analytics')}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"#### ⏱️ {get_text('dashboard.time_saved')}")
            if stats['total_time_saved'] > 0:
                fig = px.pie(values=[stats['total_time_saved'], max(1, 100 - stats['total_time_saved'])],
                             names=[get_text('dashboard.time_saved'), get_text('dashboard.remaining')],
                             title=f"{get_text('dashboard.total')}: {stats['total_time_saved']} {get_text('dashboard.hours')}",
                             color_discrete_sequence=['#28a745', '#e0e0e0'])
                fig.update_layout(height=250, showlegend=True)
                st.plotly_chart(fig, use_container_width=True)
                st.caption(f"💰 {get_text('dashboard.estimated_value')}: ${stats['total_time_saved'] * 50:,} ({get_text('dashboard.at_50_per_hour')})")
            else:
                st.info(get_text("dashboard.run_audits_to_see"))
        
        with col2:
            st.markdown(f"#### 📊 {get_text('dashboard.audit_quality_score')}")
            if len(audits) > 0:
                quality_scores = []
                for a in audits:
                    match = a.get('match_rate', 0)
                    fraud = a.get('fraud_risk', 0)
                    score = (match * 0.7) + ((1 - fraud/100) * 0.3)
                    quality_scores.append(score)
                
                avg_quality = sum(quality_scores) / len(quality_scores)
                
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = avg_quality * 100,
                    title = {'text': get_text("dashboard.quality_score")},
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    gauge = {
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "#1f77b4"},
                        'steps': [
                            {'range': [0, 50], 'color': "#ff6b6b"},
                            {'range': [50, 75], 'color': "#ffa500"},
                            {'range': [75, 100], 'color': "#4ecdc4"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': avg_quality * 100
                        }
                    }
                ))
                fig.update_layout(height=250)
                st.plotly_chart(fig, use_container_width=True)
                
                if avg_quality >= 0.75:
                    st.success(get_text("dashboard.excellent_quality"))
                elif avg_quality >= 0.5:
                    st.info(get_text("dashboard.good_quality"))
                else:
                    st.warning(get_text("dashboard.room_for_improvement"))
            else:
                st.info(get_text("dashboard.run_audits_to_see"))
        
        with col3:
            st.markdown(f"#### 🏆 {get_text('dashboard.performance_summary')}")
            if len(audits) > 0:
                best_audit = max(audits, key=lambda x: x.get('match_rate', 0))
                worst_audit = min(audits, key=lambda x: x.get('match_rate', 0))
                
                st.metric(get_text("dashboard.best_match_rate"), f"{best_audit.get('match_rate', 0):.1%}")
                st.caption(f"📁 {best_audit.get('filename', 'N/A')[:30]}")
                
                st.metric(get_text("dashboard.worst_match_rate"), f"{worst_audit.get('match_rate', 0):.1%}")
                st.caption(f"📁 {worst_audit.get('filename', 'N/A')[:30]}")
                
                if audits:
                    latest = audits[0]
                    fraud = latest.get('fraud_risk', 0)
                    if fraud >= 70:
                        st.error(f"🚨 {get_text('dashboard.latest_audit')}: {fraud:.0f}% {get_text('dashboard.fraud_risk')}")
                    elif fraud >= 40:
                        st.warning(f"⚠️ {get_text('dashboard.latest_audit')}: {fraud:.0f}% {get_text('dashboard.fraud_risk')}")
                    else:
                        st.success(f"✅ {get_text('dashboard.latest_audit')}: {fraud:.0f}% {get_text('dashboard.fraud_risk')}")
            else:
                st.info(get_text("dashboard.run_audits_to_see"))
        
        st.markdown("---")
        
        # Smart Recommendations
        st.subheader(f"💡 {get_text('ai_recommendations.title')}")
        
        if audits:
            latest = audits[0]
            
            sample_recommendations = [
                {
                    "category": "📊 Audit Quality",
                    "priority": "Medium",
                    "recommendation": get_text("ai_recommendations.match_rate_rec", match_rate=f"{latest.get('match_rate', 0):.1%}"),
                    "expected_impact": get_text("ai_recommendations.maintain_quality"),
                    "effort": "Low"
                },
                {
                    "category": "🚨 Risk Management",
                    "priority": "High" if latest.get('fraud_risk', 0) > 50 else "Low",
                    "recommendation": get_text("ai_recommendations.fraud_risk_rec", fraud_risk=f"{latest.get('fraud_risk', 0):.0f}%"),
                    "expected_impact": get_text("ai_recommendations.reduce_risk"),
                    "effort": "Medium"
                },
                {
                    "category": "📈 Performance",
                    "priority": "Low",
                    "recommendation": get_text("ai_recommendations.run_more_audits"),
                    "expected_impact": get_text("ai_recommendations.better_insights"),
                    "effort": "Low"
                }
            ]
            
            display_recommendations(sample_recommendations)
            st.caption(get_text("ai_recommendations.run_new_audit_for_details"))
        else:
            st.info(get_text("ai_recommendations.run_audit_for_recommendations"))
        
        st.markdown("---")
        
        # Recent Activity
        st.subheader(f"📋 {get_text('dashboard.recent_activity')}")
        
        if audits:
            recent = audits[:5]
            for audit in recent:
                if audit.get('created_at'):
                    try:
                        created = pd.to_datetime(audit['created_at']).strftime('%b %d, %Y')
                    except:
                        created = get_text("dashboard.date_unknown")
                else:
                    created = get_text("dashboard.date_unknown")
                
                match_rate = audit.get('match_rate', 0)
                fraud_risk = audit.get('fraud_risk', 0)
                
                if match_rate >= 0.95:
                    color = "🟢"
                elif match_rate >= 0.85:
                    color = "🟡"
                else:
                    color = "🔴"
                
                st.markdown(f"""
                <div style="padding: 10px; border-bottom: 1px solid #eee;">
                    <strong>{color} {audit['filename']}</strong><br>
                    📅 {created} &nbsp;|&nbsp;
                    📊 {get_text('dashboard.match_rate')}: {match_rate:.1%} &nbsp;|&nbsp;
                    ⚠️ {get_text('dashboard.fraud_risk')}: {fraud_risk:.0f}%
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(get_text("dashboard.no_audits_yet"))
        
        st.markdown("---")
        
        # Active Audits Section
        st.subheader("📊 Active Audits")
        
        supabase = supabase_create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
        active_audits = supabase.table("audit_progress").select("*, audits(filename)").eq("firm_id", st.session_state.firm_id).eq("status", "in_progress").execute()
        
        if active_audits.data:
            for audit in active_audits.data[:3]:
                col1, col2 = st.columns([3, 1])
                with col1:
                    audit_filename = audit.get('audits', {}).get('filename', 'Audit') if audit.get('audits') else 'Audit'
                    st.markdown(f"**{audit_filename}**")
                    st.progress(audit.get('progress_percentage', 0) / 100)
                with col2:
                    st.caption(f"{audit.get('progress_percentage', 0)}% complete")
                st.markdown("---")
        else:
            st.info("No active audits. Start a new audit to track progress.")
        
        st.markdown("---")
        st.markdown(f"### {get_text('dashboard.quick_actions')}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"📄 {get_text('dashboard.run_new_audit')}", width="stretch"):
                st.session_state.page = "New Audit"
                st.session_state.audit_results = None
                st.rerun()
        
        with col2:
            if st.button(f"📜 {get_text('dashboard.view_history')}", width="stretch"):
                st.session_state.page = "Audit History"
                st.rerun()
    
    # New Audit Page
    elif st.session_state.page == "New Audit":
        st.markdown(f"### 📄 {get_text('new_audit.title')}")
        
        current_sub = get_firm_subscription(st.session_state.firm_id)
        stats = get_firm_stats(st.session_state.firm_id)
        
        if current_sub.get('subscription_tier') == 'free' and stats['total_audits'] >= 10:
            st.warning(get_text("subscription.free_limit_reached"))
            st.info(get_text("subscription.upgrade_to_continue"))
            
            if st.button(get_text("subscription.view_plans")):
                st.session_state.page = "Settings"
                st.rerun()
        else:
            if st.session_state.audit_results is None:
                col1, col2 = st.columns(2)
                
                with col1:
                    bank_file = st.file_uploader(
                        get_text("new_audit.upload_bank"),
                        type=['xlsx', 'xls', 'pdf'],
                        key="bank"
                    )
                
                with col2:
                    ledger_file = st.file_uploader(
                        get_text("new_audit.upload_ledger"),
                        type=['xlsx', 'xls'],
                        key="ledger"
                    )
                
                if bank_file and ledger_file:
                    if st.button(f"🚀 {get_text('new_audit.run_audit')}", type="primary"):
                        with st.spinner(get_text("new_audit.processing")):
                            try:
                                from reconciler import reconcile
                                from anomaly_detector import detect_anomalies
                                from predictor import get_predictor
                                
                                predictor = get_predictor()
                                
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_bank:
                                    tmp_bank.write(bank_file.getvalue())
                                    bank_path = tmp_bank.name
                                
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_ledger:
                                    tmp_ledger.write(ledger_file.getvalue())
                                    ledger_path = tmp_ledger.name
                                
                                bank_filename = bank_file.name.lower()
                                
                                if bank_filename.endswith('.pdf'):
                                    if not check_feature_access(st.session_state.firm_id, "pdf_parsing"):
                                        st.error(get_text("subscription.pdf_parsing_required"))
                                        st.stop()
                                    from pdf_parser import parse_bank_statement
                                    bank_df = parse_bank_statement(bank_path)
                                else:
                                    bank_df = pd.read_excel(bank_path)
                                    bank_df.columns = [col.lower() for col in bank_df.columns]
                                    if 'amount' in bank_df.columns:
                                        bank_df['amount'] = bank_df['amount'].abs()
                                
                                ledger_df = pd.read_excel(ledger_path)
                                ledger_df.columns = [col.lower() for col in ledger_df.columns]
                                if 'amount' in ledger_df.columns:
                                    ledger_df['amount'] = ledger_df['amount'].abs()
                                
                                result = reconcile(bank_df, ledger_df)
                                anomalies = detect_anomalies(bank_df)
                                fraud_risk = predictor.predict_fraud_risk(bank_df)
                                predicted_hours = predictor.predict_audit_time(bank_df)
                                problem_areas = predictor.predict_problem_areas(bank_df)
                                resources = predictor.suggest_resource_allocation(fraud_risk, predicted_hours, problem_areas)
                                
                                st.session_state.audit_results = {
                                    'result': result,
                                    'anomalies': anomalies,
                                    'fraud_risk': fraud_risk,
                                    'predicted_hours': predicted_hours,
                                    'problem_areas': problem_areas,
                                    'resources': resources,
                                    'bank_filename': bank_file.name
                                }
                                
                                audit_data_summary = {
                                    "match_rate": result['summary']['match_rate'],
                                    "matched": result['summary']['matched'],
                                    "unmatched_bank": result['summary']['unmatched_bank'],
                                    "unmatched_ledger": result['summary']['unmatched_ledger'],
                                    "anomalies": len(anomalies),
                                    "problem_areas": problem_areas
                                }
                                
                                # Save audit and get the ID
                                audit_result = save_audit(
                                    firm_id=st.session_state.firm_id,
                                    filename=bank_file.name,
                                    match_rate=result['summary']['match_rate'],
                                    fraud_risk=fraud_risk,
                                    predicted_hours=predicted_hours,
                                    audit_data=audit_data_summary
                                )
                                
                                log_activity(st.session_state.firm_id, st.session_state.user_email, "run_audit", {
                                    "filename": bank_file.name,
                                    "match_rate": result['summary']['match_rate'],
                                    "transaction_count": len(bank_df)
                                })
                                
                                create_audit_notifications(
                                    firm_id=st.session_state.firm_id,
                                    filename=bank_file.name,
                                    match_rate=result['summary']['match_rate'],
                                    anomaly_count=len(anomalies),
                                    fraud_risk=fraud_risk
                                )
                                
                                os.unlink(bank_path)
                                os.unlink(ledger_path)
                                
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"Error: {e}")
            
            if st.session_state.audit_results is not None:
                results = st.session_state.audit_results
                result = results['result']
                anomalies = results['anomalies']
                fraud_risk = results['fraud_risk']
                predicted_hours = results['predicted_hours']
                problem_areas = results['problem_areas']
                resources = results['resources']
                
                st.success(get_text("new_audit.audit_complete", match_rate=f"{result['summary']['match_rate']:.1%}"))
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric(get_text("new_audit.matched"), result['summary']['matched'])
                col2.metric(get_text("new_audit.unmatched_bank"), result['summary']['unmatched_bank'])
                col3.metric(get_text("new_audit.unmatched_ledger"), result['summary']['unmatched_ledger'])
                col4.metric(get_text("new_audit.fraud_risk"), f"{fraud_risk:.0f}%")
                
                st.markdown("---")
                st.subheader(f"🤖 {get_text('ai_predictions.title')}")
                
                if fraud_risk >= 70:
                    st.markdown(f'<div class="risk-high">🔴 {get_text("ai_predictions.high_risk")}: {fraud_risk:.0f}% {get_text("ai_predictions.fraud_probability")}</div>', unsafe_allow_html=True)
                elif fraud_risk >= 40:
                    st.markdown(f'<div class="risk-medium">🟡 {get_text("ai_predictions.medium_risk")}: {fraud_risk:.0f}% {get_text("ai_predictions.fraud_probability")}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="risk-low">🟢 {get_text("ai_predictions.low_risk")}: {fraud_risk:.0f}% {get_text("ai_predictions.fraud_probability")}</div>', unsafe_allow_html=True)
                
                st.metric(f"{get_text('ai_predictions.predicted_time')}", f"{predicted_hours:.1f} {get_text('ai_predictions.hours')}")
                
                st.markdown("---")
                st.subheader(f"🎯 {get_text('problem_areas.title')}")
                for area, risk in list(problem_areas.items())[:4]:
                    st.progress(risk/100)
                    area_name = get_text(f"problem_areas.{area.lower().replace(' ', '_')}", default=area)
                    st.write(f"**{area_name}** - {risk:.0f}% {get_text('problem_areas.risk')}")
                
                st.markdown("---")
                st.subheader(f"👥 {get_text('resource_allocation.title')}")
                for rec in resources[:3]:
                    assigned_to = get_text(f"resource_allocation.{rec['assigned_to'].lower().replace(' ', '_')}", default=rec['assigned_to'])
                    st.info(f"**{rec['area']}** → {get_text('resource_allocation.assign_to')}: {assigned_to}")
                
                if not anomalies.empty:
                    st.markdown("---")
                    st.subheader(f"🚨 {get_text('anomalies.title')}")
                    st.dataframe(anomalies[['date', 'amount', 'description', 'risk_level']].head(5))
                
                tab1, tab2 = st.tabs([get_text("new_audit.unmatched_bank"), get_text("new_audit.unmatched_ledger")])
                with tab1:
                    if not result['unmatched_bank'].empty:
                        st.dataframe(result['unmatched_bank'][['date', 'amount', 'description']])
                    else:
                        st.success(f"✅ {get_text('new_audit.all_bank_matched')}")
                
                with tab2:
                    if not result['unmatched_ledger'].empty:
                        st.dataframe(result['unmatched_ledger'][['date', 'amount', 'description']])
                    else:
                        st.success(f"✅ {get_text('new_audit.all_ledger_matched')}")
                
                if check_feature_access(st.session_state.firm_id, "email_reports"):
                    st.markdown("---")
                    st.subheader(f"📧 {get_text('email_report.title')}")
                    
                    with st.form(key="email_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            client_email = st.text_input(get_text("email_report.client_email"), placeholder="client@company.com")
                        with col2:
                            client_name = st.text_input(get_text("email_report.client_name"), placeholder="Client Company Name")
                        
                        send_button = st.form_submit_button(f"📧 {get_text('email_report.send_button')}", type="secondary")
                        
                        if send_button:
                            if client_email and client_name:
                                with st.spinner(get_text("email_report.sending")):
                                    branding = get_firm_branding(st.session_state.firm_id)
                                    
                                    pdf_path = f"temp_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                                    
                                    audit_summary = {
                                        "match_rate": result['summary']['match_rate'],
                                        "matched": result['summary']['matched'],
                                        "unmatched_bank": result['summary']['unmatched_bank'],
                                        "unmatched_ledger": result['summary']['unmatched_ledger'],
                                        "anomalies": len(anomalies),
                                        "fraud_risk": fraud_risk,
                                        "problem_areas": problem_areas
                                    }
                                    
                                    generate_audit_pdf(
                                        firm_name=st.session_state.user_email.split('@')[0],
                                        client_name=client_name,
                                        audit_data=audit_summary,
                                        output_path=pdf_path,
                                        branding=branding
                                    )
                                    
                                    success, message = send_report_email(
                                        recipient_email=client_email,
                                        recipient_name=client_name,
                                        firm_name=st.session_state.user_email.split('@')[0],
                                        pdf_path=pdf_path,
                                        audit_summary=audit_summary
                                    )
                                    
                                    os.unlink(pdf_path)
                                    
                                    if success:
                                        st.success(get_text("email_report.success", email=client_email))
                                        log_activity(st.session_state.firm_id, st.session_state.user_email, "send_report", {
                                            "recipient": client_email,
                                            "client_name": client_name
                                        })
                                    else:
                                        st.error(get_text("email_report.error", error=message))
                            else:
                                st.warning(get_text("email_report.warning"))
                else:
                    st.info(get_text("subscription.email_reports_required"))
                
                # Audit Tracker
                st.markdown("---")
                filename = st.session_state.audit_results.get('bank_filename', 'Audit')
                supabase = supabase_create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
                audit_record = supabase.table("audits").select("id").eq("filename", filename).eq("firm_id", st.session_state.firm_id).order("created_at", desc=True).limit(1).execute()
                audit_id = audit_record.data[0]["id"] if audit_record.data else None
                
                if audit_id:
                    display_audit_tracker(
                        audit_id=audit_id,
                        firm_id=st.session_state.firm_id,
                        audit_name=filename,
                        estimated_hours=predicted_hours
                    )
                
                recommendations = generate_recommendations(
                    audit_data=result,
                    anomalies=anomalies,
                    fraud_risk=fraud_risk,
                    problem_areas=problem_areas,
                    match_rate=result['summary']['match_rate']
                )
                
                display_recommendations(recommendations)
                
                if st.button(f"📋 {get_text('recommendations.export_checklist')}"):
                    checklist = []
                    for rec in recommendations:
                        checklist.append(f"□ [{rec['priority']}] {rec['category']}: {rec['recommendation']}")
                    checklist_text = "\n\n".join(checklist)
                    st.code(checklist_text, language="text")
                    st.caption(get_text("recommendations.copy_checklist"))
                
                if st.button(f"🔄 {get_text('new_audit.run_another')}", type="primary"):
                    st.session_state.audit_results = None
                    st.rerun()
    
    # Audit History Page
    elif st.session_state.page == "Audit History":
        st.markdown(f"### 📜 {get_text('navigation.audit_history')}")
        
        audits = get_firm_audits(st.session_state.firm_id)
        
        if audits:
            df = pd.DataFrame(audits)
            df_display = df[['filename', 'match_rate', 'fraud_risk', 'predicted_hours', 'created_at']]
            df_display.columns = [get_text("audit_history.filename"), get_text("audit_history.match_rate"), 
                                  get_text("audit_history.fraud_risk"), get_text("audit_history.predicted_hours"), 
                                  get_text("audit_history.date")]
            st.dataframe(df_display, use_container_width=True)
        else:
            st.info(get_text("audit_history.no_audits"))
    
    # Analytics Page
    elif st.session_state.page == "Analytics":
        st.markdown(f"### 📊 {get_text('navigation.analytics')}")
        
        audits = get_firm_audits(st.session_state.firm_id, limit=500)
        stats = get_firm_stats(st.session_state.firm_id)
        
        display_analytics_dashboard(audits, st.session_state.user_email.split('@')[0])
        
        st.markdown("---")
        st.subheader(f"📅 {get_text('scheduled_reports.title')}")
        
        schedules = get_schedules(st.session_state.firm_id)
        
        if schedules:
            st.markdown(f"#### {get_text('scheduled_reports.your_schedules')}")
            display_schedules(schedules)
        
        with st.expander(f"➕ {get_text('scheduled_reports.create_new')}"):
            with st.form("schedule_form"):
                schedule_name = st.text_input(get_text("scheduled_reports.schedule_name"), placeholder="Monthly Client Report")
                
                col1, col2 = st.columns(2)
                with col1:
                    frequency = st.selectbox(get_text("scheduled_reports.frequency"), ["daily", "weekly", "monthly"])
                with col2:
                    schedule_time = st.time_input(get_text("scheduled_reports.time"), value=time(9, 0))
                
                schedule_day = None
                if frequency == "weekly":
                    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                    day_name = st.selectbox(get_text("scheduled_reports.day_of_week"), days)
                    schedule_day = days.index(day_name)
                elif frequency == "monthly":
                    schedule_day = st.number_input(get_text("scheduled_reports.day_of_month"), min_value=1, max_value=28, value=1)
                
                recipient_emails = st.text_area(get_text("scheduled_reports.recipient_emails"), placeholder="client@company.com\nmanager@firm.com", 
                                                help=get_text("scheduled_reports.emails_help"))
                
                client_name = st.text_input(get_text("scheduled_reports.client_name_optional"), placeholder="Client Company Name")
                
                submitted = st.form_submit_button(get_text("scheduled_reports.create_button"))
                
                if submitted and schedule_name and recipient_emails:
                    emails_list = [e.strip() for e in recipient_emails.split('\n') if e.strip()]
                    success, result = create_schedule(
                        st.session_state.firm_id,
                        schedule_name,
                        frequency,
                        schedule_time,
                        emails_list,
                        client_name if client_name else None,
                        schedule_day
                    )
                    if success:
                        st.success(get_text("scheduled_reports.schedule_created", name=schedule_name))
                        log_activity(st.session_state.firm_id, st.session_state.user_email, "create_schedule", {
                            "schedule_name": schedule_name,
                            "frequency": frequency
                        })
                        st.rerun()
                    else:
                        st.error(f"Error: {result}")
        
        # Batch Processing
        st.markdown("---")
        display_batch_upload_interface(st.session_state.firm_id, st.session_state.user_email)
        
        # Benchmarking
        st.markdown("---")
        display_benchmark_dashboard(st.session_state.firm_id, stats, audits)
        
        # Quality Trends
        st.markdown("---")
        display_quality_trends_dashboard(audits, st.session_state.user_email.split('@')[0])
        
        # Template Library
        st.markdown("---")
        display_template_library(st.session_state.firm_id)
    
    # Activity Log Page
    elif st.session_state.page == "Activity Log":
        st.markdown(f"### 📋 {get_text('navigation.activity_log')}")
        
        if check_feature_access(st.session_state.firm_id, "activity_log"):
            display_activity_dashboard(st.session_state.firm_id)
        else:
            st.info(get_text("subscription.activity_logging_required"))
            st.markdown("**Features include:**")
            st.markdown(f"- {get_text('subscription.track_user_actions')}")
            st.markdown(f"- {get_text('subscription.usage_analytics')}")
            st.markdown(f"- {get_text('subscription.export_logs')}")
            st.markdown(f"- {get_text('subscription.audit_trail')}")
            
            if st.button(get_text("subscription.upgrade_to_unlock"), key="upgrade_activity"):
                st.session_state.page = "Settings"
                st.rerun()
    
    # Feedback Page
    elif st.session_state.page == "Feedback":
        st.markdown("### 📝 Client Feedback")
        
        tab1, tab2 = st.tabs(["Submit Feedback", "Analytics Dashboard"])
        
        with tab1:
            display_feedback_form()
        
        with tab2:
            display_feedback_dashboard(st.session_state.firm_id)
    
    # Settings Page
    elif st.session_state.page == "Settings":
        st.markdown(f"### ⚙️ {get_text('settings.title')}")
        
        # Define tab names
        tab_names = [
            get_text("settings.team_management"),
            get_text("settings.firm_settings"),
            get_text("settings.subscription"),
            get_text("settings.branding"),
            get_text("settings.api"),
            "🏦 Bank Integration"
        ]
        
        # Create tabs
        tabs = st.tabs(tab_names)
        
        # Team Management Tab (index 0)
        with tabs[0]:
            st.markdown(f"#### 👥 {get_text('settings.team_management')}")
            
            if check_feature_access(st.session_state.firm_id, "team_members"):
                if st.session_state.user_role == "owner":
                    team_members = get_team_members(st.session_state.firm_id)
                    
                    if team_members:
                        st.markdown(f"**{get_text('settings.current_team')}:**")
                        for member in team_members:
                            col1, col2, col3 = st.columns([2, 2, 1])
                            with col1:
                                st.write(member["email"])
                            with col2:
                                st.write(f"{get_text('settings.role')}: {member['role']}")
                            with col3:
                                if member["role"] != "owner":
                                    if st.button(get_text("settings.remove"), key=f"remove_{member['id']}"):
                                        success, message = remove_team_member(
                                            member["id"], 
                                            st.session_state.firm_id,
                                            st.session_state.user_role
                                        )
                                        if success:
                                            st.success(message)
                                            log_activity(st.session_state.firm_id, st.session_state.user_email, "remove_team_member", {
                                                "removed_email": member["email"]
                                            })
                                            st.rerun()
                                        else:
                                            st.error(message)
                    
                    st.markdown("---")
                    st.markdown(f"#### ✉️ {get_text('settings.invite_new_member')}")
                    
                    with st.form("invite_form"):
                        invite_email = st.text_input(get_text("settings.email"), placeholder="colleague@firm.com")
                        invite_role = st.selectbox(get_text("settings.role"), ["staff", "manager"])
                        submitted = st.form_submit_button(get_text("settings.generate_link"))
                        
                        if submitted and invite_email:
                            success, invite_url, result = create_invite(
                                st.session_state.firm_id,
                                invite_email,
                                invite_role
                            )
                            if success:
                                st.success(get_text("settings.invite_link_generated"))
                                st.code(invite_url, language="text")
                                st.caption(get_text("settings.invite_link_expires"))
                                log_activity(st.session_state.firm_id, st.session_state.user_email, "create_invite", {
                                    "invite_email": invite_email,
                                    "role": invite_role
                                })
                            else:
                                st.error(f"Failed to create invite: {result}")
                else:
                    st.info(get_text("settings.team_management_owner_only"))
                    team_members = get_team_members(st.session_state.firm_id)
                    if team_members:
                        st.markdown(f"**{get_text('settings.your_team')}:**")
                        for member in team_members:
                            st.write(f"- {member['email']} ({member['role']})")
            else:
                st.info(get_text("subscription.team_management_required"))
                if st.button(get_text("subscription.view_plans"), key="upgrade_team"):
                    st.session_state.page = "Settings"
                    st.rerun()
        
        # Firm Settings Tab (index 1)
        with tabs[1]:
            st.markdown(f"#### 🏢 {get_text('settings.firm_settings')}")
            display_digest_settings(st.session_state.firm_id)
            
            # 2FA Settings Section
            st.markdown("---")
            display_2fa_setup(st.session_state.firm_id, st.session_state.user_email)
            
            st.markdown("---")
            st.info(get_text("settings.coming_soon"))
            st.caption(f"{get_text('settings.firm_id')}: {st.session_state.firm_id}")
        
        # Subscription Tab (index 2)
        with tabs[2]:
            display_payment_options(st.session_state.firm_id, st.session_state.user_email)
        
        # Branding Tab (index 3)
        with tabs[3]:
            st.markdown(f"#### 🎨 {get_text('settings.branding')}")
            
            if check_feature_access(st.session_state.firm_id, "custom_branding"):
                branding = get_firm_branding(st.session_state.firm_id)
                
                st.markdown(get_text("branding.customize_reports"))
                
                st.markdown(f"**{get_text('branding.logo_upload')}**")
                st.caption(get_text("branding.logo_help"))
                
                col1, col2 = st.columns(2)
                
                with col1:
                    logo_file = st.file_uploader(get_text("branding.choose_logo"), type=['png', 'jpg', 'jpeg'], key="logo_upload")
                    if logo_file:
                        if st.button(get_text("branding.upload_logo"), key="btn_upload_logo"):
                            success, result = save_firm_logo(st.session_state.firm_id, logo_file)
                            if success:
                                st.success(get_text("branding.logo_uploaded"))
                                log_activity(st.session_state.firm_id, st.session_state.user_email, "upload_logo", {})
                                st.rerun()
                            else:
                                st.error(f"Error: {result}")
                
                with col2:
                    if branding.get('logo_url'):
                        st.image(branding['logo_url'], width=100)
                        if st.button(get_text("branding.remove_logo"), key="btn_remove_logo"):
                            remove_logo(st.session_state.firm_id)
                            st.success(get_text("branding.logo_removed"))
                            st.rerun()
                
                st.markdown("---")
                
                st.markdown(f"**{get_text('branding.brand_colors')}**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    primary_color = st.color_picker(get_text("branding.primary_color"), branding.get('primary_color', '#1f77b4'), key="primary_color_picker")
                    st.caption(get_text("branding.primary_color_help"))
                
                with col2:
                    secondary_color = st.color_picker(get_text("branding.secondary_color"), branding.get('secondary_color', '#4ecdc4'), key="secondary_color_picker")
                    st.caption(get_text("branding.secondary_color_help"))
                
                if st.button(get_text("branding.save_colors"), key="btn_save_colors"):
                    update_branding(
                        st.session_state.firm_id,
                        primary_color=primary_color,
                        secondary_color=secondary_color
                    )
                    st.success(get_text("branding.colors_saved"))
                    log_activity(st.session_state.firm_id, st.session_state.user_email, "update_branding", {
                        "primary_color": primary_color,
                        "secondary_color": secondary_color
                    })
                    st.rerun()
                
                st.markdown("---")
                
                st.markdown(f"**{get_text('branding.custom_footer')}**")
                footer_text = st.text_area(get_text("branding.footer_text"), branding.get('footer_text', ''), 
                                           placeholder=get_text("branding.footer_placeholder"),
                                           help=get_text("branding.footer_help"),
                                           key="footer_text_area")
                
                if st.button(get_text("branding.save_footer"), key="btn_save_footer"):
                    update_branding(
                        st.session_state.firm_id,
                        footer_text=footer_text
                    )
                    st.success(get_text("branding.footer_saved"))
                    log_activity(st.session_state.firm_id, st.session_state.user_email, "update_footer", {})
                    st.rerun()
                
                st.markdown("---")
                st.info(get_text("branding.enterprise_branding_info"))
            else:
                st.info(get_text("branding.custom_branding_required"))
                st.markdown("**Features include:**")
                st.markdown(f"- {get_text('branding.your_logo')}")
                st.markdown(f"- {get_text('branding.custom_colors')}")
                st.markdown(f"- {get_text('branding.custom_footer')}")
                st.markdown(f"- {get_text('branding.white_label')}")
                
                if st.button(get_text("subscription.upgrade_to_enterprise"), key="upgrade_branding"):
                    st.session_state.page = "Settings"
                    st.rerun()
        
        # API Tab (index 4)
        with tabs[4]:
            if check_feature_access(st.session_state.firm_id, "api_access"):
                display_api_dashboard(st.session_state.firm_id)
            else:
                st.info(get_text("subscription.api_access_required"))
                st.markdown("**Features include:**")
                st.markdown(f"- {get_text('api.rest_api')}")
                st.markdown(f"- {get_text('api.webhooks')}")
                st.markdown(f"- {get_text('api.api_keys')}")
                st.markdown(f"- {get_text('api.usage_analytics')}")
                st.markdown(f"- {get_text('api.dedicated_support')}")
                
                if st.button(get_text("subscription.upgrade_to_enterprise"), key="upgrade_api"):
                    st.session_state.page = "Settings"
                    st.rerun()
        
        # Bank Integration Tab (index 5)
        with tabs[5]:
            display_bank_integration_dashboard(st.session_state.firm_id, st.session_state.user_role)
        
        # Set the active tab based on session state
        if st.session_state.settings_tab_index != 0:
            st.components.v1.html(f"""
                <script>
                    const tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
                    if (tabs[{st.session_state.settings_tab_index}]) {{
                        tabs[{st.session_state.settings_tab_index}].click();
                    }}
                </script>
            """, height=0)
            st.session_state.settings_tab_index = 0
    
    st.markdown("---")
    st.caption(get_text("footer.copyright"))