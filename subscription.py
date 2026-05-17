import streamlit as st
from supabase import create_client

def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def get_firm_subscription(firm_id):
    """Get subscription details for a firm"""
    supabase = get_supabase()
    
    try:
        result = supabase.table("firms").select("subscription_tier, subscription_status, subscription_end_date").eq("id", firm_id).execute()
        if result.data:
            return result.data[0]
        return {"subscription_tier": "free", "subscription_status": "active"}
    except Exception as e:
        print(f"Error getting subscription: {e}")
        return {"subscription_tier": "free", "subscription_status": "active"}

def update_subscription(firm_id, tier, status=None):
    """Update firm's subscription tier"""
    supabase = get_supabase()
    
    update_data = {"subscription_tier": tier}
    if status:
        update_data["subscription_status"] = status
    
    try:
        supabase.table("firms").update(update_data).eq("id", firm_id).execute()
        return True
    except Exception as e:
        print(f"Error updating subscription: {e}")
        return False

def check_feature_access(firm_id, feature):
    """Check if firm has access to a feature based on subscription"""
    # First, get the actual subscription tier from database
    supabase = get_supabase()
    result = supabase.table("firms").select("subscription_tier").eq("id", firm_id).execute()
    
    if result.data:
        tier = result.data[0].get("subscription_tier", "free")
    else:
        tier = "free"
    
    # Feature access by tier
    features = {
        "basic_reconciliation": ["free", "professional", "enterprise"],
        "pdf_parsing": ["professional", "enterprise"],
        "unlimited_audits": ["professional", "enterprise"],
        "team_members": ["professional", "enterprise"],
        "client_portal": ["enterprise"],
        "api_access": ["enterprise"],
        "priority_support": ["enterprise"],
        "email_reports": ["professional", "enterprise"],
        "custom_branding": ["enterprise"],
        "activity_log": ["professional", "enterprise"],
        "advanced_analytics": ["professional", "enterprise"],
        "scheduled_reports": ["professional", "enterprise"]
    }
    
    return feature in features.get(feature, []) and tier in features.get(feature, [])

def check_feature_access_with_prompt(firm_id, feature, feature_name=None):
    """Check feature access and show upgrade prompt if needed"""
    has_access = check_feature_access(firm_id, feature)
    
    if not has_access:
        display_name = feature_name if feature_name else feature.replace('_', ' ').title()
        st.info(f"🔒 **{display_name}** is available on Professional and Enterprise plans.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("View Plans", key=f"view_plans_{feature}"):
                st.session_state.page = "Settings"
                st.session_state.settings_tab_index = 2
                st.rerun()
        with col2:
            if st.button("Upgrade Now", key=f"upgrade_{feature}"):
                st.session_state.page = "Settings"
                st.session_state.settings_tab_index = 2
                st.rerun()
    
    return has_access

def get_subscription_tiers():
    """Return available subscription plans"""
    return {
        "free": {
            "name": "Free",
            "price": 0,
            "features": [
                "✅ Basic reconciliation",
                "✅ Up to 10 audits",
                "❌ PDF bank parsing",
                "❌ Team members",
                "❌ Email reports",
                "❌ Client portal",
                "❌ Priority support",
                "❌ Custom branding",
                "❌ Activity logging",
                "❌ Scheduled reports",
                "❌ Advanced analytics"
            ]
        },
        "professional": {
            "name": "Professional",
            "price": 299,
            "features": [
                "✅ Unlimited reconciliations",
                "✅ PDF bank parsing",
                "✅ Up to 5 team members",
                "✅ Email reports",
                "✅ Activity logging",
                "✅ Scheduled reports",
                "✅ Advanced analytics",
                "✅ Audit history",
                "❌ Client portal",
                "❌ Custom branding",
                "❌ Priority support"
            ]
        },
        "enterprise": {
            "name": "Enterprise",
            "price": 599,
            "features": [
                "✅ Everything in Professional",
                "✅ Unlimited team members",
                "✅ Client portal access",
                "✅ Custom branding",
                "✅ API access",
                "✅ Priority support",
                "✅ White-label reports",
                "✅ Dedicated account manager"
            ]
        }
    }

def get_feature_name(feature_key):
    """Get human-readable feature name"""
    feature_names = {
        "basic_reconciliation": "Basic Reconciliation",
        "pdf_parsing": "PDF Bank Parsing",
        "unlimited_audits": "Unlimited Audits",
        "team_members": "Team Members",
        "client_portal": "Client Portal",
        "api_access": "API Access",
        "priority_support": "Priority Support",
        "email_reports": "Email Reports",
        "custom_branding": "Custom Branding",
        "activity_log": "Activity Logging",
        "advanced_analytics": "Advanced Analytics",
        "scheduled_reports": "Scheduled Reports"
    }
    return feature_names.get(feature_key, feature_key.replace('_', ' ').title())