import streamlit as st
import requests
import json
from supabase import create_client
from datetime import datetime, timedelta
import pandas as pd

def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# Supported African banks for API integration
SUPPORTED_BANKS = {
    "absa_sa": {"name": "ABSA South Africa", "country": "South Africa", "api_type": "stanza"},
    "fnb_sa": {"name": "FNB South Africa", "country": "South Africa", "api_type": "stanza"},
    "nedbank_sa": {"name": "Nedbank South Africa", "country": "South Africa", "api_type": "stanza"},
    "standard_bank_sa": {"name": "Standard Bank South Africa", "country": "South Africa", "api_type": "stanza"},
    "kcb_ke": {"name": "KCB Kenya", "country": "Kenya", "api_type": "stanza"},
    "equity_ke": {"name": "Equity Bank Kenya", "country": "Kenya", "api_type": "stanza"},
    "mcb_mu": {"name": "MCB Mauritius", "country": "Mauritius", "api_type": "stanza"},
    "sbm_mu": {"name": "SBM Mauritius", "country": "Mauritius", "api_type": "stanza"}
}

def get_bank_connections(firm_id):
    """Get saved bank connections for a firm"""
    supabase = get_supabase()
    
    try:
        result = supabase.table("bank_connections").select("*").eq("firm_id", firm_id).execute()
        return result.data if result.data else []
    except Exception as e:
        return []

def save_bank_connection(firm_id, bank_code, account_name, account_number, access_token, refresh_token, expires_at):
    """Save a bank connection to database"""
    supabase = get_supabase()
    
    try:
        result = supabase.table("bank_connections").insert({
            "firm_id": firm_id,
            "bank_code": bank_code,
            "account_name": account_name,
            "account_number": account_number,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "last_sync": datetime.now().isoformat(),
            "is_active": True
        }).execute()
        return True, result.data[0] if result.data else None
    except Exception as e:
        return False, str(e)

def delete_bank_connection(connection_id, firm_id):
    """Delete a bank connection"""
    supabase = get_supabase()
    
    try:
        supabase.table("bank_connections").delete().eq("id", connection_id).eq("firm_id", firm_id).execute()
        return True
    except Exception as e:
        return False

def sync_bank_transactions(connection_id, days_back=90):
    """Sync transactions from connected bank account"""
    # This is a placeholder - actual implementation depends on the bank API
    # For now, return mock data for testing
    
    mock_transactions = []
    start_date = datetime.now() - timedelta(days=days_back)
    
    for i in range(50):
        date = start_date + timedelta(days=i % days_back)
        amount = round(10 + (i * 123.45) % 5000, 2)
        
        mock_transactions.append({
            "date": date.strftime("%Y-%m-%d"),
            "amount": amount,
            "description": f"Transaction {i+1}",
            "reference": f"REF{i+1:04d}"
        })
    
    return mock_transactions

