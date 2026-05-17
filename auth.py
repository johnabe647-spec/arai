import streamlit as st
from supabase import create_client
import hashlib
import re
from two_factor_auth import verify_totp, verify_backup_code, get_device_id, trust_device, is_trusted_device, record_login_attempt, get_recent_failed_attempts

def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def register_firm(firm_name, email, password):
    """Register a new audit firm with owner account"""
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
        
        # Create owner user (2FA disabled by default)
        user_result = supabase.table("users").insert({
            "firm_id": firm_id,
            "email": email,
            "password_hash": hash_password(password),
            "role": "owner",
            "two_factor_enabled": False,
            "two_factor_secret": None,
            "backup_codes": None,
            "trusted_devices": []
        }).execute()
        
        if not user_result.data:
            supabase.table("firms").delete().eq("id", firm_id).execute()
            return False, "Failed to create user"
        
        return True, firm_id
        
    except Exception as e:
        return False, str(e)

def login_user(email, password, two_factor_code=None, is_backup_code=False, device_id=None, device_name=None):
    """Login user with optional 2FA support"""
    supabase = get_supabase()
    
    try:
        email = email.lower()
        
        # Record login attempt start
        record_login_attempt(email, False)
        
        # Check for too many failed attempts (rate limiting)
        recent_failures = get_recent_failed_attempts(email, minutes=15)
        if recent_failures >= 5:
            return False, "Too many failed attempts. Please try again later.", None, None
        
        # Find user
        user_result = supabase.table("users").select("*, firms(*)").eq("email", email).execute()
        
        if not user_result.data:
            record_login_attempt(email, False)
            return False, "User not found", None, None
        
        user = user_result.data[0]
        
        # Verify password
        if user["password_hash"] != hash_password(password):
            record_login_attempt(email, False)
            return False, "Invalid password", None, None
        
        # Check if 2FA is enabled
        if user.get("two_factor_enabled", False):
            # Check if device is trusted (skip 2FA for trusted devices)
            if device_id and is_trusted_device(user["id"], device_id):
                record_login_attempt(email, True)
                firm = user.get("firms", {})
                return True, "Login successful (trusted device)", firm.get("id"), user.get("role")
            
            # 2FA required - need verification code
            if not two_factor_code:
                return False, "2FA_REQUIRED", None, None
            
            # Verify TOTP or backup code
            if is_backup_code:
                if not verify_backup_code(user["id"], two_factor_code):
                    record_login_attempt(email, False)
                    return False, "Invalid backup code", None, None
            else:
                secret = user.get("two_factor_secret")
                if not secret or not verify_totp(secret, two_factor_code):
                    record_login_attempt(email, False)
                    return False, "Invalid verification code", None, None
            
            # Trust this device if requested
            if device_id and device_name:
                trust_device(user["id"], device_id, device_name)
        
        # Login successful
        record_login_attempt(email, True)
        firm = user.get("firms", {})
        return True, "Login successful", firm.get("id"), user.get("role")
        
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
        
        # Create user for existing firm (2FA disabled by default)
        user_result = supabase.table("users").insert({
            "firm_id": firm_id,
            "email": email,
            "password_hash": hash_password(password),
            "role": role,
            "two_factor_enabled": False,
            "two_factor_secret": None,
            "backup_codes": None,
            "trusted_devices": []
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
    """Get all audits for a specific firm"""
    supabase = get_supabase()
    
    try:
        result = supabase.table("audits").select("*").eq("firm_id", firm_id).order("created_at", desc=True).limit(limit).execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error getting audits: {e}")
        return []

def save_audit(firm_id, filename, match_rate, fraud_risk, predicted_hours, audit_data):
    """Save audit results to database"""
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
    """Get summary statistics for a firm"""
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
    total_time_saved = total_audits * 15  # Estimate 15 hours saved per audit
    
    return {
        "total_audits": total_audits,
        "avg_match_rate": avg_match_rate,
        "avg_fraud_risk": avg_fraud_risk,
        "total_time_saved": total_time_saved
    }

def get_user_2fa_status(user_id):
    """Get 2FA status for a user"""
    supabase = get_supabase()
    
    try:
        result = supabase.table("users").select("two_factor_enabled").eq("id", user_id).execute()
        if result.data:
            return result.data[0].get("two_factor_enabled", False)
        return False
    except Exception as e:
        print(f"Error getting 2FA status: {e}")
        return False