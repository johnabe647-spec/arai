import streamlit as st
from supabase import create_client
import secrets
import string
from datetime import datetime, timedelta

def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def generate_invite_token():
    """Generate a unique invite token"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(32))

def create_invite(firm_id, email, role, expires_days=7):
    """Create an invite link for a new team member"""
    supabase = get_supabase()
    
    token = generate_invite_token()
    expires_at = datetime.now() + timedelta(days=expires_days)
    
    try:
        # First, check if team_invites table exists by trying to select
        try:
            test_query = supabase.table("team_invites").select("count").limit(1).execute()
            print("team_invites table accessible")
        except Exception as table_err:
            print(f"team_invites table error: {table_err}")
            return False, f"Database error: {table_err}", None
        
        # Check if user already exists in the firm
        existing = supabase.table("users").select("*").eq("email", email.lower()).eq("firm_id", firm_id).execute()
        if existing.data:
            return False, "User already belongs to this firm", None
        
        # Prepare insert data
        insert_data = {
            "firm_id": firm_id,
            "email": email.lower(),
            "role": role,
            "token": token,
            "expires_at": expires_at.isoformat(),
            "used": False
        }
        
        print(f"Attempting to insert: {insert_data}")
        
        # Insert the invite
        result = supabase.table("team_invites").insert(insert_data).execute()
        
        print(f"Insert result: {result}")
        
        if result.data and len(result.data) > 0:
            # Use your actual Streamlit app URL
            app_url = "https://arai.africa.online.streamlit.app"
            invite_url = f"{app_url}?invite={token}"
            return True, invite_url, result.data[0]
        else:
            return False, "Failed to create invite - no data returned", None
            
    except Exception as e:
        print(f"Exception in create_invite: {e}")
        return False, f"Error: {str(e)}", None

def get_invite(token):
    """Get invite details by token"""
    supabase = get_supabase()
    
    try:
        result = supabase.table("team_invites").select("*, firms(*)").eq("token", token).eq("used", False).execute()
        if result.data:
            invite = result.data[0]
            # Check if expired
            expires_at = datetime.fromisoformat(invite["expires_at"].replace('Z', '+00:00'))
            if expires_at < datetime.now(expires_at.tzinfo):
                return None, "Invite has expired"
            return invite, None
        return None, "Invite not found or already used"
    except Exception as e:
        print(f"Error in get_invite: {e}")
        return None, str(e)

def accept_invite(token, user_id):
    """Mark invite as used"""
    supabase = get_supabase()
    
    try:
        supabase.table("team_invites").update({"used": True}).eq("token", token).execute()
        return True, None
    except Exception as e:
        print(f"Error in accept_invite: {e}")
        return False, str(e)

def get_team_members(firm_id):
    """Get all team members for a firm"""
    supabase = get_supabase()
    
    try:
        result = supabase.table("users").select("*").eq("firm_id", firm_id).execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error in get_team_members: {e}")
        return []

def remove_team_member(user_id, firm_id, current_user_role):
    """Remove a team member (owner only)"""
    if current_user_role != "owner":
        return False, "Only firm owner can remove team members"
    
    supabase = get_supabase()
    
    try:
        # Don't allow removing yourself
        user = supabase.table("users").select("*").eq("id", user_id).eq("firm_id", firm_id).execute()
        if not user.data:
            return False, "User not found"
        
        if user.data[0]["role"] == "owner":
            return False, "Cannot remove the firm owner"
        
        supabase.table("users").delete().eq("id", user_id).execute()
        return True, "Team member removed"
    except Exception as e:
        print(f"Error in remove_team_member: {e}")
        return False, str(e)

def update_user_role(user_id, firm_id, new_role, current_user_role):
    """Update a team member's role (owner only)"""
    if current_user_role != "owner":
        return False, "Only firm owner can change roles"
    
    supabase = get_supabase()
    
    try:
        supabase.table("users").update({"role": new_role}).eq("id", user_id).eq("firm_id", firm_id).execute()
        return True, f"Role updated to {new_role}"
    except Exception as e:
        print(f"Error in update_user_role: {e}")
        return False, str(e)