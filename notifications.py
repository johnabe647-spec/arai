import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd

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
    
    try:
        query = supabase.table("notifications").select("*").eq("firm_id", firm_id)
        
        if user_id:
            query = query.eq("user_id", user_id)
        if unread_only:
            query = query.eq("is_read", False)
        
        result = query.order("created_at", desc=True).limit(limit).execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error in get_notifications: {e}")
        return []

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
    
    try:
        query = supabase.table("notifications").update({"is_read": True}).eq("firm_id", firm_id)
        if user_id:
            query = query.eq("user_id", user_id)
        
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

def display_notification_center(firm_id, user_email):
    """Display notification center in the sidebar"""
    
    # Get all notifications for this firm (no user filter)
    notifications = get_notifications(firm_id, limit=20)
    unread_notifications = [n for n in notifications if not n.get('is_read', False)]
    unread_count = len(unread_notifications)
    
    # Display header with count
    if unread_count > 0:
        st.markdown(f"### 🔔 Notifications ({unread_count} new)")
    else:
        st.markdown("### 🔔 Notifications")
    
    # Mark all as read button
    if unread_count > 0:
        if st.button("✓ Mark All as Read", key="mark_all_notifications"):
            mark_all_notifications_read(firm_id)
            st.rerun()
    
    st.markdown("---")
    
    # Display notifications
    if notifications:
        for notif in notifications:
            # Format the time
            created_at = notif.get('created_at', '')
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    time_str = dt.strftime('%b %d, %H:%M')
                except:
                    time_str = "recent"
            else:
                time_str = "recent"
            
            # Color based on type
            if notif['type'] == 'success':
                icon = "✅"
                bg_color = "#d4edda"
                border_color = "#28a745"
            elif notif['type'] == 'warning':
                icon = "⚠️"
                bg_color = "#fff3cd"
                border_color = "#ffc107"
            elif notif['type'] == 'error':
                icon = "🔴"
                bg_color = "#f8d7da"
                border_color = "#dc3545"
            else:
                icon = "ℹ️"
                bg_color = "#e2e3e5"
                border_color = "#6c757d"
            
            # Style based on read status
            is_read = notif.get('is_read', False)
            opacity = "0.6" if is_read else "1"
            
            st.markdown(f"""
            <div style="background-color: {bg_color}; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 4px solid {border_color}; opacity: {opacity};">
                <div style="font-weight: bold;">
                    {icon} {notif['title']}
                </div>
                <div style="font-size: 0.85rem; margin: 5px 0;">
                    {notif['message']}
                </div>
                <div style="font-size: 0.7rem; color: #666;">
                    🕐 {time_str}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Action buttons
            col1, col2 = st.columns(2)
            with col1:
                if not is_read:
                    if st.button(f"✓ Read", key=f"mark_{notif['id']}"):
                        mark_notification_read(notif['id'])
                        st.rerun()
            with col2:
                if st.button(f"🗑️ Delete", key=f"del_{notif['id']}"):
                    delete_notification(notif['id'])
                    st.rerun()
            
            st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)
    else:
        st.info("No notifications")

def create_audit_notifications(firm_id, filename, match_rate, anomaly_count, fraud_risk):
    """Create notifications based on audit results"""
    
    # Create audit completion notification
    create_notification(
        firm_id=firm_id,
        title="✅ Audit Complete",
        message=f"Audit of {filename} completed with {match_rate:.1%} match rate",
        notification_type="success"
    )
    
    # Create anomaly notification if anomalies found
    if anomaly_count > 0:
        create_notification(
            firm_id=firm_id,
            title="⚠️ Anomalies Detected",
            message=f"Found {anomaly_count} suspicious transactions requiring review",
            notification_type="warning"
        )
    
    # Create high fraud risk notification
    if fraud_risk > 70:
        create_notification(
            firm_id=firm_id,
            title="🔴 High Fraud Risk Alert",
            message=f"Fraud risk score of {fraud_risk:.0f}% detected. Immediate review recommended.",
            notification_type="error"
        )