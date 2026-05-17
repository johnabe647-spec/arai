import streamlit as st
from supabase import create_client
from datetime import datetime, time, timedelta
import pandas as pd

def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def calculate_next_run(frequency, schedule_time, schedule_day=None):
    """Calculate the next run datetime"""
    now = datetime.now()
    today_at_time = datetime.combine(now.date(), schedule_time)
    
    if frequency == 'daily':
        if today_at_time > now:
            return today_at_time
        else:
            return today_at_time + timedelta(days=1)
    
    elif frequency == 'weekly':
        if schedule_day is None:
            return None
        days_ahead = schedule_day - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_date = now.date() + timedelta(days=days_ahead)
        return datetime.combine(next_date, schedule_time)
    
    elif frequency == 'monthly':
        if schedule_day is None:
            return None
        # Cap at 28 to avoid month boundary issues
        if schedule_day > 28:
            schedule_day = 28
        if now.day <= schedule_day:
            next_date = now.date().replace(day=schedule_day)
        else:
            if now.month == 12:
                next_date = now.date().replace(year=now.year + 1, month=1, day=schedule_day)
            else:
                next_date = now.date().replace(month=now.month + 1, day=schedule_day)
        return datetime.combine(next_date, schedule_time)
    
    return None

def create_schedule(firm_id, name, frequency, schedule_time, recipient_emails, client_name=None, schedule_day=None):
    """Create a new scheduled report"""
    supabase = get_supabase()
    
    # Calculate next run time
    next_run = calculate_next_run(frequency, schedule_time, schedule_day)
    
    try:
        result = supabase.table("scheduled_reports").insert({
            "firm_id": firm_id,
            "name": name,
            "report_type": "audit",
            "schedule_frequency": frequency,
            "schedule_time": schedule_time.isoformat(),
            "schedule_day": schedule_day,
            "recipient_emails": recipient_emails,
            "client_name": client_name,
            "is_active": True,
            "next_run": next_run.isoformat() if next_run else None
        }).execute()
        
        return True, result.data[0] if result.data else None
    except Exception as e:
        return False, str(e)

def get_schedules(firm_id):
    """Get all scheduled reports for a firm"""
    supabase = get_supabase()
    
    try:
        result = supabase.table("scheduled_reports").select("*").eq("firm_id", firm_id).order("next_run").execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error getting schedules: {e}")
        return []

def update_schedule(schedule_id, is_active):
    """Update schedule active status"""
    supabase = get_supabase()
    
    try:
        supabase.table("scheduled_reports").update({"is_active": is_active}).eq("id", schedule_id).execute()
        return True
    except Exception as e:
        print(f"Error updating schedule: {e}")
        return False

def delete_schedule(schedule_id):
    """Delete a scheduled report"""
    supabase = get_supabase()
    
    try:
        supabase.table("scheduled_reports").delete().eq("id", schedule_id).execute()
        return True
    except Exception as e:
        print(f"Error deleting schedule: {e}")
        return False

def display_schedules(schedules):
    """Display schedules in a formatted way"""
    if not schedules:
        st.info("No scheduled reports yet. Create your first schedule below.")
        return
    
    for schedule in schedules:
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.markdown(f"**{schedule['name']}**")
                freq = schedule['schedule_frequency'].capitalize()
                if schedule['schedule_frequency'] == 'weekly':
                    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    day_name = days[schedule.get('schedule_day', 0)]
                    st.caption(f"{freq} on {day_name} at {schedule['schedule_time'][:5]}")
                elif schedule['schedule_frequency'] == 'monthly':
                    st.caption(f"{freq} on day {schedule.get('schedule_day', 1)} at {schedule['schedule_time'][:5]}")
                else:
                    st.caption(f"{freq} at {schedule['schedule_time'][:5]}")
                
                if schedule.get('recipient_emails'):
                    st.caption(f"📧 {', '.join(schedule['recipient_emails'][:2])}")
                    if len(schedule['recipient_emails']) > 2:
                        st.caption(f"   +{len(schedule['recipient_emails']) - 2} more")
            
            with col2:
                if schedule.get('next_run'):
                    next_date = datetime.fromisoformat(schedule['next_run'].replace('Z', '+00:00'))
                    st.metric("Next Run", next_date.strftime('%b %d, %H:%M'))
                
                status = "🟢 Active" if schedule.get('is_active') else "🔴 Paused"
                st.caption(status)
            
            with col3:
                if schedule.get('is_active'):
                    if st.button(f"Pause", key=f"pause_{schedule['id']}"):
                        update_schedule(schedule['id'], False)
                        st.rerun()
                else:
                    if st.button(f"Resume", key=f"resume_{schedule['id']}"):
                        update_schedule(schedule['id'], True)
                        st.rerun()
                
                if st.button(f"Delete", key=f"delete_{schedule['id']}"):
                    delete_schedule(schedule['id'])
                    st.rerun()
            
            st.markdown("---")

# ============================================
# BACKGROUND SCHEDULER FUNCTION (FOR LATER DEPLOYMENT)
# ============================================

