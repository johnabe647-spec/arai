import streamlit as st
from supabase import create_client
import tempfile
import os

def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def save_firm_logo(firm_id, logo_file):
    """Save firm logo to Supabase storage"""
    supabase = get_supabase()
    
    try:
        # Upload to storage
        file_ext = logo_file.name.split('.')[-1]
        file_path = f"logos/{firm_id}/logo.{file_ext}"
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(logo_file.getvalue())
            tmp_path = tmp.name
        
        with open(tmp_path, 'rb') as f:
            supabase.storage.from_("firm-assets").upload(file_path, f)
        
        os.unlink(tmp_path)
        
        # Get public URL
        public_url = supabase.storage.from_("firm-assets").get_public_url(file_path)
        
        # Update firms table
        supabase.table("firms").update({"logo_url": public_url}).eq("id", firm_id).execute()
        
        return True, public_url
    except Exception as e:
        return False, str(e)

def get_firm_branding(firm_id):
    """Get branding settings for a firm"""
    supabase = get_supabase()
    
    try:
        result = supabase.table("firms").select("logo_url, primary_color, secondary_color, footer_text, custom_branding").eq("id", firm_id).execute()
        if result.data:
            return result.data[0]
        return {
            "logo_url": None,
            "primary_color": "#1f77b4",
            "secondary_color": "#4ecdc4",
            "footer_text": None,
            "custom_branding": False
        }
    except Exception as e:
        print(f"Error getting branding: {e}")
        return {
            "logo_url": None,
            "primary_color": "#1f77b4",
            "secondary_color": "#4ecdc4",
            "footer_text": None,
            "custom_branding": False
        }

def update_branding(firm_id, primary_color=None, secondary_color=None, footer_text=None):
    """Update firm branding settings"""
    supabase = get_supabase()
    
    update_data = {}
    if primary_color:
        update_data["primary_color"] = primary_color
    if secondary_color:
        update_data["secondary_color"] = secondary_color
    if footer_text is not None:
        update_data["footer_text"] = footer_text
        update_data["custom_branding"] = True
    
    try:
        supabase.table("firms").update(update_data).eq("id", firm_id).execute()
        return True
    except Exception as e:
        print(f"Error updating branding: {e}")
        return False

def remove_logo(firm_id):
    """Remove firm logo"""
    supabase = get_supabase()
    
    try:
        supabase.table("firms").update({"logo_url": None}).eq("id", firm_id).execute()
        return True
    except Exception as e:
        print(f"Error removing logo: {e}")
        return False