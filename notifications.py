import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
import json

def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def create_notification(firm_id, title, message, notification_type="info", user_id=None, action_url=None):
    """Create a new notification for a firm"""
    supabase = get_supabase()
    
    try:
        result = supabase.table("notifications").insert({
            "firm_id": firm_id,
            "user_id": user_id,
            "title": title,
            "message": message,
            "type": notification_type,
            "action_url": action_url,
            "is_read": False
        }).execute()
        return True, result.data[0] if result.data else None
    except Exception as e:
        print(f"Error creating notification: {e}")
        return False, None

def get_notifications(firm_id, user_id=None, limit=50, unread_only=False):
    """Get notifications for a firm/user"""
    supabase = get_supabase()
    
    query = supabase.table("notifications").select("*").eq("firm_id", firm_id)
    
    if user_id:
        query = query.eq("user_id", user_id)
    if unread_only:
        query = query.eq("is_read", False)
    
    result = query.order("created_at", desc=True).limit(limit).execute()
    return result.data if result.data else []

def mark_notification_read(notification_id):
    """Mark a notification as read"""
    supabase = get_supabase()
    
    try:
        supabase.table("notifications").update({"is_read": True}).eq("id", notification_id).execute()
        return True
    except Exception as e:
        print(f"Error marking notification read: {e}")
        return False

def mark_all_notifications_read(firm_id, user_id=None):
    """Mark all notifications as read for a firm"""
    supabase = get_supabase()
    
    query = supabase.table("notifications").update({"is_read": True}).eq("firm_id", firm_id)
    if user_id:
        query = query.eq("user_id", user_id)
    
    try:
        query.execute()
        return True
    except Exception as e:
        print(f"Error marking all notifications read: {e}")
        return False

def delete_notification(notification_id):
    """Delete a notification"""
    supabase = get_supabase()
    
    try:
        supabase.table("notifications").delete().eq("id", notification_id).execute()
        return True
    except Exception as e:
        print(f"Error deleting notification: {e}")
        return False

def get_notification_preferences(firm_id, user_id=None):
    """Get notification preferences for a firm/user"""
    supabase = get_supabase()
    
    try:
        query = supabase.table("notification_preferences").select("*").eq("firm_id", firm_id)
        if user_id:
            query = query.eq("user_id", user_id)
        result = query.execute()
        
        if result.data:
            return result.data[0]
        else:
            # Create default preferences
            default = {
                "firm_id": firm_id,
                "user_id": user_id,
                "email_notifications": True,
                "browser_notifications": True,
                "audit_completed": True,
                "anomaly_detected": True,
                "report_ready": True,
                "schedule_reminder": True
            }
            if user_id:
                default["user_id"] = user_id
            supabase.table("notification_preferences").insert(default).execute()
            return default
    except Exception as e:
        print(f"Error getting preferences: {e}")
        return {
            "email_notifications": True,
            "browser_notifications": True,
            "audit_completed": True,
            "anomaly_detected": True,
            "report_ready": True,
            "schedule_reminder": True
        }

def update_notification_preferences(firm_id, user_id, preferences):
    """Update notification preferences"""
    supabase = get_supabase()
    
    try:
        # Check if exists
        existing = supabase.table("notification_preferences").select("*").eq("firm_id", firm_id).eq("user_id", user_id).execute()
        
        if existing.data:
            supabase.table("notification_preferences").update(preferences).eq("firm_id", firm_id).eq("user_id", user_id).execute()
        else:
            preferences["firm_id"] = firm_id
            preferences["user_id"] = user_id
            supabase.table("notification_preferences").insert(preferences).execute()
        
        return True
    except Exception as e:
        print(f"Error updating preferences: {e}")
        return False

def display_notification_center(firm_id, user_email):
    """Display notification center in the sidebar"""
    
    unread_count = len(get_notifications(firm_id, unread_only=True))
    
    # Get user_id from email
    supabase = get_supabase()
    user_result = supabase.table("users").select("id").eq("email", user_email).execute()
    user_id = user_result.data[0]["id"] if user_result.data else None
    
    # Notification bell in sidebar
    with st.sidebar:
        st.markdown("---")
        
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown("### 🔔 Notifications")
        with col2:
            if unread_count > 0:
                st.markdown(f"**{unread_count} new**")
        
        notifications = get_notifications(firm_id, user_id, limit=10)
        
        if notifications:
            for notif in notifications:
                with st.container():
                    # Color based on type
                    if notif['type'] == 'success':
                        icon = "✅"
                    elif notif['type'] == 'warning':
                        icon = "⚠️"
                    elif notif['type'] == 'error':
                        icon = "🔴"
                    else:
                        icon = "ℹ️"
                    
                    # Style based on read status
                    if not notif['is_read']:
                        st.markdown(f"**{icon} {notif['title']}**")
                    else:
                        st.markdown(f"{icon} {notif['title']}")
                    
                    st.caption(notif['message'][:100])
                    st.caption(f"🕐 {notif['created_at'][:16].replace('T', ' ')}")
                    
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col1:
                        if not notif['is_read']:
                            if st.button(f"Read", key=f"mark_{notif['id']}"):
                                mark_notification_read(notif['id'])
                                st.rerun()
                    with col2:
                        if st.button(f"🗑️", key=f"del_{notif['id']}"):
                            delete_notification(notif['id'])
                            st.rerun()
                    
                    st.markdown("---")
            
            if unread_count > 0:
                if st.button("Mark All as Read"):
                    mark_all_notifications_read(firm_id, user_id)
                    st.rerun()
        else:
            st.info("No notifications")