def process_scheduled_reports():
    """
    Process all due scheduled reports.
    
    THIS FUNCTION IS FOR BACKGROUND EXECUTION.
    It should be called via:
    - Cron job (every 5-15 minutes)
    - Cloud function (scheduler trigger)
    - Background worker (Celery, Redis Queue)
    
    DO NOT call this directly from the Streamlit app.
    """
    supabase = get_supabase()
    
    now = datetime.now()
    
    # Get all due schedules that are active
    try:
        result = supabase.table("scheduled_reports").select("*").eq("is_active", True).lte("next_run", now.isoformat()).execute()
        schedules = result.data if result.data else []
        
        for schedule in schedules:
            try:
                # Get the latest audit for this firm
                audit_result = supabase.table("audits").select("*").eq("firm_id", schedule['firm_id']).order("created_at", desc=True).limit(1).execute()
                
                if audit_result.data:
                    latest_audit = audit_result.data[0]
                    
                    # Get firm details for branding
                    firm_result = supabase.table("firms").select("*").eq("id", schedule['firm_id']).execute()
                    firm = firm_result.data[0] if firm_result.data else None
                    
                    # Get audit details
                    audit_data = {
                        "match_rate": latest_audit.get('match_rate', 0),
                        "matched": latest_audit.get('audit_data', {}).get('matched', 0),
                        "unmatched_bank": latest_audit.get('audit_data', {}).get('unmatched_bank', 0),
                        "unmatched_ledger": latest_audit.get('audit_data', {}).get('unmatched_ledger', 0),
                        "anomalies": latest_audit.get('audit_data', {}).get('anomalies', 0),
                        "fraud_risk": latest_audit.get('fraud_risk', 0),
                        "problem_areas": latest_audit.get('audit_data', {}).get('problem_areas', {})
                    }
                    
                    # Generate PDF report
                    from report_generator import generate_audit_pdf
                    import tempfile
                    import os
                    
                    client_name = schedule.get('client_name') or firm.get('name', 'Client')
                    firm_name = firm.get('name', 'Your Firm') if firm else 'Audit Firm'
                    
                    pdf_path = tempfile.mktemp(suffix='.pdf')
                    
                    # Get branding if available
                    branding = {
                        "primary_color": firm.get('primary_color', '#1f77b4') if firm else '#1f77b4',
                        "secondary_color": firm.get('secondary_color', '#4ecdc4') if firm else '#4ecdc4',
                        "logo_url": firm.get('logo_url') if firm else None,
                        "footer_text": firm.get('footer_text') if firm else None,
                        "custom_branding": firm.get('custom_branding', False) if firm else False
                    }
                    
                    generate_audit_pdf(
                        firm_name=firm_name,
                        client_name=client_name,
                        audit_data=audit_data,
                        output_path=pdf_path,
                        branding=branding
                    )
                    
                    # Send email to all recipients
                    from email_sender import send_report_email
                    
                    for recipient in schedule['recipient_emails']:
                        send_report_email(
                            recipient_email=recipient,
                            recipient_name=client_name,
                            firm_name=firm_name,
                            pdf_path=pdf_path,
                            audit_summary=audit_data
                        )
                    
                    # Clean up temp file
                    os.unlink(pdf_path)
                    
                    # Record that email was sent (optional: log to a new table)
                    print(f"Sent scheduled report {schedule['id']} to {len(schedule['recipient_emails'])} recipients")
                
                # Update last_sent and next_run
                next_run = calculate_next_run(
                    schedule['schedule_frequency'],
                    datetime.strptime(schedule['schedule_time'][:8], '%H:%M:%S').time(),
                    schedule.get('schedule_day')
                )
                
                supabase.table("scheduled_reports").update({
                    "last_sent": now.isoformat(),
                    "next_run": next_run.isoformat() if next_run else None
                }).eq("id", schedule['id']).execute()
                
            except Exception as e:
                print(f"Error processing schedule {schedule['id']}: {e}")
                # Log error but continue with other schedules
        
        return len(schedules)
        
    except Exception as e:
        print(f"Error in process_scheduled_reports: {e}")
        return 0


# ============================================
# DEPLOYMENT INSTRUCTIONS
# ============================================

"""
HOW TO DEPLOY THE BACKGROUND SCHEDULER:

Option 1: Cron Job (Linux/Mac Server)
--------------------------------------
Add this to crontab (runs every 10 minutes):
*/10 * * * * cd /path/to/arai && /path/to/venv/bin/python -c "from scheduler import process_scheduled_reports; process_scheduled_reports()"

Option 2: Streamlit Cloud (Manual)
-----------------------------------
Streamlit Cloud doesn't support background tasks natively.
Use an external service like:
- Koyeb (free cron jobs)
- Render (cron jobs)
- EasyCron (free tier available)

Option 3: GitHub Actions
------------------------
Create .github/workflows/scheduler.yml:
---
name: Scheduled Reports
on:
  schedule:
    - cron: '*/15 * * * *'
jobs:
  run-scheduler:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run scheduler
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
        run: |
          pip install -r requirements.txt
          python -c "from scheduler import process_scheduled_reports; process_scheduled_reports()"

Option 4: Koyeb (Free)
----------------------
1. Sign up at koyeb.com
2. Create a worker with cron trigger
3. Set command: python -c "from scheduler import process_scheduled_reports; process_scheduled_reports()"

IMPORTANT NOTES:
----------------
- The background function requires the same environment variables as your main app
- Make sure report_generator.py and email_sender.py are accessible
- Test locally first: python -c "from scheduler import process_scheduled_reports; process_scheduled_reports()"
- For production, run every 10-15 minutes
- Monitor logs for errors
"""