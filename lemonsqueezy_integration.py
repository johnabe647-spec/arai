import streamlit as st
import requests
import json
from supabase import create_client
from datetime import datetime

def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def create_checkout_url(firm_id, variant_id, user_email):
    """Create a Lemon Squeezy checkout URL for subscription"""
    
    api_key = st.secrets["LEMONSQUEEZY_API_KEY"]
    store_id = st.secrets["LEMONSQUEEZY_STORE_ID"]
    app_url = st.secrets.get("APP_URL", "https://arai.africa.online.streamlit.app")
    
    # Lemon Squeezy API endpoint
    url = "https://api.lemonsqueezy.com/v1/checkouts"
    
    headers = {
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "data": {
            "type": "checkouts",
            "attributes": {
                "checkout_data": {
                    "email": user_email,
                    "custom": {
                        "firm_id": str(firm_id)
                    }
                },
                "checkout_options": {
                    "embed": False,
                    "dark": False,
                    "logo": True,
                    "discount": True
                },
                "product_options": {
                    "enabled_variants": [int(variant_id)],
                    "redirect_url": f"{app_url}?checkout_success=true",
                    "receipt_button_text": "Return to ARAI",
                    "receipt_thank_you_note": "Thank you for upgrading! Your subscription is now active."
                }
            },
            "relationships": {
                "store": {
                    "data": {
                        "type": "stores",
                        "id": str(store_id)
                    }
                },
                "variant": {
                    "data": {
                        "type": "variants",
                        "id": str(variant_id)
                    }
                }
            }
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        checkout_url = result["data"]["attributes"]["url"]
        
        return True, checkout_url
    except Exception as e:
        return False, str(e)

def create_customer_portal_url(customer_id, return_url):
    """Create customer portal URL for managing subscriptions"""
    
    api_key = st.secrets["LEMONSQUEEZY_API_KEY"]
    store_id = st.secrets["LEMONSQUEEZY_STORE_ID"]
    
    url = "https://api.lemonsqueezy.com/v1/customer-portals"
    
    headers = {
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "data": {
            "type": "customer-portals",
            "relationships": {
                "customer": {
                    "data": {
                        "type": "customers",
                        "id": str(customer_id)
                    }
                },
                "store": {
                    "data": {
                        "type": "stores",
                        "id": str(store_id)
                    }
                }
            },
            "attributes": {
                "redirect_url": return_url
            }
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        portal_url = result["data"]["attributes"]["url"]
        
        return True, portal_url
    except Exception as e:
        return False, str(e)

def get_subscription_status(firm_id):
    """Get current subscription status from database"""
    supabase = get_supabase()
    
    try:
        result = supabase.table("firms").select(
            "subscription_tier, subscription_status, lemonsqueezy_customer_id, subscription_end_date"
        ).eq("id", firm_id).execute()
        
        if result.data:
            return result.data[0]
        return {"subscription_tier": "free", "subscription_status": "active"}
    except Exception as e:
        return {"subscription_tier": "free", "subscription_status": "active"}

def update_subscription(firm_id, tier, status, customer_id=None, end_date=None):
    """Update subscription in database"""
    supabase = get_supabase()
    
    update_data = {
        "subscription_tier": tier,
        "subscription_status": status
    }
    
    if customer_id:
        update_data["lemonsqueezy_customer_id"] = customer_id
    if end_date:
        update_data["subscription_end_date"] = end_date
    
    try:
        supabase.table("firms").update(update_data).eq("id", firm_id).execute()
        return True
    except Exception as e:
        print(f"Error updating subscription: {e}")
        return False

def display_payment_options(firm_id, user_email):
    """Display payment options in subscription settings"""
    
    current = get_subscription_status(firm_id)
    current_tier = current.get("subscription_tier", "free")
    
    st.markdown("### 💳 Payment & Subscription")
    
    if current_tier == "free":
        st.markdown("#### Upgrade Your Plan")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Professional Plan**")
            st.markdown("$299/month")
            st.markdown("- Unlimited audits")
            st.markdown("- PDF bank parsing")
            st.markdown("- Up to 5 team members")
            st.markdown("- Email reports")
            st.markdown("- Activity logging")
            
            if st.button("💳 Upgrade to Professional", key="btn_professional"):
                with st.spinner("Preparing checkout..."):
                    variant_id = st.secrets["LEMONSQUEEZY_PROFESSIONAL_VARIANT_ID"]
                    success, result = create_checkout_url(firm_id, variant_id, user_email)
                    
                    if success:
                        st.markdown(f'<meta http-equiv="refresh" content="0;url={result}">', unsafe_allow_html=True)
                        st.success("Redirecting to secure checkout...")
                        st.write(f"Click [here]({result}) if not redirected")
                    else:
                        st.error(f"Error: {result}")
        
        with col2:
            st.markdown("**Enterprise Plan**")
            st.markdown("$599/month")
            st.markdown("- Everything in Professional")
            st.markdown("- Unlimited team members")
            st.markdown("- Client portal access")
            st.markdown("- API access")
            st.markdown("- Priority support")
            st.markdown("- Custom branding")
            
            if st.button("💳 Upgrade to Enterprise", key="btn_enterprise"):
                with st.spinner("Preparing checkout..."):
                    variant_id = st.secrets["LEMONSQUEEZY_ENTERPRISE_VARIANT_ID"]
                    success, result = create_checkout_url(firm_id, variant_id, user_email)
                    
                    if success:
                        st.markdown(f'<meta http-equiv="refresh" content="0;url={result}">', unsafe_allow_html=True)
                        st.success("Redirecting to secure checkout...")
                        st.write(f"Click [here]({result}) if not redirected")
                    else:
                        st.error(f"Error: {result}")
    
    elif current_tier == "professional":
        st.success("✅ You are on the **Professional Plan**")
        st.markdown(f"Status: {current.get('subscription_status', 'active')}")
        
        if current.get('lemonsqueezy_customer_id'):
            if st.button("🔧 Manage Subscription", key="manage_sub"):
                with st.spinner("Redirecting to customer portal..."):
                    success, url = create_customer_portal_url(
                        current['lemonsqueezy_customer_id'],
                        st.secrets.get("APP_URL", "https://arai.africa.online.streamlit.app")
                    )
                    if success:
                        st.markdown(f'<meta http-equiv="refresh" content="0;url={url}">', unsafe_allow_html=True)
                        st.success("Redirecting to customer portal...")
                    else:
                        st.error(f"Error: {url}")
        
        if st.button("Downgrade to Free", key="downgrade"):
            update_subscription(firm_id, "free", "canceled")
            st.success("Downgraded to Free plan. Your subscription will end at the current billing period.")
            st.rerun()
    
    elif current_tier == "enterprise":
        st.success("✅ You are on the **Enterprise Plan**")
        st.markdown(f"Status: {current.get('subscription_status', 'active')}")
        
        if current.get('lemonsqueezy_customer_id'):
            if st.button("🔧 Manage Subscription", key="manage_sub_enterprise"):
                with st.spinner("Redirecting to customer portal..."):
                    success, url = create_customer_portal_url(
                        current['lemonsqueezy_customer_id'],
                        st.secrets.get("APP_URL", "https://arai.africa.online.streamlit.app")
                    )
                    if success:
                        st.markdown(f'<meta http-equiv="refresh" content="0;url={url}">', unsafe_allow_html=True)
                        st.success("Redirecting to customer portal...")
                    else:
                        st.error(f"Error: {url}")
        
        if st.button("Contact Sales", key="contact_sales"):
            st.info("📧 Email sales@arai.africa for custom enterprise arrangements")
    
    st.markdown("---")
    st.caption("Secure payments powered by Lemon Squeezy")

def handle_checkout_success():
    """Handle successful checkout redirect"""
    if st.query_params.get("checkout_success"):
        st.success("✅ Payment successful! Your subscription has been activated.")
        # Clear the query parameter
        st.query_params.clear()
        st.rerun()