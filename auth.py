import streamlit as st
from supabase import create_client
import hashlib
import re

def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def register_firm(firm_name, email, password):
    supabase = get_supabase()
    
    if not firm_name or not email or not password:
        return False, "All fields are required"
    
    email = email.lower()
    
    if not validate_email(email):
        return False, "Invalid email format"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    
    try:
        # Check if firm already exists
        existing = supabase.table("firms").select("*").eq("email", email).execute()
        if existing.data:
            return False, "A firm with this email already exists"
        
        # Create firm
        firm_result = supabase.table("firms").insert({
            "name": firm_name,
            "email": email,
            "subscription_tier": "free"
        }).execute()
        
        if not firm_result.data:
            return False, "Failed to create firm"
        
        firm_id = firm_result.data[0]["id"]
        
        # Create owner user
        user_result = supabase.table("users").insert({
            "firm_id": firm_id,
            "email": email,
            "password_hash": hash_password(password),
            "role": "owner"
        }).execute()
        
        if not user_result.data:
            supabase.table("firms").delete().eq("id", firm_id).execute()
            return False, "Failed to create user"
        
        return True, firm_id
        
    except Exception as e:
        return False, str(e)

def login_user(email, password):
    supabase = get_supabase()
    
    try:
        email = email.lower()
        
        user_result = supabase.table("users").select("*, firms(*)").eq("email", email).execute()
        
        if not user_result.data:
            return False, "User not found", None, None
        
        user = user_result.data[0]
        
        if user["password_hash"] != hash_password(password):
            return False, "Invalid password", None, None
        
        firm = user.get("firms", {})
        return True, "Login successful", firm["id"], user["role"]
        
    except Exception as e:
        return False, str(e), None, None

def register_user_for_existing_firm(email, password, firm_id, role, invite_token):
    """Register a new user for an existing firm via invite"""
    supabase = get_supabase()
    
    email = email.lower()
    
    if not validate_email(email):
        return False, "Invalid email format"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    
    try:
        # Check if user already exists
        existing = supabase.table("users").select("*").eq("email", email).execute()
        if existing.data:
            return False, "User already exists"
        
        # Create user for existing firm
        user_result = supabase.table("users").insert({
            "firm_id": firm_id,
            "email": email,
            "password_hash": hash_password(password),
            "role": role
        }).execute()
        
        if not user_result.data:
            return False, "Failed to create user"
        
        # Mark invite as used
        from team import accept_invite
        accept_invite(invite_token, user_result.data[0]["id"])
        
        return True, user_result.data[0]["id"]
        
    except Exception as e:
        return False, str(e)

def get_firm_audits(firm_id, limit=50):
    supabase = get_supabase()
    
    try:
        result = supabase.table("audits").select("*").eq("firm_id", firm_id).order("created_at", desc=True).limit(limit).execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error getting audits: {e}")
        return []

def save_audit(firm_id, filename, match_rate, fraud_risk, predicted_hours, audit_data):
    supabase = get_supabase()
    
    try:
        result = supabase.table("audits").insert({
            "firm_id": firm_id,
            "filename": filename,
            "match_rate": match_rate,
            "fraud_risk": fraud_risk,
            "predicted_hours": predicted_hours,
            "audit_data": audit_data
        }).execute()
        
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error saving audit: {e}")
        return None

def get_firm_stats(firm_id):
    audits = get_firm_audits(firm_id, limit=1000)
    
    if not audits:
        return {
            "total_audits": 0,
            "avg_match_rate": 0,
            "avg_fraud_risk": 0,
            "total_time_saved": 0
        }
    
    total_audits = len(audits)
    avg_match_rate = sum(a.get("match_rate", 0) for a in audits) / total_audits
    avg_fraud_risk = sum(a.get("fraud_risk", 0) for a in audits) / total_audits
    total_time_saved = total_audits * 15
    
    return {
        "total_audits": total_audits,
        "avg_match_rate": avg_match_rate,
        "avg_fraud_risk": avg_fraud_risk,
        "total_time_saved": total_time_saved
    }