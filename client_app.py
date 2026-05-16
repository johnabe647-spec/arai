import streamlit as st
import pandas as pd
from supabase import create_client
from client_portal import login_client, get_client_reports
from report_generator import generate_audit_pdf
import os
from datetime import datetime
import tempfile

# Page config
st.set_page_config(
    page_title="ARAI - Client Portal",
    page_icon="🔍",
    layout="wide"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🔍 ARAI Client Portal</p>', unsafe_allow_html=True)
st.markdown("---")

# Initialize Supabase
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# Session state
if "client_authenticated" not in st.session_state:
    st.session_state.client_authenticated = False
if "client_data" not in st.session_state:
    st.session_state.client_data = None

if not st.session_state.client_authenticated:
    with st.form("client_login_form"):
        st.subheader("Client Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            success, message, client = login_client(email, password)
            if success:
                st.session_state.client_authenticated = True
                st.session_state.client_data = client
                st.rerun()
            else:
                st.error(message)
else:
    client = st.session_state.client_data
    
    st.success(f"Welcome, {client['client_name']}!")
    st.markdown(f"**Company:** {client['client_company']}")
    st.markdown("---")
    
    # Get reports
    reports = get_client_reports(client['id'])
    
    st.subheader("📄 Your Audit Reports")
    
    if reports:
        for report in reports:
            audit = report.get('audits', {})
            created_at = audit.get('created_at', 'Unknown date')[:10]
            match_rate = audit.get('match_rate', 0)
            fraud_risk = audit.get('fraud_risk', 0)
            
            with st.expander(f"📊 Audit Report - {created_at}"):
                col1, col2, col3 = st.columns(3)
                col1.metric("Match Rate", f"{match_rate:.1%}")
                col2.metric("Fraud Risk", f"{fraud_risk:.0f}%")
                col3.metric("Date", created_at)
                
                if st.button(f"Download Report", key=f"download_{report['id']}"):
                    # Generate PDF from stored audit data
                    pdf_path = f"client_report_{report['id']}.pdf"
                    
                    # You'll need to store full audit data in the audits table
                    audit_summary = {
                        "match_rate": match_rate,
                        "matched": audit.get('audit_data', {}).get('matched', 0),
                        "unmatched_bank": audit.get('audit_data', {}).get('unmatched_bank', 0),
                        "unmatched_ledger": audit.get('audit_data', {}).get('unmatched_ledger', 0),
                        "anomalies": audit.get('audit_data', {}).get('anomalies', 0),
                        "fraud_risk": fraud_risk,
                        "problem_areas": audit.get('audit_data', {}).get('problem_areas', {})
                    }
                    
                    generate_audit_pdf(
                        firm_name=client.get('firms', {}).get('name', 'Your Auditor'),
                        client_name=client['client_name'],
                        audit_data=audit_summary,
                        output_path=pdf_path
                    )
                    
                    with open(pdf_path, 'rb') as f:
                        st.download_button(
                            label="📥 Click to Download",
                            data=f,
                            file_name=f"audit_report_{created_at}.pdf",
                            mime="application/pdf"
                        )
                    
                    os.unlink(pdf_path)
    else:
        st.info("No reports have been shared with you yet.")
    
    st.markdown("---")
    if st.button("Logout"):
        st.session_state.client_authenticated = False
        st.session_state.client_data = None
        st.rerun()