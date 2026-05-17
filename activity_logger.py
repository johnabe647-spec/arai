import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px  # Add this import

def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def log_activity(firm_id, user_email, action, details=None):
    """Log user activity to database"""
    supabase = get_supabase()
    
    try:
        ip_address = 'unknown'
        user_agent = 'unknown'
        
        result = supabase.table("activity_log").insert({
            "firm_id": firm_id,
            "user_email": user_email,
            "action": action,
            "details": details or {},
            "ip_address": ip_address,
            "user_agent": user_agent
        }).execute()
        
        return True
    except Exception as e:
        print(f"Error logging activity: {e}")
        return False

def get_activity_log(firm_id, limit=100, days=30):
    """Get activity log for a firm"""
    supabase = get_supabase()
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    try:
        result = supabase.table("activity_log").select("*").eq("firm_id", firm_id).gte("created_at", cutoff_date.isoformat()).order("created_at", desc=True).limit(limit).execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error getting activity log: {e}")
        return []

def get_usage_stats(firm_id, days=30):
    """Get usage statistics for a firm"""
    logs = get_activity_log(firm_id, limit=1000, days=days)
    
    if not logs:
        return {
            "total_actions": 0,
            "unique_users": [],
            "actions_by_type": {},
            "daily_activity": [],
            "most_active_user": None,
            "peak_hours": {}
        }
    
    df = pd.DataFrame(logs)
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['date'] = df['created_at'].dt.date
    df['hour'] = df['created_at'].dt.hour
    
    stats = {
        "total_actions": len(df),
        "unique_users": df['user_email'].unique().tolist(),
        "actions_by_type": df['action'].value_counts().to_dict(),
        "daily_activity": df.groupby('date').size().to_dict(),
        "most_active_user": df['user_email'].value_counts().index[0] if len(df) > 0 else None,
        "peak_hours": df['hour'].value_counts().sort_index().to_dict()
    }
    
    return stats

def display_activity_dashboard(firm_id):
    """Display activity log dashboard in Streamlit"""
    
    st.markdown("### 📊 User Activity Dashboard")
    
    col1, col2 = st.columns(2)
    with col1:
        days = st.selectbox("Time Range", [7, 30, 90, 365], index=1)
    with col2:
        limit = st.number_input("Max Records", min_value=50, max_value=500, value=100)
    
    logs = get_activity_log(firm_id, limit=limit, days=days)
    stats = get_usage_stats(firm_id, days=days)
    
    if not logs:
        st.info("No activity logged yet. Run some actions to see activity here.")
        return
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Actions", stats['total_actions'])
    col2.metric("Unique Users", len(stats['unique_users']))
    col3.metric("Most Active", stats['most_active_user'].split('@')[0] if stats['most_active_user'] else 'N/A')
    col4.metric("Time Range", f"{days} days")
    
    st.markdown("---")
    
    # Actions by type chart
    st.subheader("📈 Actions by Type")
    
    if stats['actions_by_type']:
        actions_df = pd.DataFrame(list(stats['actions_by_type'].items()), columns=['Action', 'Count'])
        fig = px.bar(actions_df, x='Action', y='Count', title='User Actions Distribution',
                     color_discrete_sequence=['#1f77b4'])
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Daily activity chart
    st.subheader("📅 Daily Activity")
    
    if stats['daily_activity']:
        daily_df = pd.DataFrame(list(stats['daily_activity'].items()), columns=['Date', 'Count'])
        daily_df['Date'] = pd.to_datetime(daily_df['Date'])
        daily_df = daily_df.sort_values('Date')
        
        fig = px.line(daily_df, x='Date', y='Count', title='Activity Over Time',
                      markers=True)
        fig.update_traces(line_color='#28a745', marker_size=8)
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    # Peak hours
    if stats['peak_hours']:
        st.subheader("⏰ Peak Activity Hours")
        
        hours_df = pd.DataFrame(list(stats['peak_hours'].items()), columns=['Hour', 'Count'])
        hours_df = hours_df.sort_values('Hour')
        
        fig = px.bar(hours_df, x='Hour', y='Count', title='Activity by Hour',
                     color_discrete_sequence=['#ffa500'])
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Recent activity table
    st.subheader("📋 Recent Activity Log")
    
    display_logs = []
    for log in logs[:50]:
        display_logs.append({
            "Time": pd.to_datetime(log['created_at']).strftime('%Y-%m-%d %H:%M'),
            "User": log['user_email'].split('@')[0],
            "Action": log['action'],
            "Details": str(log.get('details', {}))[:50] if log.get('details') else ''
        })
    
    if display_logs:
        st.dataframe(pd.DataFrame(display_logs), use_container_width=True)
    
    # Export button
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Export Activity Log (CSV)"):
            export_df = pd.DataFrame(logs)
            csv = export_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"activity_log_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("🗑️ Clear Old Logs", help="Delete logs older than 90 days"):
            cutoff = datetime.now() - timedelta(days=90)
            supabase = get_supabase()
            supabase.table("activity_log").delete().lt("created_at", cutoff.isoformat()).execute()
            st.success("Old logs cleared!")
            st.rerun()