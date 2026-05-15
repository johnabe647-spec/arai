import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime
from supabase import create_client

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

# Header
st.markdown('<p class="main-header">🔍 ARAI</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Audit Risk & AI Intelligence</p>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar navigation - FIXED: Added label "Navigation"
with st.sidebar:
    st.markdown("### 📋 Navigation")
    page = st.radio("Navigation", ["Dashboard", "Upload Files", "Audit History"])
    
    st.markdown("---")
    st.markdown("### 📊 System Status")
    st.success("✅ Reconciliation Engine Ready")
    st.info("📄 Supports: Excel, PDF")
    st.info("🏦 GTBank, Standard Bank SA, ABSA, KCB, NMB Zimbabwe")
    
    st.markdown("---")
    st.markdown("### 🔧 Features")
    st.markdown("- Bank-Ledger Reconciliation")
    st.markdown("- Fuzzy Description Matching")
    st.markdown("- Anomaly Detection")
    st.markdown("- PDF Bank Parsing")
    st.markdown("- Excel Report Export")

# Simple authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

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
        st.markdown("Ready to run your first audit?")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Audits This Month", "0")
        col2.metric("Transactions Processed", "0")
        col3.metric("Anomalies Found", "0")
        
        st.info("👈 Go to 'Upload Files' to start an audit")
        
        st.markdown("---")
        st.markdown("### 📈 Quick Start Guide")
        
        with st.expander("How to run an audit"):
            st.markdown("""
            1. Click **'Upload Files'** in the sidebar
            2. Upload your **Bank Statement** (Excel or PDF)
            3. Upload your **Ledger** (Excel file)
            4. Click **'Run Audit'**
            5. Download your Excel report
            """)
        
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()
    
    # Upload Files Page
    elif page == "Upload Files":
        st.markdown("### 📄 Upload Audit Files")
        st.markdown("Upload your bank statement and ledger to run an automated audit.")
        
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
            if st.button("🚀 Run Audit", type="primary", use_container_width=True):
                with st.spinner("Processing audit... This may take a few seconds"):
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
                        
                        # Display results
                        st.markdown("---")
                        st.subheader("📊 Audit Results")
                        
                        # Summary metrics
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("✅ Matched", result['summary']['matched'])
                        m2.metric("⚠️ Unmatched Bank", result['summary']['unmatched_bank'])
                        m3.metric("⚠️ Unmatched Ledger", result['summary']['unmatched_ledger'])
                        m4.metric("📈 Match Rate", f"{result['summary']['match_rate']:.1%}")
                        
                        # Anomalies
                        if not anomalies.empty:
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
                        
                        # Generate downloadable report
                        st.markdown("---")
                        st.subheader("📥 Download Report")
                        
                        # Create Excel report
                        output_path = "audit_report.xlsx"
                        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                            pd.DataFrame([result['summary']]).to_excel(writer, sheet_name='Summary', index=False)
                            if not result['matched'].empty:
                                result['matched'].to_excel(writer, sheet_name='Matched', index=False)
                            if not result['unmatched_bank'].empty:
                                result['unmatched_bank'].to_excel(writer, sheet_name='Unmatched_Bank', index=False)
                            if not result['unmatched_ledger'].empty:
                                result['unmatched_ledger'].to_excel(writer, sheet_name='Unmatched_Ledger', index=False)
                            if not anomalies.empty:
                                anomalies.to_excel(writer, sheet_name='Anomalies', index=False)
                        
                        with open(output_path, 'rb') as f:
                            st.download_button(
                                label="📎 Download Excel Report",
                                data=f,
                                file_name="arai_audit_report.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                        
                        # Clean up
                        os.unlink(bank_path)
                        os.unlink(ledger_path)
                        os.unlink(output_path)
                        
                        st.success("✅ Audit complete! Download your report above.")
                        
                    except Exception as e:
                        st.error(f"Error: {e}")
                        st.info("Troubleshooting tips:\n- Ensure Excel files have 'date', 'amount', and 'description' columns\n- Try converting PDF to Excel if parsing fails")
    
    # Audit History Page
    elif page == "Audit History":
        st.markdown("### 📜 Audit History")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info("📁 No audits processed yet")
            st.caption("Upload files to start your first audit")
        
        with col2:
            st.info("📊 Coming soon")
            st.caption("Audit history will appear here")
        
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()
    
    st.markdown("---")
    st.caption("© 2025 ARAI | Audit Risk & AI Intelligence | Finance Done Smarter")