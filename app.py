import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime
from supabase import create_client as supabase_create_client
from auth import register_firm, login_user, get_firm_audits, save_audit, get_firm_stats, register_user_for_existing_firm
from report_generator import generate_audit_pdf
from email_sender import send_report_email
from team import get_invite, get_team_members, remove_team_member, create_invite
from subscription import get_firm_subscription, get_subscription_tiers, update_subscription, check_feature_access
from recommendations import generate_recommendations, display_recommendations
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="ARAI - Audit Risk & AI Intelligence",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS
st.markdown("""
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
</style>
""", unsafe_allow_html=True)

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
        st.info(f"✨ You've been invited to join **{invite['firms']['name']}** as a **{invite['role']}**. Please register below.")

# Header
st.markdown('<p class="main-header">🔍 ARAI</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Audit Risk & AI Intelligence | Client Portal</p>', unsafe_allow_html=True)
st.markdown("---")

# Authentication
if not st.session_state.authenticated:
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            st.markdown("### 🔐 Login")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", width="stretch")
            
            if submitted:
                success, message, firm_id, role = login_user(email, password)
                if success:
                    st.session_state.authenticated = True
                    st.session_state.firm_id = firm_id
                    st.session_state.user_email = email
                    st.session_state.user_role = role
                    st.rerun()
                else:
                    st.error(message)
    
    with tab2:
        with st.form("register_form"):
            st.markdown("### 📝 Register")
            
            if "pending_invite" in st.session_state:
                invite = st.session_state.pending_invite
                st.info(f"You are joining: **{invite['firms']['name']}** as a **{invite['role']}**")
                
                firm_name = st.text_input("Firm Name", value=invite['firms']['name'], disabled=True)
                email = st.text_input("Email", value=invite['email'], disabled=True)
                password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                
                submitted = st.form_submit_button("Join Firm", width="stretch")
                
                if submitted:
                    if password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        success, result = register_user_for_existing_firm(
                            email, password, 
                            invite['firms']['id'], 
                            invite['role'],
                            token
                        )
                        if success:
                            st.success("Registration successful! Please login.")
                            del st.session_state.pending_invite
                            st.rerun()
                        else:
                            st.error(result)
            else:
                firm_name = st.text_input("Firm Name")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                submitted = st.form_submit_button("Register Firm", width="stretch")
                
                if submitted:
                    if password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        success, result = register_firm(firm_name, email, password)
                        if success:
                            st.success("Registration successful! Please login.")
                        else:
                            st.error(result)

else:
    # Sidebar navigation
    with st.sidebar:
        st.markdown(f"**User:** {st.session_state.user_email}")
        st.markdown(f"**Role:** {st.session_state.user_role}")
        st.markdown(f"**Firm ID:** {st.session_state.firm_id}")
        
        # Show subscription tier in sidebar
        sub = get_firm_subscription(st.session_state.firm_id)
        st.markdown(f"**Plan:** {sub.get('subscription_tier', 'free').title()}")
        
        st.markdown("---")
        
        page = st.radio("Navigation", ["Dashboard", "New Audit", "Audit History", "Settings"])
        
        if page != "New Audit" and st.session_state.page == "New Audit":
            st.session_state.audit_results = None
        
        st.session_state.page = page
        
        st.markdown("---")
        
        # Client Portal Link
        st.markdown("### 🔗 Client Portal")
        st.markdown("Share this link with your clients:")
        st.code("https://arai-client-portal.streamlit.app", language="text")
        st.caption("Clients can view their audit reports here")
        
        st.markdown("---")
        
        if st.button("Logout"):
            for key in ["authenticated", "firm_id", "user_email", "user_role", "audit_results"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    # Dashboard Page
    if st.session_state.page == "Dashboard":
        st.markdown(f"### Welcome to ARAI")
        
        # Get firm statistics
        stats = get_firm_stats(st.session_state.firm_id)
        audits = get_firm_audits(st.session_state.firm_id, limit=100)
        
        # Top metrics row
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Audits", stats["total_audits"])
        col2.metric("Avg Match Rate", f"{stats['avg_match_rate']:.1%}")
        col3.metric("Avg Fraud Risk", f"{stats['avg_fraud_risk']:.0f}%")
        col4.metric("Time Saved", f"{stats['total_time_saved']} hours")
        
        st.markdown("---")
        
        # Row 1: Main Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Match Rate Trend")
            if len(audits) >= 2:
                valid_audits = [a for a in audits if a.get('created_at')]
                if len(valid_audits) >= 2:
                    df = pd.DataFrame(valid_audits)
                    df['created_at'] = pd.to_datetime(df['created_at'])
                    df = df.sort_values('created_at')
                    
                    fig = px.line(df, x='created_at', y='match_rate', 
                                  title='Match Rate Over Time',
                                  labels={'match_rate': 'Match Rate', 'created_at': 'Date'})
                    fig.update_traces(line_color='#1f77b4', line_width=3)
                    fig.update_layout(showlegend=False, height=300)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    if len(df) >= 3:
                        st.caption("📊 Trend: " + ("Improving 📈" if df['match_rate'].iloc[-1] > df['match_rate'].iloc[0] else "Declining 📉"))
                else:
                    st.info("Run more audits to see trend data")
            else:
                st.info("Run at least 2 audits to see trend data")
        
        with col2:
            st.subheader("🎯 Fraud Risk Distribution")
            if len(audits) >= 3:
                risk_levels = []
                for a in audits:
                    risk = a.get('fraud_risk', 0)
                    if risk >= 70:
                        risk_levels.append('High')
                    elif risk >= 40:
                        risk_levels.append('Medium')
                    else:
                        risk_levels.append('Low')
                
                risk_df = pd.DataFrame({'Risk Level': risk_levels})
                risk_counts = risk_df['Risk Level'].value_counts().reset_index()
                risk_counts.columns = ['Risk Level', 'Count']
                
                colors = {'High': '#ff6b6b', 'Medium': '#ffa500', 'Low': '#4ecdc4'}
                fig = px.bar(risk_counts, x='Risk Level', y='Count', 
                             title='Audits by Risk Level',
                             color='Risk Level',
                             color_discrete_map=colors)
                fig.update_layout(showlegend=False, height=300)
                st.plotly_chart(fig, use_container_width=True)
                
                high_count = risk_levels.count('High')
                if high_count > 0:
                    st.warning(f"⚠️ {high_count} high-risk audits detected")
            else:
                st.info("Run at least 3 audits to see risk distribution")
        
        st.markdown("---")
        
        # Row 2: Advanced Analytics
        st.subheader("📊 Advanced Analytics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### ⏱️ Time Saved")
            if stats['total_time_saved'] > 0:
                fig = px.pie(values=[stats['total_time_saved'], max(1, 100 - stats['total_time_saved'])],
                             names=['Time Saved', 'Remaining'],
                             title=f"Total: {stats['total_time_saved']} hours",
                             color_discrete_sequence=['#28a745', '#e0e0e0'])
                fig.update_layout(height=250, showlegend=True)
                st.plotly_chart(fig, use_container_width=True)
                st.caption(f"💰 Estimated value: ${stats['total_time_saved'] * 50:,} (at $50/hour)")
            else:
                st.info("Run audits to see time saved")
        
        with col2:
            st.markdown("#### 📊 Audit Quality Score")
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
                    title = {'text': "Quality Score"},
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
                    st.success("Excellent audit quality")
                elif avg_quality >= 0.5:
                    st.info("Good audit quality")
                else:
                    st.warning("Room for improvement")
            else:
                st.info("Run audits to see quality score")
        
        with col3:
            st.markdown("#### 🏆 Performance Summary")
            if len(audits) > 0:
                best_audit = max(audits, key=lambda x: x.get('match_rate', 0))
                worst_audit = min(audits, key=lambda x: x.get('match_rate', 0))
                
                st.metric("Best Match Rate", f"{best_audit.get('match_rate', 0):.1%}")
                st.caption(f"📁 {best_audit.get('filename', 'N/A')[:30]}")
                
                st.metric("Worst Match Rate", f"{worst_audit.get('match_rate', 0):.1%}")
                st.caption(f"📁 {worst_audit.get('filename', 'N/A')[:30]}")
                
                if audits:
                    latest = audits[0]
                    fraud = latest.get('fraud_risk', 0)
                    if fraud >= 70:
                        st.error(f"🚨 Latest audit: {fraud:.0f}% fraud risk")
                    elif fraud >= 40:
                        st.warning(f"⚠️ Latest audit: {fraud:.0f}% fraud risk")
                    else:
                        st.success(f"✅ Latest audit: {fraud:.0f}% fraud risk")
            else:
                st.info("Run audits to see summary")
        
        st.markdown("---")
        
        # Smart Recommendations on Dashboard
        st.subheader("💡 Smart Recommendations")
        
        if audits:
            latest = audits[0]
            
            sample_recommendations = [
                {
                    "category": "📊 Audit Quality",
                    "priority": "Medium",
                    "recommendation": f"Your match rate is {latest.get('match_rate', 0):.1%}. Continue monitoring for consistency.",
                    "expected_impact": "Maintain quality standards",
                    "effort": "Low"
                },
                {
                    "category": "🚨 Risk Management",
                    "priority": "High" if latest.get('fraud_risk', 0) > 50 else "Low",
                    "recommendation": f"Fraud risk is {latest.get('fraud_risk', 0):.0f}%. {'Review controls immediately' if latest.get('fraud_risk', 0) > 50 else 'Current controls appear adequate'}.",
                    "expected_impact": "Reduce risk exposure",
                    "effort": "Medium"
                },
                {
                    "category": "📈 Performance",
                    "priority": "Low",
                    "recommendation": "Run more audits to get personalized recommendations based on your specific results.",
                    "expected_impact": "Better insights",
                    "effort": "Low"
                }
            ]
            
            display_recommendations(sample_recommendations)
            st.caption("Run a new audit to get detailed recommendations based on your specific results")
        else:
            st.info("Run an audit to get personalized recommendations")
        
        st.markdown("---")
        
        # Recent Activity
        st.subheader("📋 Recent Activity")
        
        if audits:
            recent = audits[:5]
            for audit in recent:
                if audit.get('created_at'):
                    try:
                        created = pd.to_datetime(audit['created_at']).strftime('%b %d, %Y')
                    except:
                        created = "Date unknown"
                else:
                    created = "Date unknown"
                
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
                    📊 Match Rate: {match_rate:.1%} &nbsp;|&nbsp;
                    ⚠️ Fraud Risk: {fraud_risk:.0f}%
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No audits yet. Run your first audit!")
        
        st.markdown("---")
        st.markdown("### Quick Actions")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📄 Run New Audit", width="stretch"):
                st.session_state.page = "New Audit"
                st.session_state.audit_results = None
                st.rerun()
        
        with col2:
            if st.button("📜 View Audit History", width="stretch"):
                st.session_state.page = "Audit History"
                st.rerun()
    
    # New Audit Page
    elif st.session_state.page == "New Audit":
        st.markdown("### 📄 New Audit")
        
        # Check subscription for audit limits
        current_sub = get_firm_subscription(st.session_state.firm_id)
        stats = get_firm_stats(st.session_state.firm_id)
        
        if current_sub.get('subscription_tier') == 'free' and stats['total_audits'] >= 10:
            st.warning("You have reached the free plan limit of 10 audits. Please upgrade to continue.")
            st.info("Go to Settings → Subscription to upgrade your plan.")
            
            if st.button("View Subscription Plans"):
                st.session_state.page = "Settings"
                st.rerun()
        else:
            if st.session_state.audit_results is None:
                col1, col2 = st.columns(2)
                
                with col1:
                    bank_file = st.file_uploader(
                        "Bank Statement (Excel or PDF)",
                        type=['xlsx', 'xls', 'pdf'],
                        key="bank"
                    )
                
                with col2:
                    ledger_file = st.file_uploader(
                        "Ledger (Excel only)",
                        type=['xlsx', 'xls'],
                        key="ledger"
                    )
                
                if bank_file and ledger_file:
                    if st.button("🚀 Run Audit", type="primary"):
                        with st.spinner("Running AI-powered audit..."):
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
                                        st.error("PDF parsing is only available on Professional and Enterprise plans. Please upgrade.")
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
                                
                                save_audit(
                                    firm_id=st.session_state.firm_id,
                                    filename=bank_file.name,
                                    match_rate=result['summary']['match_rate'],
                                    fraud_risk=fraud_risk,
                                    predicted_hours=predicted_hours,
                                    audit_data=audit_data_summary
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
                
                st.success(f"✅ Audit complete! Match rate: {result['summary']['match_rate']:.1%}")
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Matched", result['summary']['matched'])
                col2.metric("Unmatched Bank", result['summary']['unmatched_bank'])
                col3.metric("Unmatched Ledger", result['summary']['unmatched_ledger'])
                col4.metric("Fraud Risk", f"{fraud_risk:.0f}%")
                
                st.markdown("---")
                st.subheader("🤖 AI Predictions")
                
                if fraud_risk >= 70:
                    st.markdown(f'<div class="risk-high">🔴 HIGH RISK: {fraud_risk:.0f}% fraud probability</div>', unsafe_allow_html=True)
                elif fraud_risk >= 40:
                    st.markdown(f'<div class="risk-medium">🟡 MEDIUM RISK: {fraud_risk:.0f}% fraud probability</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="risk-low">🟢 LOW RISK: {fraud_risk:.0f}% fraud probability</div>', unsafe_allow_html=True)
                
                st.metric("Predicted Audit Time", f"{predicted_hours:.1f} hours")
                
                st.markdown("---")
                st.subheader("🎯 Problem Areas Identified")
                for area, risk in list(problem_areas.items())[:4]:
                    st.progress(risk/100)
                    st.write(f"**{area}** - {risk:.0f}% risk")
                
                st.markdown("---")
                st.subheader("👥 Resource Allocation Recommendations")
                for rec in resources[:3]:
                    st.info(f"**{rec['area']}** → Assign to: {rec['assigned_to']}")
                
                if not anomalies.empty:
                    st.markdown("---")
                    st.subheader("🚨 Anomalies Detected")
                    st.dataframe(anomalies[['date', 'amount', 'description', 'risk_level']].head(5))
                
                tab1, tab2 = st.tabs(["Unmatched Bank", "Unmatched Ledger"])
                with tab1:
                    if not result['unmatched_bank'].empty:
                        st.dataframe(result['unmatched_bank'][['date', 'amount', 'description']])
                    else:
                        st.success("✅ All bank transactions matched!")
                
                with tab2:
                    if not result['unmatched_ledger'].empty:
                        st.dataframe(result['unmatched_ledger'][['date', 'amount', 'description']])
                    else:
                        st.success("✅ All ledger entries matched!")
                
                # Email Section (only for Professional and Enterprise)
                if check_feature_access(st.session_state.firm_id, "email_reports"):
                    st.markdown("---")
                    st.subheader("📧 Email Report to Client")
                    
                    with st.form(key="email_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            client_email = st.text_input("Client Email Address", placeholder="client@company.com")
                        with col2:
                            client_name = st.text_input("Client Name", placeholder="Client Company Name")
                        
                        send_button = st.form_submit_button("📧 Send Report via Email", type="secondary")
                        
                        if send_button:
                            if client_email and client_name:
                                with st.spinner("Generating and sending report..."):
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
                                        output_path=pdf_path
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
                                        st.success(f"✅ Report sent to {client_email}")
                                    else:
                                        st.error(f"Failed to send: {message}")
                            else:
                                st.warning("Please enter both client email and name")
                else:
                    st.info("📧 Email reports are available on Professional and Enterprise plans. Upgrade to send reports.")
                
                # AI Recommendations
                st.markdown("---")
                st.subheader("💡 AI Recommendations")
                
                recommendations = generate_recommendations(
                    audit_data=result,
                    anomalies=anomalies,
                    fraud_risk=fraud_risk,
                    problem_areas=problem_areas,
                    match_rate=result['summary']['match_rate']
                )
                
                display_recommendations(recommendations)
                
                if st.button("📋 Export Recommendations as Checklist"):
                    checklist = []
                    for rec in recommendations:
                        checklist.append(f"□ [{rec['priority']}] {rec['category']}: {rec['recommendation']}")
                    checklist_text = "\n\n".join(checklist)
                    st.code(checklist_text, language="text")
                    st.caption("Copy this checklist for your audit team")
                
                if st.button("🔄 Run Another Audit", type="primary"):
                    st.session_state.audit_results = None
                    st.rerun()
    
    # Audit History Page
    elif st.session_state.page == "Audit History":
        st.markdown("### 📜 Audit History")
        
        audits = get_firm_audits(st.session_state.firm_id)
        
        if audits:
            df = pd.DataFrame(audits)
            df_display = df[['filename', 'match_rate', 'fraud_risk', 'predicted_hours', 'created_at']]
            df_display.columns = ['Filename', 'Match Rate', 'Fraud Risk', 'Predicted Hours', 'Date']
            st.dataframe(df_display, use_container_width=True)
        else:
            st.info("No audits yet. Run your first audit!")
    
    # Settings Page
    elif st.session_state.page == "Settings":
        st.markdown("### ⚙️ Settings")
        
        tab1, tab2, tab3 = st.tabs(["Team Management", "Firm Settings", "Subscription"])
        
        # Team Management Tab
        with tab1:
            st.markdown("#### 👥 Team Members")
            
            if check_feature_access(st.session_state.firm_id, "team_members"):
                if st.session_state.user_role == "owner":
                    team_members = get_team_members(st.session_state.firm_id)
                    
                    if team_members:
                        st.markdown("**Current Team:**")
                        for member in team_members:
                            col1, col2, col3 = st.columns([2, 2, 1])
                            with col1:
                                st.write(member["email"])
                            with col2:
                                st.write(f"Role: {member['role']}")
                            with col3:
                                if member["role"] != "owner":
                                    if st.button(f"Remove", key=f"remove_{member['id']}"):
                                        success, message = remove_team_member(
                                            member["id"], 
                                            st.session_state.firm_id,
                                            st.session_state.user_role
                                        )
                                        if success:
                                            st.success(message)
                                            st.rerun()
                                        else:
                                            st.error(message)
                    
                    st.markdown("---")
                    st.markdown("#### ✉️ Invite New Team Member")
                    
                    with st.form("invite_form"):
                        invite_email = st.text_input("Email Address", placeholder="colleague@firm.com")
                        invite_role = st.selectbox("Role", ["staff", "manager"])
                        submitted = st.form_submit_button("Generate Invite Link")
                        
                        if submitted and invite_email:
                            success, invite_url, result = create_invite(
                                st.session_state.firm_id,
                                invite_email,
                                invite_role
                            )
                            if success:
                                st.success("Invite link generated!")
                                st.code(invite_url, language="text")
                                st.caption("Copy this link and send it to your team member. Link expires in 7 days.")
                            else:
                                st.error(f"Failed to create invite: {result}")
                else:
                    st.info("Team management is only available to firm owners.")
                    team_members = get_team_members(st.session_state.firm_id)
                    if team_members:
                        st.markdown("**Your Team:**")
                        for member in team_members:
                            st.write(f"- {member['email']} ({member['role']})")
            else:
                st.info("👥 Team management is available on Professional and Enterprise plans. Upgrade to invite team members.")
                if st.button("View Subscription Plans"):
                    st.session_state.page = "Settings"
                    st.rerun()
        
        # Firm Settings Tab
        with tab2:
            st.markdown("#### 🏢 Firm Settings")
            st.info("Coming soon: Subscription management, billing, API keys")
            st.caption(f"Firm ID: {st.session_state.firm_id}")
        
        # Subscription Tab
        with tab3:
            st.markdown("#### 💳 Subscription & Billing")
            
            current_sub = get_firm_subscription(st.session_state.firm_id)
            current_tier = current_sub.get("subscription_tier", "free")
            tiers = get_subscription_tiers()
            
            st.markdown(f"**Current Plan:** {tiers[current_tier]['name']}")
            
            if current_tier == "free":
                st.info("You are on the Free plan. Upgrade to access more features.")
                st.caption("Free plan includes: 10 audits, basic reconciliation only")
            elif current_tier == "professional":
                st.success("You are on the Professional plan. Unlimited audits, PDF parsing, team members.")
            else:
                st.success("You are on the Enterprise plan. Everything included + client portal + API access.")
            
            st.markdown("---")
            st.markdown("### Available Plans")
            
            col1, col2, col3 = st.columns(3)
            
            for idx, (tier_id, tier) in enumerate(tiers.items()):
                col = [col1, col2, col3][idx]
                with col:
                    st.markdown(f"#### {tier['name']}")
                    if tier['price'] > 0:
                        st.markdown(f"**${tier['price']}/month**")
                    else:
                        st.markdown("**Free**")
                    st.markdown("---")
                    for feature in tier['features']:
                        if feature.startswith("✅"):
                            st.markdown(f"<span style='color:green'>{feature}</span>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<span style='color:#999'>{feature}</span>", unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    if tier_id == current_tier:
                        st.button("Current Plan", disabled=True, key=f"current_{tier_id}")
                    elif tier_id == "free":
                        if current_tier != "free":
                            if st.button("Downgrade to Free", key="btn_free"):
                                update_subscription(st.session_state.firm_id, "free")
                                st.success("Downgraded to Free plan")
                                st.rerun()
                    else:
                        if st.button(f"Upgrade to {tier['name']}", key=f"btn_{tier_id}"):
                            st.info(f"Payment integration coming soon. Please contact sales for {tier['name']} plan.")
    
    st.markdown("---")
    st.caption("© 2025 ARAI | Audit Risk & AI Intelligence | Finance Done Smarter")