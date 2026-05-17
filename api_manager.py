import streamlit as st
from supabase import create_client
import secrets
import string
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px

def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def generate_api_key():
    """Generate a secure API key"""
    alphabet = string.ascii_letters + string.digits
    return 'arai_' + ''.join(secrets.choice(alphabet) for _ in range(32))

def create_api_key(firm_id, key_name, permissions=None, expires_days=None):
    """Create a new API key for a firm"""
    supabase = get_supabase()
    
    api_key = generate_api_key()
    expires_at = datetime.now() + timedelta(days=expires_days) if expires_days else None
    
    if permissions is None:
        permissions = {"audit": True, "read": True, "write": False}
    
    try:
        result = supabase.table("api_keys").insert({
            "firm_id": firm_id,
            "key_name": key_name,
            "api_key": api_key,
            "permissions": permissions,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "is_active": True
        }).execute()
        
        return True, api_key, result.data[0] if result.data else None
    except Exception as e:
        return False, str(e), None

def get_api_keys(firm_id):
    """Get all API keys for a firm"""
    supabase = get_supabase()
    
    try:
        result = supabase.table("api_keys").select("*").eq("firm_id", firm_id).order("created_at", desc=True).execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error getting API keys: {e}")
        return []

def revoke_api_key(key_id, firm_id):
    """Revoke an API key"""
    supabase = get_supabase()
    
    try:
        supabase.table("api_keys").update({"is_active": False}).eq("id", key_id).eq("firm_id", firm_id).execute()
        return True
    except Exception as e:
        print(f"Error revoking API key: {e}")
        return False

def delete_api_key(key_id, firm_id):
    """Delete an API key"""
    supabase = get_supabase()
    
    try:
        supabase.table("api_keys").delete().eq("id", key_id).eq("firm_id", firm_id).execute()
        return True
    except Exception as e:
        print(f"Error deleting API key: {e}")
        return False

def create_webhook(firm_id, webhook_name, webhook_url, events):
    """Create a new webhook"""
    supabase = get_supabase()
    
    secret_key = secrets.token_hex(32)
    
    try:
        result = supabase.table("webhooks").insert({
            "firm_id": firm_id,
            "webhook_name": webhook_name,
            "webhook_url": webhook_url,
            "events": events,
            "secret_key": secret_key,
            "is_active": True
        }).execute()
        
        return True, secret_key, result.data[0] if result.data else None
    except Exception as e:
        return False, str(e), None

def get_webhooks(firm_id):
    """Get all webhooks for a firm"""
    supabase = get_supabase()
    
    try:
        result = supabase.table("webhooks").select("*").eq("firm_id", firm_id).execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error getting webhooks: {e}")
        return []

def delete_webhook(webhook_id, firm_id):
    """Delete a webhook"""
    supabase = get_supabase()
    
    try:
        supabase.table("webhooks").delete().eq("id", webhook_id).eq("firm_id", firm_id).execute()
        return True
    except Exception as e:
        print(f"Error deleting webhook: {e}")
        return False

def toggle_webhook(webhook_id, firm_id, is_active):
    """Enable/disable a webhook"""
    supabase = get_supabase()
    
    try:
        supabase.table("webhooks").update({"is_active": is_active}).eq("id", webhook_id).eq("firm_id", firm_id).execute()
        return True
    except Exception as e:
        print(f"Error toggling webhook: {e}")
        return False

def get_api_logs(firm_id, limit=100):
    """Get API usage logs"""
    supabase = get_supabase()
    
    try:
        result = supabase.table("api_logs").select("*").eq("firm_id", firm_id).order("created_at", desc=True).limit(limit).execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error getting API logs: {e}")
        return []

