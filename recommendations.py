import streamlit as st
import pandas as pd
from datetime import datetime

def generate_recommendations(audit_data, anomalies, fraud_risk, problem_areas, match_rate):
    """
    Generate AI-powered recommendations based on audit results
    """
    recommendations = []
    
    # Match rate recommendations
    if match_rate < 0.7:
        recommendations.append({
            "category": "📊 Reconciliation",
            "priority": "High",
            "recommendation": "Match rate is below 70%. Review chart of accounts mapping and verify transaction coding.",
            "expected_impact": "+15-20% match rate improvement",
            "effort": "Medium"
        })
    elif match_rate < 0.85:
        recommendations.append({
            "category": "📊 Reconciliation",
            "priority": "Medium",
            "recommendation": "Improve match rate by standardizing transaction descriptions and implementing consistent coding.",
            "expected_impact": "+5-10% match rate improvement",
            "effort": "Low"
        })
    else:
        recommendations.append({
            "category": "📊 Reconciliation",
            "priority": "Low",
            "recommendation": "Match rate is excellent. Maintain current reconciliation procedures.",
            "expected_impact": "Sustain current performance",
            "effort": "Low"
        })
    
    # Fraud risk recommendations
    if fraud_risk >= 70:
        recommendations.append({
            "category": "🚨 Fraud Prevention",
            "priority": "Critical",
            "recommendation": "High fraud risk detected. Implement enhanced review procedures, increase sample sizes by 50%, and involve senior auditor.",
            "expected_impact": "Reduce fraud risk by 40-60%",
            "effort": "High"
        })
    elif fraud_risk >= 40:
        recommendations.append({
            "category": "🚨 Fraud Prevention",
            "priority": "High",
            "recommendation": "Medium fraud risk. Review all high-risk transactions ($10,000+) and add secondary approval for payments.",
            "expected_impact": "Reduce fraud risk by 20-30%",
            "effort": "Medium"
        })
    else:
        recommendations.append({
            "category": "🚨 Fraud Prevention",
            "priority": "Low",
            "recommendation": "Low fraud risk. Maintain current controls and continue regular monitoring.",
            "expected_impact": "Maintain low risk level",
            "effort": "Low"
        })
    
    # Anomaly recommendations
    if len(anomalies) > 5:
        recommendations.append({
            "category": "⚠️ Anomaly Detection",
            "priority": "High",
            "recommendation": f"Found {len(anomalies)} anomalies. Investigate round-dollar transactions and duplicate payments immediately.",
            "expected_impact": "Prevent potential losses of $5,000-50,000",
            "effort": "High"
        })
    elif len(anomalies) > 0:
        recommendations.append({
            "category": "⚠️ Anomaly Detection",
            "priority": "Medium",
            "recommendation": f"Review {len(anomalies)} flagged transactions. Focus on high-risk (red) items first.",
            "expected_impact": "Identify and correct errors early",
            "effort": "Medium"
        })
    
    # Problem area recommendations
    high_risk_areas = [(area, risk) for area, risk in problem_areas.items() if risk > 70]
    for area, risk in high_risk_areas[:2]:
        recommendations.append({
            "category": f"🎯 {area}",
            "priority": "High",
            "recommendation": f"High risk ({risk:.0f}%) detected in {area}. Perform detailed testing and document all procedures.",
            "expected_impact": "Reduce risk to below 30%",
            "effort": "High"
        })
    
    # Time efficiency recommendations
    if len(anomalies) > 10:
        recommendations.append({
            "category": "⏱️ Efficiency",
            "priority": "Medium",
            "recommendation": "High anomaly count suggests data quality issues. Consider automating data entry validation.",
            "expected_impact": "Save 5-10 hours per audit",
            "effort": "Medium"
        })
    
    # Compliance recommendations
    if fraud_risk > 50:
        recommendations.append({
            "category": "📋 Compliance",
            "priority": "High",
            "recommendation": "Document all findings in detail. Consider consulting with legal counsel for high-risk matters.",
            "expected_impact": "Strengthen audit defense",
            "effort": "Low"
        })
    
    return recommendations

def display_recommendations(recommendations):
    """
    Display recommendations in a formatted way
    """
    if not recommendations:
        st.info("No specific recommendations at this time.")
        return
    
    # Group by priority
    critical = [r for r in recommendations if r['priority'] == 'Critical']
    high = [r for r in recommendations if r['priority'] == 'High']
    medium = [r for r in recommendations if r['priority'] == 'Medium']
    low = [r for r in recommendations if r['priority'] == 'Low']
    
    # Display critical first
    if critical:
        st.markdown("### 🔴 Critical Issues")
        for rec in critical:
            with st.container():
                st.error(f"**{rec['category']}**")
                st.write(f"📝 {rec['recommendation']}")
                st.caption(f"🎯 Expected impact: {rec['expected_impact']} | ⏱️ Effort: {rec['effort']}")
                st.markdown("---")
    
    # Display high priority
    if high:
        st.markdown("### 🟠 High Priority")
        for rec in high:
            with st.container():
                st.warning(f"**{rec['category']}**")
                st.write(f"📝 {rec['recommendation']}")
                st.caption(f"🎯 Expected impact: {rec['expected_impact']} | ⏱️ Effort: {rec['effort']}")
                st.markdown("---")
    
    # Display medium priority
    if medium:
        st.markdown("### 🟡 Medium Priority")
        for rec in medium:
            with st.container():
                st.info(f"**{rec['category']}**")
                st.write(f"📝 {rec['recommendation']}")
                st.caption(f"🎯 Expected impact: {rec['expected_impact']} | ⏱️ Effort: {rec['effort']}")
                st.markdown("---")
    
    # Display low priority
    if low:
        st.markdown("### 🟢 Low Priority")
        for rec in low:
            with st.container():
                st.write(f"**{rec['category']}**")
                st.write(f"📝 {rec['recommendation']}")
                st.caption(f"🎯 Expected impact: {rec['expected_impact']} | ⏱️ Effort: {rec['effort']}")
                st.markdown("---")