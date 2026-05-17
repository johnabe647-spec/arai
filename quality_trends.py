import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

def calculate_quality_score(match_rate, fraud_risk, anomaly_count):
    """Calculate quality score for a single audit"""
    # Match rate contributes 50%, fraud risk 30%, anomalies 20%
    match_score = match_rate * 50
    fraud_score = max(0, 30 - (fraud_risk / 100) * 30)
    anomaly_score = max(0, 20 - (anomaly_count / 10) * 20)
    return min(100, match_score + fraud_score + anomaly_score)

def process_quality_trends(audits):
    """Process audits to generate quality trends"""
    if not audits:
        return pd.DataFrame(), {}
    
    df = pd.DataFrame(audits)
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['quality_score'] = df.apply(
        lambda x: calculate_quality_score(
            x.get('match_rate', 0),
            x.get('fraud_risk', 0),
            x.get('audit_data', {}).get('anomalies', 0) if isinstance(x.get('audit_data'), dict) else 0
        ),
        axis=1
    )
    df['month'] = df['created_at'].dt.strftime('%Y-%m')
    df['week'] = df['created_at'].dt.isocalendar().week
    
    # Calculate trends
    overall_quality = df['quality_score'].mean()
    recent_audits = df.head(5)
    recent_quality = recent_audits['quality_score'].mean() if len(recent_audits) > 0 else 0
    
    # Determine trend direction
    if len(df) >= 3:
        first_three = df.tail(3)['quality_score'].mean()
        last_three = df.head(3)['quality_score'].mean()
        trend = "improving" if last_three > first_three else "declining" if last_three < first_three else "stable"
        trend_percent = abs((last_three - first_three) / first_three * 100) if first_three > 0 else 0
    else:
        trend = "insufficient_data"
        trend_percent = 0
    
    # Monthly aggregation
    monthly = df.groupby('month').agg({
        'quality_score': 'mean',
        'match_rate': 'mean',
        'fraud_risk': 'mean'
    }).reset_index()
    
    return df, {
        "overall_quality": overall_quality,
        "recent_quality": recent_quality,
        "trend": trend,
        "trend_percent": trend_percent,
        "total_audits": len(df),
        "monthly_data": monthly.to_dict('records') if not monthly.empty else []
    }

def get_quality_alerts(quality_stats):
    """Generate alerts based on quality metrics"""
    alerts = []
    
    if quality_stats["overall_quality"] < 60:
        alerts.append({
            "type": "critical",
            "message": f"Overall quality score is {quality_stats['overall_quality']:.0f}/100. Immediate improvement needed.",
            "action": "Review audit procedures and increase staff training"
        })
    elif quality_stats["overall_quality"] < 75:
        alerts.append({
            "type": "warning",
            "message": f"Overall quality score is {quality_stats['overall_quality']:.0f}/100. Below target of 80.",
            "action": "Focus on improving match rates and reducing anomalies"
        })
    
    if quality_stats["trend"] == "declining" and quality_stats["trend_percent"] > 10:
        alerts.append({
            "type": "warning",
            "message": f"Quality is declining by {quality_stats['trend_percent']:.0f}% over recent audits.",
            "action": "Review recent audit files for common issues"
        })
    
    if quality_stats["total_audits"] < 5:
        alerts.append({
            "type": "info",
            "message": f"Only {quality_stats['total_audits']} audits analyzed. Run more audits for better insights.",
            "action": "Continue running audits to establish quality baseline"
        })
    
    return alerts

def get_improvement_recommendations(audits, quality_stats):
    """Generate improvement recommendations based on quality data"""
    recommendations = []
    
    if not audits:
        return recommendations
    
    # Find worst performing audits
    df = pd.DataFrame(audits)
    df['quality_score'] = df.apply(
        lambda x: calculate_quality_score(
            x.get('match_rate', 0),
            x.get('fraud_risk', 0),
            x.get('audit_data', {}).get('anomalies', 0) if isinstance(x.get('audit_data'), dict) else 0
        ),
        axis=1
    )
    df = df.sort_values('quality_score')
    
    if len(df) > 0:
        worst_audit = df.iloc[0]
        recommendations.append({
            "area": "Lowest Quality Audit",
            "current": f"Score: {worst_audit['quality_score']:.0f}/100",
            "recommendation": f"Review audit '{worst_audit['filename']}' for quality issues. Match rate: {worst_audit.get('match_rate', 0):.1%}"
        })
    
    # Check match rate issues
    low_match = [a for a in audits if a.get('match_rate', 0) < 0.7]
    if len(low_match) > 2:
        recommendations.append({
            "area": "Match Rate",
            "current": f"{len(low_match)} audits with <70% match rate",
            "recommendation": "Standardize transaction descriptions and implement automated mapping rules"
        })
    
    # Check fraud risk issues
    high_risk = [a for a in audits if a.get('fraud_risk', 0) > 50]
    if len(high_risk) > 2:
        recommendations.append({
            "area": "Fraud Risk",
            "current": f"{len(high_risk)} audits with >50% fraud risk",
            "recommendation": "Enhance control testing and increase sample sizes for high-risk transactions"
        })
    
    if quality_stats["overall_quality"] < 70:
        recommendations.append({
            "area": "Overall Quality",
            "current": f"{quality_stats['overall_quality']:.0f}/100",
            "recommendation": "Implement pre-audit checklist and post-audit quality review process"
        })
    
    return recommendations