def display_bank_integration_dashboard(firm_id, user_role):
    """Display bank integration dashboard"""
    
    st.markdown("### 🏦 Bank Integration")
    st.markdown("Connect directly to your clients' bank accounts for real-time transaction data.")
    
    # Check if user has access (Enterprise only)
    from subscription import check_feature_access
    if not check_feature_access(firm_id, "api_access"):
        st.info("🔌 Bank API integration is available on Enterprise plans ($599/month).")
        st.markdown("**Benefits of Bank Integration:**")
        st.markdown("- Real-time transaction sync")
        st.markdown("- No more PDF uploads")
        st.markdown("- Automated daily updates")
        st.markdown("- Reduced manual work")
        
        # Fix: Use session state to switch to Subscription tab
        if st.button("💳 Upgrade to Enterprise", key="upgrade_bank_integration"):
            st.session_state.page = "Settings"
            st.session_state.settings_tab = "Subscription"
            st.rerun()
        return
    
    tabs = st.tabs(["Connected Banks", "Add New Bank", "Sync History"])
    
    # Connected Banks Tab
    with tabs[0]:
        st.markdown("#### 🔗 Connected Bank Accounts")
        
        connections = get_bank_connections(firm_id)
        
        if connections:
            for conn in connections:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    bank_info = SUPPORTED_BANKS.get(conn['bank_code'], {"name": conn['bank_code']})
                    
                    with col1:
                        st.markdown(f"**{bank_info['name']}**")
                        st.caption(f"Account: {conn.get('account_name', 'N/A')}")
                        st.caption(f"Number: {conn.get('account_number', 'N/A')}")
                    
                    with col2:
                        st.caption(f"Last synced: {conn.get('last_sync', 'Never')[:10] if conn.get('last_sync') else 'Never'}")
                        if conn.get('is_active'):
                            st.caption("Status: 🟢 Active")
                        else:
                            st.caption("Status: 🔴 Inactive")
                    
                    with col3:
                        if st.button(f"Sync Now", key=f"sync_{conn['id']}"):
                            with st.spinner("Syncing transactions..."):
                                transactions = sync_bank_transactions(conn['id'])
                                st.success(f"Synced {len(transactions)} transactions")
                                st.rerun()
                        
                        if st.button(f"Remove", key=f"remove_{conn['id']}"):
                            delete_bank_connection(conn['id'], firm_id)
                            st.rerun()
                    
                    st.markdown("---")
        else:
            st.info("No bank accounts connected. Go to 'Add New Bank' to connect your first account.")
    
    # Add New Bank Tab
    with tabs[1]:
        st.markdown("#### ➕ Connect a Bank Account")
        
        col1, col2 = st.columns(2)
        
        with col1:
            bank_options = {code: info['name'] for code, info in SUPPORTED_BANKS.items()}
            selected_bank = st.selectbox("Select Bank", list(bank_options.keys()), format_func=lambda x: bank_options[x])
            
            account_name = st.text_input("Account Name", placeholder="Client ABC - Operating Account")
            account_number = st.text_input("Account Number", placeholder="Enter account number")
        
        with col2:
            st.markdown("#### Authorization")
            st.markdown("""
            To connect your bank account, you will be redirected to your bank's secure login page.
            
            We use **Stanza** (open banking provider) to securely connect to:
            - ABSA South Africa
            - FNB South Africa
            - Nedbank South Africa
            - Standard Bank South Africa
            - KCB Kenya
            - Equity Bank Kenya
            - MCB Mauritius
            - SBM Mauritius
            
            Your credentials are never stored on our servers.
            """)
        
        if st.button("🔐 Connect Bank Account", type="primary"):
            if account_name:
                # In production, this would redirect to Stanza's OAuth flow
                st.info(f"Redirecting to {bank_options[selected_bank]} for authorization...")
                st.caption("In production, this would open your bank's login page.")
                
                # For demo, create a mock connection
                mock_expires = datetime.now() + timedelta(days=90)
                success, result = save_bank_connection(
                    firm_id, selected_bank, account_name, account_number,
                    "mock_access_token", "mock_refresh_token", mock_expires
                )
                if success:
                    st.success("Bank account connected successfully!")
                    st.rerun()
                else:
                    st.error(f"Error: {result}")
            else:
                st.warning("Please enter an account name")
    
    # Sync History Tab
    with tabs[2]:
        st.markdown("#### 📜 Sync History")
        
        connections = get_bank_connections(firm_id)
        
        if connections:
            for conn in connections:
                with st.expander(f"{SUPPORTED_BANKS.get(conn['bank_code'], {}).get('name', conn['bank_code'])} - {conn.get('account_name', 'N/A')}"):
                    # Show sync history (mock data for now)
                    st.markdown(f"**Last sync:** {conn.get('last_sync', 'Never')}")
                    st.markdown(f"**Status:** {'Active' if conn.get('is_active') else 'Inactive'}")
                    st.markdown(f"**Connected on:** {conn.get('created_at', 'Unknown')[:10] if conn.get('created_at') else 'Unknown'}")
                    
                    if st.button(f"View Transactions", key=f"history_{conn['id']}"):
                        transactions = sync_bank_transactions(conn['id'], days_back=30)
                        df = pd.DataFrame(transactions)
                        st.dataframe(df, use_container_width=True)
        else:
            st.info("No bank accounts connected yet.")