def display_api_dashboard(firm_id):
    """Display API management dashboard"""
    
    st.markdown("### 🔌 API Management")
    
    tab1, tab2, tab3 = st.tabs(["API Keys", "Webhooks", "API Usage"])
    
    # API Keys Tab
    with tab1:
        st.markdown("#### 🔑 API Keys")
        st.caption("Create API keys to integrate ARAI with your internal systems.")
        
        # Create new API key
        with st.expander("➕ Create New API Key"):
            with st.form("create_api_key_form"):
                key_name = st.text_input("Key Name", placeholder="Production Server")
                
                col1, col2 = st.columns(2)
                with col1:
                    expires_days = st.number_input("Expires After (Days)", min_value=0, max_value=365, value=90, 
                                                   help="0 = never expires")
                with col2:
                    permissions = st.multiselect("Permissions", ["audit", "read", "write"], default=["audit", "read"])
                
                submitted = st.form_submit_button("Generate API Key")
                
                if submitted and key_name:
                    perms_dict = {p: True for p in permissions}
                    success, result, key_data = create_api_key(
                        firm_id, key_name, perms_dict, expires_days if expires_days > 0 else None
                    )
                    if success:
                        st.success("API Key Generated!")
                        st.code(result, language="text")
                        st.warning("⚠️ Copy this key now. You won't be able to see it again.")
                        st.caption("Example usage:")
                        st.code(f'curl -X POST https://api.arai.africa/v1/audit \\\n  -H "Authorization: Bearer {result}" \\\n  -H "Content-Type: application/json" \\\n  -d \'{{"bank_file_url": "https://..."}}\'', language="bash")
                    else:
                        st.error(f"Error: {result}")
        
        # Display existing keys
        keys = get_api_keys(firm_id)
        if keys:
            st.markdown("#### Your API Keys")
            for key in keys:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.markdown(f"**{key['key_name']}**")
                        st.caption(f"Created: {key['created_at'][:10]}")
                        if key.get('expires_at'):
                            st.caption(f"Expires: {key['expires_at'][:10]}")
                    with col2:
                        if key.get('permissions'):
                            perms = [p for p, v in key['permissions'].items() if v]
                            st.caption(f"Permissions: {', '.join(perms)}")
                    with col3:
                        if key['is_active']:
                            if st.button(f"Revoke", key=f"revoke_{key['id']}"):
                                revoke_api_key(key['id'], firm_id)
                                st.rerun()
                        else:
                            st.caption("🔴 Revoked")
                        
                        if st.button(f"Delete", key=f"delete_key_{key['id']}"):
                            delete_api_key(key['id'], firm_id)
                            st.rerun()
                    st.markdown("---")
        else:
            st.info("No API keys created yet.")
    
    # Webhooks Tab
    with tab2:
        st.markdown("#### 🔔 Webhooks")
        st.caption("Receive real-time notifications when audits complete.")
        
        # Create new webhook
        with st.expander("➕ Create New Webhook"):
            with st.form("create_webhook_form"):
                webhook_name = st.text_input("Webhook Name", placeholder="Slack Notifications")
                webhook_url = st.text_input("Webhook URL", placeholder="https://your-server.com/webhook")
                events = st.multiselect("Events to Send", 
                                        ["audit.completed", "report.generated", "anomaly.detected", "client.created"],
                                        default=["audit.completed"])
                
                submitted = st.form_submit_button("Create Webhook")
                
                if submitted and webhook_name and webhook_url:
                    success, result, webhook_data = create_webhook(firm_id, webhook_name, webhook_url, events)
                    if success:
                        st.success("Webhook created!")
                        st.code(f"Secret Key: {result}", language="text")
                        st.warning("⚠️ Copy this secret key. You'll need it to verify webhook signatures.")
                        
                        # Example payload
                        st.caption("Example payload sent to your webhook:")
                        st.code('''
{
  "event": "audit.completed",
  "timestamp": "2025-01-01T12:00:00Z",
  "data": {
    "audit_id": 123,
    "match_rate": 0.95,
    "fraud_risk": 25,
    "download_url": "https://..."
  },
  "signature": "sha256=..."
}
''', language="json")
                    else:
                        st.error(f"Error: {result}")
        
        # Display existing webhooks
        webhooks = get_webhooks(firm_id)
        if webhooks:
            st.markdown("#### Your Webhooks")
            for webhook in webhooks:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.markdown(f"**{webhook['webhook_name']}**")
                        st.caption(f"URL: {webhook['webhook_url'][:50]}...")
                        st.caption(f"Events: {', '.join(webhook['events'])}")
                    with col2:
                        status = "🟢 Active" if webhook['is_active'] else "🔴 Paused"
                        st.caption(status)
                    with col3:
                        if webhook['is_active']:
                            if st.button(f"Pause", key=f"pause_webhook_{webhook['id']}"):
                                toggle_webhook(webhook['id'], firm_id, False)
                                st.rerun()
                        else:
                            if st.button(f"Resume", key=f"resume_webhook_{webhook['id']}"):
                                toggle_webhook(webhook['id'], firm_id, True)
                                st.rerun()
                        
                        if st.button(f"Delete", key=f"delete_webhook_{webhook['id']}"):
                            delete_webhook(webhook['id'], firm_id)
                            st.rerun()
                    st.markdown("---")
        else:
            st.info("No webhooks created yet.")
    
    # API Usage Tab
    with tab3:
        st.markdown("#### 📊 API Usage")
        
        logs = get_api_logs(firm_id, limit=200)
        
        if logs:
            df = pd.DataFrame(logs)
            df['created_at'] = pd.to_datetime(df['created_at'])
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total API Calls", len(df))
            col2.metric("Avg Response Time", f"{df['response_time_ms'].mean():.0f} ms")
            col3.metric("Success Rate", f"{(df['status_code'] == 200).mean() * 100:.1f}%")
            
            st.markdown("---")
            
            # Usage by endpoint chart
            endpoint_counts = df['endpoint'].value_counts().reset_index()
            endpoint_counts.columns = ['Endpoint', 'Count']
            fig = px.bar(endpoint_counts, x='Endpoint', y='Count', title='API Calls by Endpoint',
                         color_discrete_sequence=['#1f77b4'])
            st.plotly_chart(fig, use_container_width=True)
            
            # Recent logs
            st.markdown("#### Recent API Calls")
            recent = df[['created_at', 'method', 'endpoint', 'status_code', 'response_time_ms']].head(20)
            recent['created_at'] = recent['created_at'].dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(recent, use_container_width=True)
        else:
            st.info("No API usage yet. Make your first API call to see analytics.")