def display_quality_trends_dashboard(audits, firm_name):
    """Display quality trends dashboard"""
    
    st.markdown("### 📈 Audit Quality Trends")
    st.markdown("Track your audit quality over time and identify improvement opportunities.")
    
    if not audits or len(audits) < 1:
        st.info("Run at least 1 audit to see quality trends.")
        return
    
    df, stats = process_quality_trends(audits)
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Overall Quality", f"{stats['overall_quality']:.0f}/100")
    col2.metric("Recent Quality", f"{stats['recent_quality']:.0f}/100")
    
    trend_icon = "📈" if stats['trend'] == "improving" else "📉" if stats['trend'] == "declining" else "➡️"
    trend_text = "Improving" if stats['trend'] == "improving" else "Declining" if stats['trend'] == "declining" else "Stable"
    col3.metric("Trend", f"{trend_icon} {trend_text}")
    
    col4.metric("Total Audits", stats['total_audits'])
    
    st.markdown("---")
    
    # Quality Score Trend Chart
    st.subheader("📊 Quality Score Trend")
    
    if len(df) >= 2:
        fig = px.line(df, x='created_at', y='quality_score', 
                      title='Quality Score Over Time',
                      labels={'quality_score': 'Quality Score', 'created_at': 'Audit Date'},
                      markers=True)
        fig.update_traces(line_color='#1f77b4', marker_size=8)
        fig.update_layout(height=350)
        
        # Add target line
        fig.add_hline(y=80, line_dash="dash", line_color="green", annotation_text="Target (80)")
        fig.add_hline(y=60, line_dash="dash", line_color="red", annotation_text="Warning (60)")
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Run more audits to see quality trends.")
    
    st.markdown("---")
    
    # Monthly Trends
    if stats['monthly_data'] and len(stats['monthly_data']) >= 2:
        st.subheader("📅 Monthly Trends")
        
        monthly_df = pd.DataFrame(stats['monthly_data'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(monthly_df, x='month', y='quality_score', 
                         title='Monthly Quality Score',
                         labels={'quality_score': 'Quality Score', 'month': 'Month'},
                         color_discrete_sequence=['#28a745'])
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.line(monthly_df, x='month', y='match_rate', 
                          title='Monthly Match Rate',
                          labels={'match_rate': 'Match Rate', 'month': 'Month'},
                          markers=True)
            fig.update_traces(line_color='#1f77b4')
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Quality Alerts
    alerts = get_quality_alerts(stats)
    if alerts:
        st.subheader("⚠️ Quality Alerts")
        for alert in alerts:
            if alert['type'] == 'critical':
                st.error(f"🔴 {alert['message']}")
                st.info(f"💡 {alert['action']}")
            elif alert['type'] == 'warning':
                st.warning(f"🟡 {alert['message']}")
                st.info(f"💡 {alert['action']}")
            else:
                st.info(f"ℹ️ {alert['message']}")
        st.markdown("---")
    
    # Improvement Recommendations
    recommendations = get_improvement_recommendations(audits, stats)
    if recommendations:
        st.subheader("💡 Improvement Recommendations")
        for rec in recommendations:
            with st.container():
                st.markdown(f"**{rec['area']}**")
                st.write(f"📊 {rec['current']}")
                st.write(f"✅ {rec['recommendation']}")
                st.markdown("---")
    
    # Export option
    if st.button("📥 Export Quality Report"):
        # Create report
        report_data = []
        for audit in audits[:50]:
            quality_score = calculate_quality_score(
                audit.get('match_rate', 0),
                audit.get('fraud_risk', 0),
                audit.get('audit_data', {}).get('anomalies', 0) if isinstance(audit.get('audit_data'), dict) else 0
            )
            report_data.append({
                "Date": audit.get('created_at', ''),
                "Filename": audit.get('filename', ''),
                "Match Rate": audit.get('match_rate', 0),
                "Fraud Risk": audit.get('fraud_risk', 0),
                "Quality Score": quality_score
            })
        
        report_df = pd.DataFrame(report_data)
        csv = report_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"quality_report_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )