import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime
from supabase import create_client
from auth import register_firm, login_user, get_firm_audits, save_audit, get_firm_stats, get_supabase

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
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<p class="main-header">🔍 ARAI</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Audit Risk & AI Intelligence | Client Portal</p>', unsafe_allow_html=True)
st.markdown("---")

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "firm_id" not in st.session_state:
    st.session_state.firm_id = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

# Authentication
if not st.session_state.authenticated:
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            st.markdown("### 🔐 Login")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)
            
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
            st.markdown("### 📝 Register Your Firm")
            firm_name = st.text_input("Firm Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Register", use_container_width=True)
            
            if submitted:
                if password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    success, result = register_firm(firm_name, email, password)
                    if success:
                        st.success("Registration successful! Please login.")
                    else:
                        st.error(result)

else:
    # Sidebar navigation
    with st.sidebar:
        st.markdown(f"### {st.session_state.user_email}")
        st.markdown(f"Firm ID: {st.session_state.firm_id}")
        st.markdown("---")
        
        page = st.radio("Navigation", ["Dashboard", "New Audit", "Audit History", "Settings"])
        st.session_state.page = page
        
        st.markdown("---")
        if st.button("Logout"):
            for key in ["authenticated", "firm_id", "user_email", "user_role"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    # Dashboard Page
    if st.session_state.page == "Dashboard":
        st.markdown(f"### Welcome to ARAI")
        
        # Get firm statistics
        stats = get_firm_stats(st.session_state.firm_id)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Audits", stats["total_audits"])
        col2.metric("Avg Match Rate", f"{stats['avg_match_rate']:.1%}")
        col3.metric("Avg Fraud Risk", f"{stats['avg_fraud_risk']:.0f}%")
        col4.metric("Time Saved", f"{stats['total_time_saved']} hours")
        
        st.markdown("---")
        st.markdown("### Quick Actions")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📄 Run New Audit", use_container_width=True):
                st.session_state.page = "New Audit"
                st.rerun()
        
        with col2:
            if st.button("📜 View Audit History", use_container_width=True):
                st.session_state.page = "Audit History"
                st.rerun()
    
    # New Audit Page
    elif st.session_state.page == "New Audit":
        st.markdown("### 📄 New Audit")
        
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
                        
                        # Save uploaded files
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_bank:
                            tmp_bank.write(bank_file.getvalue())
                            bank_path = tmp_bank.name
                        
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_ledger:
                            tmp_ledger.write(ledger_file.getvalue())
                            ledger_path = tmp_ledger.name
                        
                        # Load bank file
                        bank_filename = bank_file.name.lower()
                        
                        if bank_filename.endswith('.pdf'):
                            from pdf_parser import parse_bank_statement
                            bank_df = parse_bank_statement(bank_path)
                        else:
                            bank_df = pd.read_excel(bank_path)
                            bank_df.columns = [col.lower() for col in bank_df.columns]
                            if 'amount' in bank_df.columns:
                                bank_df['amount'] = bank_df['amount'].abs()
                        
                        # Load ledger
                        ledger_df = pd.read_excel(ledger_path)
                        ledger_df.columns = [col.lower() for col in ledger_df.columns]
                        if 'amount' in ledger_df.columns:
                            ledger_df['amount'] = ledger_df['amount'].abs()
                        
                        # Run reconciliation
                        result = reconcile(bank_df, ledger_df)
                        
                        # Detect anomalies
                        anomalies = detect_anomalies(bank_df)
                        
                        # Predictive analytics
                        fraud_risk = predictor.predict_fraud_risk(bank_df)
                        predicted_hours = predictor.predict_audit_time(bank_df)
                        problem_areas = predictor.predict_problem_areas(bank_df)
                        
                        # Save to database
                        audit_data = {
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
                            audit_data=audit_data
                        )
                        
                        # Display results
                        st.success(f"✅ Audit complete! Match rate: {result['summary']['match_rate']:.1%}")
                        
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("Matched", result['summary']['matched'])
                        m2.metric("Unmatched Bank", result['summary']['unmatched_bank'])
                        m3.metric("Unmatched Ledger", result['summary']['unmatched_ledger'])
                        m4.metric("Fraud Risk", f"{fraud_risk:.0f}%")
                        
                        # Clean up
                        os.unlink(bank_path)
                        os.unlink(ledger_path)
                        
                    except Exception as e:
                        st.error(f"Error: {e}")
    
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
        st.info("Coming soon: Firm settings, team member invitations, subscription management")
    
    st.markdown("---")
    st.caption("© 2025 ARAI | Audit Risk & AI Intelligence | Finance Done Smarter")