import streamlit as st
from supabase import create_client
import hashlib
from datetime import datetime

def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_client(firm_id, client_name, client_email, client_company, password):
    """Create a new client for a firm"""
    supabase = get_supabase()
    
    try:
        # Check if client exists
        existing = supabase.table("clients").select("*").eq("client_email", client_email.lower()).execute()
        if existing.data:
            return False, "Client with this email already exists"
        
        # Create client
        result = supabase.table("clients").insert({
            "firm_id": firm_id,
            "client_name": client_name,
            "client_email": client_email.lower(),
            "client_company": client_company,
            "password_hash": hash_password(password)
        }).execute()
        
        return True, result.data[0] if result.data else None
    except Exception as e:
        return False, str(e)

def get_clients(firm_id):
    """Get all clients for a firm"""
    supabase = get_supabase()
    
    try:
        result = supabase.table("clients").select("*").eq("firm_id", firm_id).execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error in get_clients: {e}")
        return []

def get_client_reports(client_id):
    """Get all reports shared with a client"""
    supabase = get_supabase()
    
    try:
        result = supabase.table("client_reports").select("*, audits(*)").eq("client_id", client_id).execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error in get_client_reports: {e}")
        return []

def share_report_with_client(client_id, audit_id):
    """Share an audit report with a client"""
    supabase = get_supabase()
    
    try:
        result = supabase.table("client_reports").insert({
            "client_id": client_id,
            "audit_id": audit_id,
            "shared_at": datetime.now().isoformat(),
            "viewed": False
        }).execute()
        return True, result.data[0] if result.data else None
    except Exception as e:
        return False, str(e)

def login_client(email, password):
    """Login client and return client data"""
    supabase = get_supabase()
    
    try:
        email = email.lower()
        result = supabase.table("clients").select("*, firms(*)").eq("client_email", email).execute()
        
        if not result.data:
            return False, "Client not found", None
        
        client = result.data[0]
        
        if client["password_hash"] != hash_password(password):
            return False, "Invalid password", None
        
        return True, "Login successful", client
    except Exception as e:
        return False, str(e), None