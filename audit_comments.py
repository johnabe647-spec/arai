import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd
import re

def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def add_comment(audit_id, firm_id, user_email, comment_text, transaction_id=None, parent_comment_id=None):
    """Add a comment to an audit"""
    supabase = get_supabase()
    
    try:
        result = supabase.table("audit_comments").insert({
            "audit_id": audit_id,
            "firm_id": firm_id,
            "user_email": user_email,
            "transaction_id": transaction_id,
            "comment_text": comment_text,
            "status": "open",
            "parent_comment_id": parent_comment_id
        }).execute()
        
        # Check for @mentions
        mentions = re.findall(r'@(\w+)', comment_text)
        for mention in mentions:
            supabase.table("comment_mentions").insert({
                "comment_id": result.data[0]["id"],
                "mentioned_email": mention
            }).execute()
        
        return True, result.data[0] if result.data else None
    except Exception as e:
        return False, str(e)

def get_comments(audit_id, transaction_id=None):
    """Get comments for an audit or specific transaction"""
    supabase = get_supabase()
    
    try:
        query = supabase.table("audit_comments").select("*").eq("audit_id", audit_id).order("created_at", desc=False)
        
        if transaction_id:
            query = query.eq("transaction_id", transaction_id)
        
        result = query.execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error getting comments: {e}")
        return []

def update_comment_status(comment_id, status):
    """Update comment status (open, resolved, flagged)"""
    supabase = get_supabase()
    
    try:
        supabase.table("audit_comments").update({
            "status": status,
            "updated_at": datetime.now().isoformat()
        }).eq("id", comment_id).execute()
        return True
    except Exception as e:
        return False

def delete_comment(comment_id):
    """Delete a comment"""
    supabase = get_supabase()
    
    try:
        supabase.table("audit_comments").delete().eq("id", comment_id).execute()
        return True
    except Exception as e:
        return False

def get_comment_summary(audit_id):
    """Get summary of comments for an audit"""
    comments = get_comments(audit_id)
    
    if not comments:
        return {
            "total": 0,
            "open": 0,
            "resolved": 0,
            "flagged": 0,
            "transaction_comments": 0,
            "general_comments": 0
        }
    
    return {
        "total": len(comments),
        "open": sum(1 for c in comments if c.get("status") == "open"),
        "resolved": sum(1 for c in comments if c.get("status") == "resolved"),
        "flagged": sum(1 for c in comments if c.get("status") == "flagged"),
        "transaction_comments": sum(1 for c in comments if c.get("transaction_id")),
        "general_comments": sum(1 for c in comments if not c.get("transaction_id"))
    }

def display_comments_section(audit_id, firm_id, user_email, transaction_id=None, transaction_data=None):
    """Display comments section for an audit or transaction"""
    
    comments = get_comments(audit_id, transaction_id)
    summary = get_comment_summary(audit_id) if not transaction_id else None
    
    if transaction_id and transaction_data:
        st.markdown(f"#### 💬 Comments on Transaction: {transaction_data.get('date', 'Unknown')} - ${transaction_data.get('amount', 0):,.2f}")
    else:
        st.markdown("#### 💬 Audit Comments")
        if summary:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total", summary["total"])
            col2.metric("Open", summary["open"])
            col3.metric("Resolved", summary["resolved"])
            col4.metric("Flagged", summary["flagged"])
        st.markdown("---")
    
    # Add new comment form
    with st.form(key=f"comment_form_{transaction_id or 'general'}"):
        comment_text = st.text_area("Add a comment", placeholder="Type your comment here... Use @username to mention team members", height=100)
        
        col1, col2 = st.columns([1, 5])
        with col1:
            submitted = st.form_submit_button("Post Comment", type="primary")
        
        if submitted and comment_text:
            success, result = add_comment(audit_id, firm_id, user_email, comment_text, transaction_id)
            if success:
                st.success("Comment added!")
                st.rerun()
            else:
                st.error(f"Error: {result}")
    
    st.markdown("---")
    
    # Display existing comments
    if comments:
        st.markdown("#### Previous Comments")
        for comment in comments:
            with st.container():
                # Determine status color
                status_colors = {
                    "open": "🔵 Open",
                    "resolved": "🟢 Resolved",
                    "flagged": "🔴 Flagged"
                }
                status_text = status_colors.get(comment.get("status"), "⚪ Open")
                
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{comment['user_email'].split('@')[0]}** - *{status_text}*")
                    st.caption(comment['created_at'][:16].replace('T', ' '))
                    st.write(comment['comment_text'])
                
                with col2:
                    if comment.get("status") != "resolved":
                        if st.button("✓ Resolve", key=f"resolve_{comment['id']}"):
                            update_comment_status(comment['id'], "resolved")
                            st.rerun()
                    if comment.get("status") != "flagged":
                        if st.button("⚠️ Flag", key=f"flag_{comment['id']}"):
                            update_comment_status(comment['id'], "flagged")
                            st.rerun()
                    if st.button("🗑️ Delete", key=f"delete_{comment['id']}"):
                        delete_comment(comment['id'])
                        st.rerun()
                
                st.markdown("---")
    else:
        st.info("No comments yet. Add the first comment above.")