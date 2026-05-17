import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px

def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def get_usage_stats(firm_id):
    """Get usage statistics for a firm"""
    supabase = get_supabase()
    
    # Get current subscription
    sub_result = supabase.table("firms").select("subscription_tier").eq("id", firm_id).execute()
    current_tier = sub_result.data[0].get("subscription_tier", "free") if sub_result.data else "free"
    
    # Get audit count
    audit_result = supabase.table("audits").select("id", count="exact").eq("firm_id", firm_id).execute()
    audit_count = audit_result.count if hasattr(audit_result, 'count') else len(audit_result.data) if audit_result.data else 0
    
    # Get team member count
    team_result = supabase.table("users").select("id", count="exact").eq("firm_id", firm_id).execute()
    team_count = team_result.count if hasattr(team_result, 'count') else len(team_result.data) if team_result.data else 0
    
    # Get this month's activity (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_result = supabase.table("audits").select("id", count="exact").eq("firm_id", firm_id).gte("created_at", thirty_days_ago.isoformat()).execute()
    recent_audits = recent_result.count if hasattr(recent_result, 'count') else len(recent_result.data) if recent_result.data else 0
    
    # Define limits by tier
    limits = {
        "free": {
            "max_audits": 10,
            "max_team_members": 1,
            "max_audits_per_month": 10,
            "features": ["basic_reconciliation", "excel_upload"]
        },
        "professional": {
            "max_audits": 999999,
            "max_team_members": 5,
            "max_audits_per_month": 999999,
            "features": ["basic_reconciliation", "pdf_parsing", "team_members", "email_reports", "activity_log", "scheduled_reports"]
        },
        "enterprise": {
            "max_audits": 999999,
            "max_team_members": 999999,
            "max_audits_per_month": 999999,
            "features": ["everything"]
        }
    }
    
    limits_info = limits.get(current_tier, limits["free"])
    
    return {
        "current_tier": current_tier,
        "audit_count": audit_count,
        "team_count": team_count,
        "recent_audits": recent_audits,
        "max_audits": limits_info["max_audits"],
        "max_team_members": limits_info["max_team_members"],
        "max_audits_per_month": limits_info["max_audits_per_month"],
        "audit_percentage": min(100, (audit_count / limits_info["max_audits"]) * 100) if limits_info["max_audits"] < 999999 else 0,
        "team_percentage": min(100, (team_count / limits_info["max_team_members"]) * 100) if limits_info["max_team_members"] < 999999 else 0,
        "monthly_percentage": min(100, (recent_audits / limits_info["max_audits_per_month"]) * 100) if limits_info["max_audits_per_month"] < 999999 else 0,
        "needs_upgrade": current_tier == "free" and audit_count >= 8,
        "approaching_limit": current_tier == "free" and audit_count >= 5
    }

def display_usage_dashboard(firm_id):
    """Display usage dashboard in sidebar or main area"""
    
    stats = get_usage_stats(firm_id)
    
    if stats["current_tier"] == "free":
        st.markdown("### 📊 Your Usage")
        
        # Audit usage progress
        st.markdown("**Audits Used**")
        st.progress(stats["audit_percentage"] / 100)
        col1, col2 = st.columns(2)
        col1.metric("Used", stats["audit_count"])
        col2.metric("Limit", stats["max_audits"])
        
        if stats["needs_upgrade"]:
            st.warning(f"⚠️ You've used {stats['audit_count']} of {stats['max_audits']} free audits. Upgrade to continue!")
            if st.button("🚀 Upgrade Now", key="upgrade_usage"):
                st.session_state.page = "Settings"
                st.session_state.settings_tab_index = 2
                st.rerun()
        elif stats["approaching_limit"]:
            st.info(f"📈 You've used {stats['audit_count']} of {stats['max_audits']} free audits. Upgrade for unlimited audits.")
            if st.button("View Plans", key="view_plans_usage"):
                st.session_state.page = "Settings"
                st.session_state.settings_tab_index = 2
                st.rerun()
        
        st.markdown("---")
        st.markdown("**Team Members**")
        st.progress(stats["team_percentage"] / 100)
        col1, col2 = st.columns(2)
        col1.metric("Members", stats["team_count"])
        col2.metric("Limit", stats["max_team_members"])
    
    return stats

def display_upgrade_prompt():
    """Display upgrade prompt when user tries to use limited features"""
    
    st.markdown("### 🚀 Upgrade Your Plan")
    st.markdown("This feature is available on Professional and Enterprise plans.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Professional Plan**")
        st.markdown("$299/month")
        st.markdown("- ✅ Unlimited audits")
        st.markdown("- ✅ PDF bank parsing")
        st.markdown("- ✅ Up to 5 team members")
        st.markdown("- ✅ Email reports")
        st.markdown("- ✅ Activity logging")
    
    with col2:
        st.markdown("**Enterprise Plan**")
        st.markdown("$599/month")
        st.markdown("- ✅ Everything in Professional")
        st.markdown("- ✅ Unlimited team members")
        st.markdown("- ✅ Client portal access")
        st.markdown("- ✅ API access")
        st.markdown("- ✅ Priority support")
    
    if st.button("Upgrade Now", key="upgrade_prompt"):
        st.session_state.page = "Settings"
        st.session_state.settings_tab_index = 2
        st.rerun()