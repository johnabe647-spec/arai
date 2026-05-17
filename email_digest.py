import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
import pandas as pd
from email_sender import send_report_email
from report_generator import generate_audit_pdf
import tempfile
import os

def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def generate_weekly_digest(firm_id, firm_email, firm_name, audits):
    """Generate a weekly digest email content"""
    
    if not audits:
        return None
    
    # Calculate metrics
    total_audits = len(audits)
    avg_match_rate = sum(a.get('match_rate', 0) for a in audits) / total_audits
    avg_fraud_risk = sum(a.get('fraud_risk', 0) for a in audits) / total_audits
    total_time_saved = total_audits * 15  # 15 hours saved per audit
    
    # Count anomalies
    total_anomalies = sum(a.get('audit_data', {}).get('anomalies', 0) for a in audits)
    
    # Get top 3 highest risk audits
    high_risk_audits = sorted(audits, key=lambda x: x.get('fraud_risk', 0), reverse=True)[:3]
    
    # Generate HTML email
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background-color: #1f77b4; color: white; padding: 20px; text-align: center; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .metric {{ background-color: #f0f2f6; padding: 15px; border-radius: 5px; margin: 10px 0; }}
            .metric-value {{ font-size: 24px; font-weight: bold; color: #1f77b4; }}
            .risk-high {{ color: #dc3545; }}
            .risk-medium {{ color: #ffc107; }}
            .risk-low {{ color: #28a745; }}
            .footer {{ text-align: center; font-size: 12px; color: #999; margin-top: 30px; }}
            .button {{ background-color: #1f77b4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔍 ARAI Weekly Digest</h1>
            <p>Your audit activity for the week ending {datetime.now().strftime('%B %d, %Y')}</p>
        </div>
        <div class="container">
            <h2>Hello {firm_name},</h2>
            <p>Here's your weekly audit summary from ARAI.</p>
            
            <div class="metric">
                <strong>📊 Total Audits:</strong>
                <div class="metric-value">{total_audits}</div>
            </div>
            
            <div class="metric">
                <strong>📈 Average Match Rate:</strong>
                <div class="metric-value">{avg_match_rate:.1%}</div>
            </div>
            
            <div class="metric">
                <strong>⚠️ Average Fraud Risk:</strong>
                <div class="metric-value">{avg_fraud_risk:.0f}%</div>
            </div>
            
            <div class="metric">
                <strong>⏱️ Time Saved:</strong>
                <div class="metric-value">{total_time_saved} hours</div>
                <small>Estimated value: ${total_time_saved * 50:,}</small>
            </div>
            
            <div class="metric">
                <strong>🚨 Anomalies Detected:</strong>
                <div class="metric-value">{total_anomalies}</div>
            </div>
    """
    
    if high_risk_audits:
        html_content += """
            <h3>🔴 High Priority Items</h3>
            <ul>
        """
        for audit in high_risk_audits:
            fraud_risk = audit.get('fraud_risk', 0)
            risk_class = "risk-high" if fraud_risk >= 70 else "risk-medium" if fraud_risk >= 40 else "risk-low"
            html_content += f"""
                <li class="{risk_class}">
                    <strong>{audit.get('filename', 'Audit')}</strong><br>
                    Fraud Risk: {fraud_risk:.0f}% | Match Rate: {audit.get('match_rate', 0):.1%}
                </li>
            """
        html_content += "</ul>"
    
    html_content += f"""
            <div style="text-align: center; margin: 30px 0;">
                <a href="https://arai.africa.online.streamlit.app" class="button">View Full Dashboard</a>
            </div>
            
            <hr>
            <p><small>You're receiving this because you're an ARAI user. 
            <a href="#" style="color: #999;">Unsubscribe</a> | 
            <a href="https://arai.africa.online.streamlit.app/settings" style="color: #999;">Manage preferences</a></small></p>
        </div>
        <div class="footer">
            <p>© 2025 ARAI | Audit Risk & AI Intelligence | Finance Done Smarter</p>
        </div>
    </body>
    </html>
    """
    
    return html_content

def send_weekly_digests():
    """Send weekly digests to all firms (to be called by cron job)"""
    supabase = get_supabase()
    
    # Get all firms with email digest enabled
    # For now, send to all firms with activity in the last week
    one_week_ago = datetime.now() - timedelta(days=7)
    
    result = supabase.table("firms").select("*").execute()
    firms = result.data if result.data else []
    
    sent_count = 0
    for firm in firms:
        try:
            # Get audits from last week
            audits_result = supabase.table("audits").select("*").eq("firm_id", firm['id']).gte("created_at", one_week_ago.isoformat()).execute()
            audits = audits_result.data if audits_result.data else []
            
            if audits:
                digest_html = generate_weekly_digest(firm['id'], firm['email'], firm['name'], audits)
                
                if digest_html:
                    # Send email (simplified for now)
                    print(f"Sending weekly digest to {firm['email']}")
                    sent_count += 1
        except Exception as e:
            print(f"Error sending digest to firm {firm.get('id')}: {e}")
    
    return sent_count

def display_digest_settings(firm_id):
    """Display digest settings in Settings page"""
    st.markdown("#### 📧 Weekly Digest Settings")
    st.caption("Get a weekly email summary of your audit activity")
    
    # Check if digest is enabled (store in firms table)
    supabase = get_supabase()
    result = supabase.table("firms").select("digest_enabled").eq("id", firm_id).execute()
    digest_enabled = result.data[0].get('digest_enabled', True) if result.data else True
    
    col1, col2 = st.columns(2)
    with col1:
        digest_enabled = st.toggle("Enable Weekly Digest", value=digest_enabled, key="digest_toggle")
    
    with col2:
        digest_day = st.selectbox("Day to Send", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], index=0, key="digest_day")
    
    if st.button("Save Digest Settings", key="save_digest"):
        supabase.table("firms").update({"digest_enabled": digest_enabled, "digest_day": digest_day}).eq("id", firm_id).execute()
        st.success("Digest settings saved!")
        st.rerun()
    
    if digest_enabled:
        st.info(f"📧 Weekly digests will be sent every {digest_day} morning.")
    else:
        st.info("Weekly digests are currently disabled.")