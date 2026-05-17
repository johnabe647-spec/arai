import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
import pandas as pd
import time as time_module

def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def get_or_create_audit_progress(audit_id, firm_id, estimated_hours=None):
    """Get existing audit progress or create new one"""
    supabase = get_supabase()
    
    # Check if exists
    result = supabase.table("audit_progress").select("*").eq("audit_id", audit_id).execute()
    
    if result.data:
        return result.data[0]
    
    # Create new progress record
    estimated_minutes = int(estimated_hours * 60) if estimated_hours else None
    
    new_progress = supabase.table("audit_progress").insert({
        "audit_id": audit_id,
        "firm_id": firm_id,
        "status": "in_progress",
        "progress_percentage": 0,
        "tasks_completed": 0,
        "tasks_total": 5,
        "estimated_time_minutes": estimated_minutes,
        "started_at": datetime.now().isoformat()
    }).execute()
    
    progress_id = new_progress.data[0]["id"]
    
    # Create default tasks
    default_tasks = [
        {"name": "Upload Documents", "description": "Upload bank statement and ledger", "order": 1},
        {"name": "Run Reconciliation", "description": "Execute AI reconciliation", "order": 2},
        {"name": "Review Anomalies", "description": "Check flagged transactions", "order": 3},
        {"name": "Generate Report", "description": "Create audit report", "order": 4},
        {"name": "Send to Client", "description": "Email report to client", "order": 5}
    ]
    
    for task in default_tasks:
        supabase.table("audit_tasks").insert({
            "audit_progress_id": progress_id,
            "task_name": task["name"],
            "task_description": task["description"],
            "task_order": task["order"],
            "is_completed": False
        }).execute()
    
    return new_progress.data[0]

def update_task_status(task_id, is_completed):
    """Update task completion status"""
    supabase = get_supabase()
    
    update_data = {
        "is_completed": is_completed,
        "completed_at": datetime.now().isoformat() if is_completed else None
    }
    
    supabase.table("audit_tasks").update(update_data).eq("id", task_id).execute()
    
    # Update progress percentage
    tasks = supabase.table("audit_tasks").select("*").eq("audit_progress_id", task_id).execute()
    if tasks.data:
        total = len(tasks.data)
        completed = sum(1 for t in tasks.data if t.get("is_completed"))
        percentage = int((completed / total) * 100) if total > 0 else 0
        
        supabase.table("audit_progress").update({
            "progress_percentage": percentage,
            "tasks_completed": completed,
            "last_updated": datetime.now().isoformat()
        }).eq("id", task_id).execute()

def update_time_spent(progress_id, minutes_added):
    """Update time spent on audit"""
    supabase = get_supabase()
    
    result = supabase.table("audit_progress").select("time_spent_minutes").eq("id", progress_id).execute()
    current_time = result.data[0].get("time_spent_minutes", 0) if result.data else 0
    
    supabase.table("audit_progress").update({
        "time_spent_minutes": current_time + minutes_added,
        "last_updated": datetime.now().isoformat()
    }).eq("id", progress_id).execute()

def complete_audit(progress_id):
    """Mark audit as complete"""
    supabase = get_supabase()
    
    supabase.table("audit_progress").update({
        "status": "completed",
        "progress_percentage": 100,
        "tasks_completed": 5,
        "completed_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat()
    }).eq("id", progress_id).execute()

def get_audit_progress_display(audit_id, firm_id, estimated_hours=None):
    """Get formatted progress display"""
    progress = get_or_create_audit_progress(audit_id, firm_id, estimated_hours)
    
    supabase = get_supabase()
    tasks = supabase.table("audit_tasks").select("*").eq("audit_progress_id", progress["id"]).order("task_order").execute()
    
    return {
        "progress": progress,
        "tasks": tasks.data if tasks.data else []
    }

def display_audit_tracker(audit_id, firm_id, audit_name, estimated_hours=None):
    """Display audit tracker in the UI"""
    
    data = get_audit_progress_display(audit_id, firm_id, estimated_hours)
    progress = data["progress"]
    tasks = data["tasks"]
    
    st.markdown("### 📋 Audit Progress Tracker")
    
    # Progress bar
    st.progress(progress["progress_percentage"] / 100)
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Progress", f"{progress['progress_percentage']}%")
    col2.metric("Tasks Completed", f"{progress['tasks_completed']}/{progress['tasks_total']}")
    col3.metric("Status", progress["status"].replace("_", " ").title())
    
    if progress.get("estimated_time_minutes"):
        est_hours = progress["estimated_time_minutes"] / 60
        col4.metric("Estimated Time", f"{est_hours:.1f} hours")
    
    st.markdown("---")
    
    # Task checklist
    st.markdown("#### ✅ Task Checklist")
    
    for task in tasks:
        col1, col2, col3 = st.columns([0.5, 4, 1])
        
        with col1:
            if task["is_completed"]:
                st.markdown("✅")
            else:
                st.markdown("⬜")
        
        with col2:
            st.markdown(f"**{task['task_name']}**")
            st.caption(task.get("task_description", ""))
        
        with col3:
            if not task["is_completed"]:
                if st.button("Complete", key=f"complete_task_{task['id']}"):
                    update_task_status(task["id"], True)
                    st.rerun()
    
    st.markdown("---")
    
    # Time tracking
    st.markdown("#### ⏱️ Time Tracking")
    
    col1, col2 = st.columns(2)
    with col1:
        minutes_to_add = st.number_input("Add minutes spent", min_value=0, max_value=480, value=0, step=15)
        if st.button("Add Time", key="add_time"):
            update_time_spent(progress["id"], minutes_to_add)
            st.rerun()
    
    with col2:
        if progress.get("time_spent_minutes"):
            hours_spent = progress["time_spent_minutes"] / 60
            st.metric("Total Time Spent", f"{hours_spent:.1f} hours")
    
    # Complete audit button
    if progress["progress_percentage"] == 100 and progress["status"] != "completed":
        if st.button("🎉 Complete Audit", type="primary"):
            complete_audit(progress["id"])
            st.success("Audit marked as complete!")
            st.balloons()
            st.rerun()