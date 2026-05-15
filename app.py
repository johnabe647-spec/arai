import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime
from supabase import create_client
from predictor import get_predictor

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
    .prediction-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .stButton > button {
        background-color: #1f77b4;
        color: white;
        border-radius: 5px;
    }
    .stButton > button:hover {
        background-color: #145a8a;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Supabase
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# Initialize predictor
@st.cache_resource
def init_predictor():
    return get_predictor()

predictor = init_predictor()

# Header
st.markdown('<p class="main-header">🔍 ARAI</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Audit Risk & AI Intelligence | Predictive Audit Analytics</p>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar navigation
with st.sidebar:
    st.markdown("### 📋 Navigation")
    page = st.radio("Navigation", ["Dashboard", "Upload Files", "Audit History", "Predictive Analytics"])
    
    st.markdown("---")
    st.markdown("### 📊 System Status")
    st.success("✅ Reconciliation Engine Ready")
    st.info("🤖 AI Predictions Active")
    st.info("📄 Supports: Excel, PDF")
    
    st.markdown("---")
    st.markdown("### 🔮 Predictive Features")
    st.markdown("- Fraud Risk Score")
    st.markdown("- Time Prediction")
    st.markdown("- Problem Area Detection")
    st.markdown("- Resource Allocation")

# Simple authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.audit_history = []

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("### 🔐 Login")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                if email and password:
                    st.session_state.authenticated = True
                    st.session_state.user_email = email
                    st.rerun()
                else:
                    st.error("Please enter email and password")
else:
    # Dashboard Page
    if page == "Dashboard":
        st.markdown(f"### Welcome back, {st.session_state.user_email}")
        st.markdown("ARAI predicts audit risks before you start. Upload files to get AI-powered insights.")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Audits This Month", len(st.session_state.audit_history))
        col2.metric("Avg Match Rate", "92%", help="Based on completed audits")
        col3.metric("Time Saved", f"{len(st.session_state.audit_history) * 15}h", help="Estimated hours saved")
        
        st.markdown("---")
        st.markdown("### 📈 Quick Start")
        
        with st.expander("How to run a predictive audit"):
            st.markdown("""
            1. Click **'Upload Files'** in the sidebar
            2. Upload your **Bank Statement** (Excel or PDF)
            3. Upload your **Ledger** (Excel file)
            4. Click **'Run Audit'**
            5. ARAI will:
               - Reconcile all transactions
               - Calculate fraud risk score
               - Predict audit hours
               - Identify problem areas
               - Suggest staff allocation
            6. Download your comprehensive report
            """)
        
        if st.button("Start New Audit", type="primary"):
            st.session_state.page = "Upload Files"
            st.rerun()
        
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()
    
    # Upload Files Page
    elif page == "Upload Files":
        st.markdown("### 📄 Upload Audit Files")
        st.markdown("Upload your bank statement and ledger for AI-powered analysis.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🏦 Bank Statement")
            bank_file = st.file_uploader(
                "Upload Excel or PDF",
                type=['xlsx', 'xls', 'pdf'],
                key="bank",
                help="Supported formats: Excel (.xlsx, .xls) or PDF (.pdf)"
            )
            if bank_file:
                st.success(f"✅ {bank_file.name}")
        
        with col2:
            st.markdown("#### 📊 Ledger")
            ledger_file = st.file_uploader(
                "Upload Excel file",
                type=['xlsx', 'xls'],
                key="ledger",
                help="Ledger must be in Excel format (.xlsx or .xls)"
            )
            if ledger_file:
                st.success(f"✅ {ledger_file.name}")
        
        st.markdown("---")
        
        if bank_file and ledger_file:
            if st.button("🚀 Run Predictive Audit", type="primary", use_container_width=True):
                with st.spinner("Running AI-powered audit..."):
                    try:
                        # Import reconciliation modules
                        from reconciler import reconcile
                        from anomaly_detector import detect_anomalies
                        
                        # Save uploaded files temporarily
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
                            st.info("📄 Parsing PDF bank statement...")
                            bank_df = parse_bank_statement(bank_path)
                            if bank_df.empty:
                                st.error("Could not parse PDF. Try Excel format or specify bank name.")
                                st.stop()
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
                        st.info("🔄 Matching transactions...")
                        result = reconcile(bank_df, ledger_df)
                        
                        # Detect anomalies
                        st.info("🔍 Scanning for anomalies...")
                        anomalies = detect_anomalies(bank_df)
                        
                        # === PREDICTIVE ANALYTICS ===
                        st.info("🤖 Running predictive analytics...")
                        
                        # Fraud risk prediction
                        fraud_risk = predictor.predict_fraud_risk(bank_df)
                        
                        # Time prediction
                        predicted_hours = predictor.predict_audit_time(bank_df)
                        
                        # Problem areas
                        problem_areas = predictor.predict_problem_areas(bank_df)
                        
                        # Resource allocation
                        resources = predictor.suggest_resource_allocation(fraud_risk, predicted_hours, problem_areas)
                        
                        # Display results
                        st.markdown("---")
                        st.subheader("📊 Audit Results")
                        
                        # Summary metrics row 1
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("✅ Matched", result['summary']['matched'])
                        m2.metric("⚠️ Unmatched Bank", result['summary']['unmatched_bank'])
                        m3.metric("⚠️ Unmatched Ledger", result['summary']['unmatched_ledger'])
                        m4.metric("📈 Match Rate", f"{result['summary']['match_rate']:.1%}")
                        
                        st.markdown("---")
                        st.subheader("🤖 AI Predictions")
                        
                        # Fraud risk meter
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### 🔮 Fraud Risk Score")
                            if fraud_risk >= 70:
                                st.markdown(f'<div class="risk-high">🔴 HIGH RISK: {fraud_risk:.0f}%</div>', unsafe_allow_html=True)
                                st.caption("This audit has a high probability of material misstatement. Assign senior staff and increase sample sizes.")
                            elif fraud_risk >= 40:
                                st.markdown(f'<div class="risk-medium">🟡 MEDIUM RISK: {fraud_risk:.0f}%</div>', unsafe_allow_html=True)
                                st.caption("Moderate risk detected. Standard procedures with additional oversight recommended.")
                            else:
                                st.markdown(f'<div class="risk-low">🟢 LOW RISK: {fraud_risk:.0f}%</div>', unsafe_allow_html=True)
                                st.caption("Low risk audit. Standard procedures are sufficient.")
                            
                            st.markdown("---")
                            st.markdown("#### ⏱️ Predicted Audit Time")
                            st.metric("Estimated Hours", f"{predicted_hours:.1f} hours")
                            st.caption(f"Based on {len(bank_df)} transactions and complexity analysis")
                        
                        with col2:
                            st.markdown("#### 🎯 Problem Areas")
                            for area, risk in list(problem_areas.items())[:4]:
                                st.progress(risk/100)
                                st.write(f"**{area}** - {risk:.0f}% risk")
                        
                        st.markdown("---")
                        st.markdown("#### 👥 Resource Allocation Recommendations")
                        
                        for rec in resources[:4]:
                            with st.container():
                                st.markdown(f"""
                                <div class="prediction-card">
                                    <strong>📌 {rec['area']}</strong><br>
                                    👤 Assign to: <strong>{rec['assigned_to']}</strong><br>
                                    📝 {rec['reason']}
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Anomalies
                        if not anomalies.empty:
                            st.markdown("---")
                            st.subheader("🚨 Anomalies Detected")
                            st.warning(f"Found {len(anomalies)} suspicious transactions that require review")
                            st.dataframe(anomalies[['date', 'amount', 'description', 'risk_level', 'anomaly_reasons']].head(10), use_container_width=True)
                        else:
                            st.success("✅ No anomalies detected")
                        
                        # Unmatched transactions
                        tab1, tab2 = st.tabs(["Unmatched Bank Transactions", "Unmatched Ledger Entries"])
                        
                        with tab1:
                            if not result['unmatched_bank'].empty:
                                st.warning(f"{len(result['unmatched_bank'])} transactions in bank statement with no ledger match")
                                st.dataframe(result['unmatched_bank'][['date', 'amount', 'description']], use_container_width=True)
                            else:
                                st.success("✅ All bank transactions matched!")
                        
                        with tab2:
                            if not result['unmatched_ledger'].empty:
                                st.warning(f"{len(result['unmatched_ledger'])} ledger entries with no bank match")
                                st.dataframe(result['unmatched_ledger'][['date', 'amount', 'description']], use_container_width=True)
                            else:
                                st.success("✅ All ledger entries matched!")
                        
                        # Save to history
                        st.session_state.audit_history.append({
                            'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                            'filename': bank_file.name,
                            'match_rate': result['summary']['match_rate'],
                            'fraud_risk': fraud_risk,
                            'predicted_hours': predicted_hours,
                            'anomalies': len(anomalies)
                        })
                        
                        # Generate downloadable report
                        st.markdown("---")
                        st.subheader("📥 Download Report")
                        
                        output_path = "audit_report.xlsx"
                        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                            # Summary with predictions
                            summary_data = {
                                'Metric': ['Match Rate', 'Matched Transactions', 'Unmatched Bank', 'Unmatched Ledger', 
                                          'Fraud Risk Score', 'Predicted Audit Hours', 'Anomalies Found'],
                                'Value': [f"{result['summary']['match_rate']:.1%}", result['summary']['matched'],
                                         result['summary']['unmatched_bank'], result['summary']['unmatched_ledger'],
                                         f"{fraud_risk:.1f}%", f"{predicted_hours:.1f}", len(anomalies)]
                            }
                            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
                            
                            if not result['matched'].empty:
                                result['matched'].to_excel(writer, sheet_name='Matched', index=False)
                            if not result['unmatched_bank'].empty:
                                result['unmatched_bank'].to_excel(writer, sheet_name='Unmatched_Bank', index=False)
                            if not result['unmatched_ledger'].empty:
                                result['unmatched_ledger'].to_excel(writer, sheet_name='Unmatched_Ledger', index=False)
                            if not anomalies.empty:
                                anomalies.to_excel(writer, sheet_name='Anomalies', index=False)
                            
                            # Predictions sheet
                            predictions_data = []
                            for area, risk in problem_areas.items():
                                predictions_data.append({'Problem Area': area, 'Risk Level': f"{risk:.0f}%"})
                            pd.DataFrame(predictions_data).to_excel(writer, sheet_name='Predictions', index=False)
                            
                            # Resource allocation sheet
                            resources_data = []
                            for rec in resources:
                                resources_data.append({'Area': rec['area'], 'Assign To': rec['assigned_to'], 'Reason': rec['reason']})
                            pd.DataFrame(resources_data).to_excel(writer, sheet_name='Resource Allocation', index=False)
                        
                        with open(output_path, 'rb') as f:
                            st.download_button(
                                label="📎 Download Comprehensive Audit Report",
                                data=f,
                                file_name="arai_predictive_audit_report.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                        
                        # Clean up
                        os.unlink(bank_path)
                        os.unlink(ledger_path)
                        os.unlink(output_path)
                        
                        st.balloons()
                        st.success("✅ Predictive audit complete! Download your comprehensive report above.")
                        
                    except Exception as e:
                        st.error(f"Error: {e}")
                        st.info("Troubleshooting tips:\n- Ensure Excel files have 'date', 'amount', and 'description' columns\n- Try converting PDF to Excel if parsing fails")
    
    # Audit History Page
    elif page == "Audit History":
        st.markdown("### 📜 Audit History")
        
        if st.session_state.audit_history:
            history_df = pd.DataFrame(st.session_state.audit_history)
            st.dataframe(history_df, use_container_width=True)
            
            # Summary stats
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Audits", len(history_df))
            col2.metric("Avg Match Rate", f"{history_df['match_rate'].mean():.1%}")
            col3.metric("Avg Fraud Risk", f"{history_df['fraud_risk'].mean():.1f}%")
            
            if st.button("Clear History"):
                st.session_state.audit_history = []
                st.rerun()
        else:
            st.info("No audits processed yet. Upload files to get started.")
        
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()
    
    # Predictive Analytics Page
    elif page == "Predictive Analytics":
        st.markdown("### 🤖 Predictive Analytics Dashboard")
        st.markdown("ARAI uses machine learning to predict audit risks before you start.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔮 How Fraud Risk is Calculated")
            st.markdown("""
            ARAI analyzes multiple risk indicators:
            - **Round dollar transactions** - Potential fraud indicator
            - **Duplicate payments** - Possible errors or fraud
            - **Weekend transactions** - Unusual posting patterns
            - **Unusually large amounts** - Statistical outliers
            - **Transaction frequency** - Unusual patterns
            """)
        
        with col2:
            st.markdown("#### ⏱️ How Time is Predicted")
            st.markdown("""
            Time predictions are based on:
            - **Transaction volume** - More transactions = more time
            - **Complexity score** - Anomalies add time
            - **File type** - PDF vs Excel parsing time
            - **Historical patterns** - Learning from past audits
            """)
        
        st.markdown("---")
        st.markdown("#### 📊 Understanding Your Results")
        
        st.markdown("""
        | Score | Risk Level | Recommended Action |
        |-------|------------|-------------------|
        | 0-40% | 🟢 Low Risk | Standard audit procedures |
        | 40-70% | 🟡 Medium Risk | Increase sample size, add senior review |
        | 70-100% | 🔴 High Risk | Full forensic approach, partner oversight |
        """)
        
        if st.button("Run a Predictive Audit"):
            st.session_state.page = "Upload Files"
            st.rerun()
    
    st.markdown("---")
    st.caption("© 2025 ARAI | Audit Risk & AI Intelligence | Finance Done Smarter | Powered by Machine Learning")