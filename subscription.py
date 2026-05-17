import streamlit as st
from supabase import create_client
import stripe

# Initialize Stripe (add your keys to secrets later)
def get_stripe_keys():
    try:
        return {
            "public_key": st.secrets["STRIPE_PUBLIC_KEY"],
            "secret_key": st.secrets["STRIPE_SECRET_KEY"]
        }
    except:
        return None

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
    sub = get_firm_subscription(firm_id)
    tier = sub.get("subscription_tier", "free")
    
    # Feature access by tier
    features = {
        "basic_reconciliation": ["free", "professional", "enterprise"],
        "pdf_parsing": ["professional", "enterprise"],
        "unlimited_audits": ["professional", "enterprise"],
        "team_members": ["professional", "enterprise"],
        "client_portal": ["enterprise"],
        "api_access": ["enterprise"],
        "priority_support": ["enterprise"]
    }
    
    return feature in features.get(feature, []) and tier in features.get(feature, [])

def get_subscription_tiers():
    """Return available subscription plans"""
    return {
        "free": {
            "name": "Free",
            "price": 0,
            "price_id": None,
            "features": [
                "✅ Basic reconciliation",
                "✅ Up to 10 audits",
                "✅ 1 team member",
                "❌ PDF bank parsing",
                "❌ Team members",
                "❌ Client portal",
                "❌ Priority support"
            ]
        },
        "professional": {
            "name": "Professional",
            "price": 299,
            "price_id": "price_professional",  # Replace with actual Stripe price ID
            "features": [
                "✅ Unlimited reconciliations",
                "✅ PDF bank parsing",
                "✅ Up to 5 team members",
                "✅ Email reports",
                "✅ Audit history",
                "❌ Client portal",
                "❌ Priority support"
            ]
        },
        "enterprise": {
            "name": "Enterprise",
            "price": 599,
            "price_id": "price_enterprise",  # Replace with actual Stripe price ID
            "features": [
                "✅ Everything in Professional",
                "✅ Unlimited team members",
                "✅ Client portal access",
                "✅ API access",
                "✅ Priority support",
                "✅ Custom branding",
                "✅ Dedicated account manager"
            ]
        }
    }